import numpy as np
from elasticsearch import Elasticsearch

INDEX_NAME = "mrs-playlists"

class SimilaritySearch:
    """FAISS 버전과 동일한 인터페이스 유지 - image_to_song.py import만 교체하면 동작"""

    def __init__(self, tag_table_path=None):
        # ES 버전은 tag_table_path 불필요, 인터페이스 호환용으로만 받음
        self.es = Elasticsearch("http://localhost:9200")

    def build_index(self):
        # ES는 사전에 인덱싱 완료 상태 → 여기서는 연결 확인만
        if not self.es.indices.exists(index=INDEX_NAME):
            raise RuntimeError(f"ES 인덱스 없음: {INDEX_NAME} — es_indexer.py 먼저 실행")
        print(f"ES 인덱스 연결 확인: {INDEX_NAME}")

    def search_similar_playlists(self, query_tags, k=15):
        # 쿼리 벡터 정규화
        query_vec = np.array(query_tags, dtype="float32")
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm
        # norm == 0이면 정규화 안 된 zero 벡터 그대로 ES로 전송 → 검색 결과 의미 없음
        if norm == 0:
            raise ValueError("쿼리 태그 벡터가 모두 0입니다. 유효한 태그가 없습니다.")

        # kNN 검색
        response = self.es.search(
            index=INDEX_NAME,
            knn={
                "field": "tag_vector",
                "query_vector": query_vec.tolist(),
                "k": k,
                "num_candidates": 100
            },
            source=["playlist_songs_id"]
        )


        hits = response["hits"]["hits"]
        return [hit["_source"]["playlist_songs_id"] for hit in hits]