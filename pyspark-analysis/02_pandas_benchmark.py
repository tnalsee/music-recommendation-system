"""
02_pandas_benchmark.py
pandas로 co-occurrence matrix 계산 시간 측정

측정 작업:
1. CSV 로드
2. 전처리 (중복 제거, 결측값 처리)
3. co-occurrence matrix 계산 (self join 대신 행렬 곱)
4. 상위 10 co-occurrence 쌍 추출
5. 태그별 플레이리스트 수 집계
"""

import pandas as pd
import numpy as np
import time
import json
import os

TAG_COLS = [f'tag{i}' for i in range(29)]
INPUT_CSV = 'data/tag_table_500k.csv'
OUTPUT_JSON = 'results/pandas_results.json'

os.makedirs('results', exist_ok=True)

results = {}
total_start = time.time()

# ── Step 1. CSV 로드 ──────────────────────────
print("=" * 50)
print("Step 1. CSV 로드")
t = time.time()
df = pd.read_csv(INPUT_CSV)
elapsed = time.time() - t
results['load_sec'] = round(elapsed, 4)
print(f"  행 수: {len(df):,}")
print(f"  소요시간: {elapsed:.4f}초")

# ── Step 2. 전처리 ───────────────────────────
print("\nStep 2. 전처리")
t = time.time()
df.drop_duplicates(subset=['playlist_id'], inplace=True)
df.dropna(inplace=True)
df = df[df['num_of_songs'] > 0]
df[TAG_COLS] = df[TAG_COLS].astype(int)
elapsed = time.time() - t
results['preprocess_sec'] = round(elapsed, 4)
print(f"  전처리 후 행 수: {len(df):,}")
print(f"  소요시간: {elapsed:.4f}초")

# ── Step 3. co-occurrence matrix ─────────────
print("\nStep 3. Co-occurrence matrix 계산")
print("  (태그 벡터 행렬 전치 곱: M^T × M)")
t = time.time()

tag_matrix = df[TAG_COLS].values.astype(np.float32)
# M^T × M → 29×29 co-occurrence matrix
co_matrix = tag_matrix.T @ tag_matrix
# 대각선 제거 (자기 자신과의 co-occurrence)
np.fill_diagonal(co_matrix, 0)

elapsed = time.time() - t
results['cooccurrence_sec'] = round(elapsed, 4)
print(f"  matrix shape: {co_matrix.shape}")
print(f"  소요시간: {elapsed:.4f}초")

# ── Step 4. 상위 10 co-occurrence 쌍 추출 ────
print("\nStep 4. 상위 10 co-occurrence 쌍 추출")
t = time.time()

pairs = []
for i in range(29):
    for j in range(i+1, 29):
        pairs.append({
            'tag_a': f'tag{i}',
            'tag_b': f'tag{j}',
            'count': int(co_matrix[i][j])
        })

df_pairs = pd.DataFrame(pairs).sort_values('count', ascending=False)
top10 = df_pairs.head(10)

elapsed = time.time() - t
results['top10_sec'] = round(elapsed, 4)
print(f"  소요시간: {elapsed:.4f}초")
print(f"\n  [상위 10 co-occurrence 쌍]")
print(f"  {'tag_a':<8} {'tag_b':<8} {'count':>10}")
for _, row in top10.iterrows():
    print(f"  {row['tag_a']:<8} {row['tag_b']:<8} {row['count']:>10,}")

# ── Step 5. 태그별 플레이리스트 수 집계 ───────
print("\nStep 5. 태그별 플레이리스트 수 집계")
t = time.time()

tag_counts = df[TAG_COLS].sum().sort_values(ascending=False)

elapsed = time.time() - t
results['groupby_sec'] = round(elapsed, 4)
print(f"  소요시간: {elapsed:.4f}초")
print(f"\n  [태그별 플레이리스트 수 상위 5개]")
for tag, cnt in tag_counts.head(5).items():
    print(f"  {tag}: {int(cnt):,}")

# ── 총 소요시간 ──────────────────────────────
total_elapsed = time.time() - total_start
results['total_sec'] = round(total_elapsed, 4)
results['rows'] = len(df)

print("\n" + "=" * 50)
print(f"pandas 총 소요시간: {total_elapsed:.4f}초")
print("=" * 50)

# ── 결과 저장 ────────────────────────────────
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n결과 저장: {OUTPUT_JSON}")
