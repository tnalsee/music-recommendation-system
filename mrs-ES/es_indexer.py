import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch, helpers # helpers 모듈 추가

CSV_PATH = r"E:\coconut2\mrs-BE\csv\tag_table3.csv"
INDEX_NAME = "mrs-playlists"

# Elasticsearch 8.x 버전의 경우 로컬 테스트 시 보안 경고가 뜰 수 있으므로 환경에 맞게 설정하세요.
es = Elasticsearch("http://localhost:9200")

# 1. 인덱스 생성
mapping = {
    "mappings": {
        "properties": {
            "playlist_id":       {"type": "integer"},
            "tag_vector":        {"type": "dense_vector", "dims": 29, "index": True, "similarity": "l2_norm"},
            "num_of_songs":      {"type": "integer"},
            "playlist_songs_id": {"type": "keyword"}
        }
    }
}

if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
    print(f"기존 인덱스 삭제: {INDEX_NAME}")

# [수정됨] Elasticsearch 8.x에서는 body 파라미터가 제거되었습니다. mappings를 직접 전달해야 합니다.
es.indices.create(index=INDEX_NAME, mappings=mapping["mappings"])
print(f"인덱스 생성 완료: {INDEX_NAME}")

# 2. CSV 로드 및 벡터 정규화
df = pd.read_csv(CSV_PATH)
tag_cols = [f"tag{i}" for i in range(29)]
tag_vectors = df[tag_cols].values.astype("float32")

norms = np.linalg.norm(tag_vectors, axis=1, keepdims=True)
norms[norms == 0] = 1
tag_vectors = tag_vectors / norms

# 3. 벌크 인덱싱 [수정됨] helpers.bulk()를 사용하여 메모리 효율성과 안정성 증가
def generate_actions():
    for i, row in df.iterrows():
        tag_fields = {f"tag{j}": int(row[f"tag{j}"]) for j in range(29)}
        source = {
            "playlist_id":       int(row["playlist_id"]),
            "tag_vector":        tag_vectors[i].tolist(),
            "num_of_songs":      int(row["num_of_songs"]),
            "playlist_songs_id": str(row["playlist_songs_id"])
        }
        source.update(tag_fields)
        yield {
            "_index": INDEX_NAME,
            "_id": str(i),
            "_source": source
        }
# 제너레이터를 통해 대용량 데이터도 청크(chunk) 단위로 안전하게 전송합니다.
helpers.bulk(es, generate_actions())
print(f"인덱싱 완료: {len(df)}개 문서")

# 4. refresh 후 카운트
es.indices.refresh(index=INDEX_NAME)
count = es.count(index=INDEX_NAME)["count"]
print(f"ES 저장 문서 수: {count}")