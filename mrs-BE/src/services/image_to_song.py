from .recommend_playlist_songs import SimilaritySearch as SimilaritySearchFAISS # 기존의 FAISS 버전
from .recommend_playlist_songs_es import SimilaritySearch as SimilaritySearchES # Elastic 버전

# 전환할 때 이 한 줄만 바꾸면 됨!!!!!!!!!!
# SimilaritySearch = SimilaritySearchFAISS  # FAISS 버전
SimilaritySearch = SimilaritySearchES       # ES 버전

from .image_processing import ImageProcessor
from .recommend_song_detail import RecommendSongs
import pandas as pd
import numpy as np
import sys, os
import json 

import math

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from ..utils import image_module
from settings.path import *


def get_filtered_tags(tags_list, min_count):
    # 1. 입력 데이터를 numpy 행렬로 변환
    all_tags = np.array(tags_list)
    
    # 2. 세로 방향 합산
    sum_of_tags = np.sum(all_tags, axis=0)
    
    # 3. min_count 이상인 것만 필터링 (min_count가 0이면 모든 태그가 1이 됨)
    filtered_tags = (sum_of_tags >= min_count).astype(int).tolist()
    
    print(f"DEBUG - Min Count: {min_count}")
    print(f"DEBUG - Sum of tags: {sum_of_tags}")
    
    return filtered_tags


def get_recommend_songs(image_paths: list):
    # 이미지 프로세서 인스턴스를 생성
    image_processor = ImageProcessor(model_path=MODEL_PATH)
    
    # 외부에서 주입받은 image_paths를 그대로 사용
    print("===== 이미지 경로 =====", image_paths)  # 추가
    
    # 1. 각 이미지의 태그와 확률을 함께 추출
    # extract_tags가 (predictions, probabilities)를 반환하도록 수정되어 있어야 합니다.
    results = [image_processor.extract_tags(image_path=image_path) for image_path in image_paths]
    
    extracted_tags = [r[0] for r in results]    # 예측값(0/1) 리스트
    extracted_probs = [r[1] for r in results]   # 확률값(0~1) 리스트
    print("===== 추출된 태그 =====", extracted_tags)  # 추가

    # 2. 유의미한 태그만 필터링
    # round(0.5)는 0이 되어 모든 태그를 1로 만듭니다. 
    # math.ceil(0.5)를 사용하여 1장일 때 최소 1번은 나타난 태그만 필터링하게 합니다.
    min_count = math.ceil(len(image_paths) / 2)
    if min_count == 0: min_count = 1 # 최소값 방어 코드
    
    filtered_query_tags = get_filtered_tags(extracted_tags, min_count)
    print("===== 필터링된 태그 =====", filtered_query_tags)  # 추가

    # 3. class_idx_to_label JSON 파일을 로드 후 매핑
    with open(IDX_JSON_PATH, 'r', encoding='utf-8') as json_file:
        class_idx_to_label = json.load(json_file)

    # 인덱스 태그를 한글 레이블로 매핑합니다. (LLM 생성에 활용예정)
    filtered_query_labels = [
	    class_idx_to_label[str(idx)] 
	    for idx, value in enumerate(filtered_query_tags) if value == 1]

    # 각 태그별 확률 딕셔너리 생성 
    # 여러 장일 경우, 모든 사진 확률의 평균값 계산
    avg_probs = np.mean(extracted_probs, axis=0)

    prob_dict = {
        class_idx_to_label[str(i)]: round(float(avg_probs[i]) * 100, 2) 
        for i in range(len(class_idx_to_label))
    }

    # 4. 유사성 검색 인스턴스를 생성 및 FAISS 인덱스를 빌드
    similarity_search = SimilaritySearch(tag_table_path=TAG_TABLE_PATH)
    similarity_search.build_index()

    # 유사한 플레이리스트의 playlist_songs_id를 검색합니다.
    similar_playlists_songs_ids = similarity_search.search_similar_playlists(query_tags=filtered_query_tags)

    # 각 playlist_songs_ids에 대해 get_top_songs을 호출하고 결과를 합칩니다.
    all_top_songs = pd.DataFrame()
    song_recommender = RecommendSongs(song_table_path=SONG_TABLE_PATH)
    song_recommender.load_songs()

    for playlist_songs_ids_str in similar_playlists_songs_ids:
        top_songs = song_recommender.get_top_songs(playlist_songs_ids_str)
        all_top_songs = pd.concat([all_top_songs, top_songs])


    # 5. 결과 정리 
    all_top_songs.drop_duplicates(inplace=True)

    if not all_top_songs.empty:
        all_top_songs = all_top_songs.sort_values(by='popularity', ascending=False).head(5)
        songs_dict = {row['SONG_TITLE']: row['ARTIST_NAME'] for _, row in all_top_songs.iterrows()}
    else:
        songs_dict = {}
    
    # [수정] 4개의 값을 반환합니다: 곡 리스트, 한글 태그 리스트, 태그 벡터, 확률 딕셔너리
    return songs_dict, filtered_query_labels, filtered_query_tags, prob_dict