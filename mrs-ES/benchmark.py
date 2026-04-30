import sys
import time
import numpy as np

sys.path.append(r"E:\coconut2\mrs-BE")

from src.services.recommend_playlist_songs import SimilaritySearch as FAISSSearch
from src.services.recommend_playlist_songs_es import SimilaritySearch as ESSearch

TAG_TABLE_PATH = r"E:\coconut2\mrs-BE\csv\tag_table3.csv"
QUERY_TAGS = [0] * 29
QUERY_TAGS[0] = 1
N_TRIALS = 100
K = 15

# ── FAISS 벤치마크 ──────────────────────────────
faiss_search = FAISSSearch(tag_table_path=TAG_TABLE_PATH)
faiss_search.build_index()

faiss_times = []
for _ in range(N_TRIALS):
    start = time.perf_counter()
    faiss_search.search_similar_playlists(QUERY_TAGS, k=K)
    faiss_times.append(time.perf_counter() - start)

# ── ES 벤치마크 ─────────────────────────────────
es_search = ESSearch()
es_search.build_index()

es_times = []
for _ in range(N_TRIALS):
    start = time.perf_counter()
    es_search.search_similar_playlists(QUERY_TAGS, k=K)
    es_times.append(time.perf_counter() - start)

# ── 결과 출력 ───────────────────────────────────
print("========📍 FAISS 📍========")
print(f"평균:  {np.mean(faiss_times)*1000:.2f}ms")
print(f"p95:   {np.percentile(faiss_times, 95)*1000:.2f}ms")
print(f"최소:  {np.min(faiss_times)*1000:.2f}ms")
print(f"최대:  {np.max(faiss_times)*1000:.2f}ms")

print("\n===📍 Elasticsearch 📍===")
print(f"평균:  {np.mean(es_times)*1000:.2f}ms")
print(f"p95:   {np.percentile(es_times, 95)*1000:.2f}ms")
print(f"최소:  {np.min(es_times)*1000:.2f}ms")
print(f"최대:  {np.max(es_times)*1000:.2f}ms")

print("\n========📊 비교 📊========")
ratio = np.mean(es_times) / np.mean(faiss_times)
print(f"ES 평균 / FAISS 평균: {ratio:.1f}x")
print(f"ES가 FAISS보다 {'느림' if ratio > 1 else '빠름'} ({abs(ratio-1)*100:.0f}%)")