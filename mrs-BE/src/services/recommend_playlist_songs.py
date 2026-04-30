import faiss
import pandas as pd
import numpy as np

class SimilaritySearch:
    def __init__(self, tag_table_path):
        self.tag_table_path = tag_table_path
        self.index = None
        self.playlist_songs_ids = None  # playlist_songs_id 정보를 저장할 변수

    def build_index(self):
        # tag_table.csv 파일을 읽습니다.
        df = pd.read_csv(self.tag_table_path)
        
        # playlist_songs_id를 저장합니다.
        self.playlist_songs_ids = df['playlist_songs_id'].values
        
        # 태그 벡터만을 포함하는 DataFrame을 생성합니다.
        tag_vectors = df.drop(columns=['playlist_id', 'num_of_songs', 'playlist_songs_id']).values
        
        # 태그 벡터를 정규화합니다.
        norms = np.linalg.norm(tag_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 길이가 0인 벡터를 처리합니다.
        norm_tag_vectors = tag_vectors / norms
        
        # FAISS 인덱스를 생성하고 태그 벡터를 추가합니다.
        self.index = faiss.IndexFlatL2(norm_tag_vectors.shape[1])
        self.index.add(norm_tag_vectors.astype('float32'))

    def search_similar_playlists(self, query_tags, k=15):
        # 쿼리 태그 벡터를 정규화합니다.
        query_vec = np.array(query_tags) / np.linalg.norm(query_tags)
        
        # 가장 유사한 플레이리스트를 검색합니다.
        distances, indices = self.index.search(np.array([query_vec]).astype('float32'), k)
        
        # 가장 유사한 플레이리스트의 playlist_songs_id를 반환합니다.
        return self.playlist_songs_ids[indices.flatten()]