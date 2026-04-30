from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re

# ── 기본 설정 ────────────────────────────────── 
default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
OUTPUT_DIR = '/opt/airflow/data'  # 가능하면 환경 변수나 Airflow Variable로 관리


# ── 우리 태그 → 지니 태그 매핑 ───────────────────────
TAG_MAPPING = {
    '출/퇴근':    '출/퇴근길',
    '일/공부':    '일/공부',
    '집':         '집',
    '카페':       '카페',
    '드라이브':   '드라이브',
    '거리':       '거리',
    '클럽':       '클럽',
    '파티':       '하우스파티',
    '휴식':       '휴식',
    '해변':       '해변',
    '집중':       '집중',
    '여유':       '잠잘 때',
    '아침':       '아침',
    '밤':         '밤',
    '산책':       '산책',
    '운동':       '운동',
    '행복':       '행복',
    '화남':       '분노',
    '몽환적인':   '몽환적인',
    '밝은':       '밝은',
    '슬픔':       '슬픔',
    '우울/외로움':'우울',
    '편안한':     '편안한',
    '사랑':       '사랑',
    '봄':         '봄',
    '여름':       '여름',
    '가을':       '가을',
    '겨울':       '겨울',
    '우중충한날': '흐린날',
}


# ── Task 1: CSV 로드 ───────────────────────
def load_tag_csv(**context):
    """tag_table3.csv를 로드하여 경로를 XCom에 전달"""
    csv_path = '/opt/airflow/data/tag_table3.csv'
    df = pd.read_csv(csv_path)
    print(f"CSV 로드 완료: {len(df)}행 × {len(df.columns)}열")
    return csv_path


# ── Task 2: 멀티-핫 태그 행 추출 ───────────────────
def extract_playlist_tags(**context):
    """tag0~tag28 컬럼을 long-format으로 변환"""
    csv_path = context['ti'].xcom_pull(task_ids='load_tag_csv')
    execution_date = context['ds_nodash']
    
    df = pd.read_csv(csv_path)
    
    # 태그 컬럼만 추출
    tag_cols = [f'tag{i}' for i in range(29)]
    df_tags = df[['playlist_id'] + tag_cols + ['num_of_songs']].copy()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw_path = f'{OUTPUT_DIR}/raw_{execution_date}.csv'
    df_tags.to_csv(raw_path, index=False, encoding='utf-8-sig')
    print(f"태그 추출 완료: {len(df_tags)}개 플레이리스트")
    return raw_path


# ── Task 3: 전처리 ────────────────────────────────────
def preprocess(**context):
    raw_path = context['ti'].xcom_pull(task_ids='extract_playlist_tags')  # ← 수정
    execution_date = context['ds_nodash']

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {raw_path}")

    df = pd.read_csv(raw_path)

    # 중복 제거
    df.drop_duplicates(subset=['playlist_id'], inplace=True)
    # 결측값 제거
    df.dropna(inplace=True)
    # num_of_songs 0인 행 제거
    df = df[df['num_of_songs'] > 0]

    processed_path = f'{OUTPUT_DIR}/processed_playlists_{execution_date}.csv'
    df.to_csv(processed_path, index=False, encoding='utf-8-sig')

    print(f"전처리 완료: {len(df)}개 플레이리스트")
    print(df.head())

    return processed_path


# ── Task 4: ES 인덱싱 ───────────────────────────────
def index_to_es(**context):
    """전처리된 데이터를 Elasticsearch에 인덱싱"""
    from elasticsearch import Elasticsearch, helpers
    import numpy as np
    import pandas as pd
    
    processed_path = context['ti'].xcom_pull(task_ids='preprocess')
    df = pd.read_csv(processed_path)
    
    # host.docker.internal = 컨테이너에서 Windows 호스트(localhost)를 가리키는 주소. mrs-ES가 localhost:9200에 떠 있으니 이걸로 접근 가능.
    es = Elasticsearch("http://host.docker.internal:9200")
    
    INDEX_NAME = "mrs-playlists" # ← 기존 인덱스명과 통일

    # 인덱스 매핑 사전 정의
    mapping = {
        "mappings": {
            "properties": {
                "playlist_id":  {"type": "integer"},
                "tag_vector":   {"type": "dense_vector", "dims": 29, "index": True, "similarity": "l2_norm"},
                "num_of_songs": {"type": "integer"}
            }
        }
    }

    # 기존 인덱스 삭제 후 재생성
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"기존 인덱스 삭제: {INDEX_NAME}")

    es.indices.create(index=INDEX_NAME, mappings=mapping["mappings"])
    print(f"인덱스 생성 완료: {INDEX_NAME}")
    
    tag_cols = [f'tag{i}' for i in range(29)]
    # 데이터 타입 강제 변환 (계산을 위해 숫자형으로)
    df[tag_cols] = df[tag_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    actions = []
    for _, row in df.iterrows():
        vector = row[tag_cols].values.astype(float)
        
        # L2 정규화
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = (vector / norm).tolist()
        else:
            vector = vector.tolist()

        # 벌크 작업을 위한 액션 생성
        doc = {
            "_index": "genie-playlists",
            "_id": int(row['playlist_id']),
            "_source": {
                'playlist_id': int(row['playlist_id']),
                'tag_vector': vector,
                'num_of_songs': int(row['num_of_songs']),
                'indexed_at': context['ds']
            }
        }
        actions.append(doc)

        # 500개 단위로 벌크 실행 (메모리 효율)
        if len(actions) >= 500:
            # helpers.bulk(es, actions)
            success, failed = helpers.bulk(es, actions, raise_on_error=False, stats_only=True)  # ← 교체
            print(f"bulk 중간 결과 - 성공: {success}, 실패: {failed}")
            
            actions = []

    # 남은 데이터 처리
    if actions:
        # helpers.bulk(es, actions)
        success, failed = helpers.bulk(es, actions, raise_on_error=False, stats_only=True)
        print(f"bulk 결과 - 성공: {success}, 실패: {failed}")  # ← 실패 수 확인

    print(f"ES 인덱싱 완료: {len(df)}개")

    es.indices.refresh(index=INDEX_NAME)
    count = es.count(index=INDEX_NAME)["count"]
    print(f"ES 저장 문서 수: {count}")


# ── DAG 정의 ──────────────────────────────────────────
with DAG(
    dag_id='genie_playlist_pipeline',
    default_args=default_args,
    description='Genie 플레이리스트 태그 벡터 추출 → 전처리 → Elasticsearch 인덱싱',
    schedule_interval='0 2 * * 1',  # 매주 월요일 새벽 2시
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['genie', 'music', 'crawling', 'pipeline'],
) as dag:

    task_load_csv = PythonOperator(task_id='load_tag_csv', python_callable=load_tag_csv)
    task_extract  = PythonOperator(task_id='extract_playlist_tags', python_callable=extract_playlist_tags)
    task_preprocess = PythonOperator(task_id='preprocess', python_callable=preprocess)
    task_index_es = PythonOperator(task_id='index_to_es', python_callable=index_to_es)

    # 4개의 Task 순서대로 연결되도록 파이프라인 수정
    task_load_csv >> task_extract >> task_preprocess >> task_index_es