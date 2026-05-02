"""
01_generate_data.py
기존 tag_table3.csv(5,431행)를 기반으로 50만 건 확장 데이터 생성

확장 방식:
- playlist_id: 순차 증가 (중복 없음)
- tag 조합: 원본 분포 기반 + 노이즈 추가 (다양성 증가)
- num_of_songs: 원본 분포 기반 랜덤 샘플링
"""

import pandas as pd
import numpy as np
import os
import time

# ── 설정 ──────────────────────────────────────
ORIGINAL_CSV = 'data/tag_table3.csv'
OUTPUT_CSV   = 'data/tag_table_500k.csv'
TARGET_ROWS  = 500_000
TAG_COLS     = [f'tag{i}' for i in range(29)]
RANDOM_SEED  = 42

np.random.seed(RANDOM_SEED)

# ── 원본 로드 ──────────────────────────────────
print("원본 데이터 로드 중...")
df_origin = pd.read_csv(ORIGINAL_CSV)
print(f"원본: {len(df_origin):,}행 × {len(df_origin.columns)}열")

# ── 태그 분포 분석 ──────────────────────────────
# 각 태그의 활성화 확률 계산 (원본 분포 보존)
tag_probs = df_origin[TAG_COLS].mean().values
print(f"\n태그 활성화 확률 (상위 5개):")
for i, p in sorted(enumerate(tag_probs), key=lambda x: -x[1])[:5]:
    print(f"  tag{i}: {p:.3f}")

# ── 50만 건 생성 ──────────────────────────────
print(f"\n{TARGET_ROWS:,}건 데이터 생성 중...")
start = time.time()

# 1. playlist_id: 원본 최대값 이후부터 순차 증가
max_id = df_origin['playlist_id'].max()
new_ids = np.arange(max_id + 1, max_id + 1 + TARGET_ROWS)

# 2. 태그 벡터: 원본 확률 분포 기반 베르누이 샘플링 + 노이즈
#    노이즈: 태그 확률에 ±0.05 랜덤 편차 추가 → 다양성 증가
noise = np.random.uniform(-0.05, 0.05, size=(TARGET_ROWS, 29))
probs_with_noise = np.clip(tag_probs + noise, 0.02, 0.98)
tag_matrix = (np.random.rand(TARGET_ROWS, 29) < probs_with_noise).astype(int)

# 태그가 하나도 없는 행 방지: 최소 1개 태그 강제 활성화
zero_rows = np.where(tag_matrix.sum(axis=1) == 0)[0]
for idx in zero_rows:
    rand_tag = np.random.randint(0, 29)
    tag_matrix[idx, rand_tag] = 1

# 3. num_of_songs: 원본 분포에서 복원 샘플링
songs_pool = df_origin['num_of_songs'].values
new_songs = np.random.choice(songs_pool, size=TARGET_ROWS, replace=True)

# 4. DataFrame 조립
df_new = pd.DataFrame(tag_matrix, columns=TAG_COLS)
df_new.insert(0, 'playlist_id', new_ids)
df_new['num_of_songs'] = new_songs

elapsed = time.time() - start
print(f"생성 완료: {len(df_new):,}행 ({elapsed:.2f}초)")

# ── 검증 ──────────────────────────────────────
print(f"\n[검증]")
print(f"playlist_id 중복: {df_new['playlist_id'].duplicated().sum()}개")
print(f"태그 0개 행: {(df_new[TAG_COLS].sum(axis=1) == 0).sum()}개")
print(f"num_of_songs 분포:\n{df_new['num_of_songs'].describe().round(1)}")

# 태그별 활성화 비율 비교 (원본 vs 생성)
print(f"\n태그 활성화 비율 비교 (상위 5개 태그):")
print(f"{'태그':<8} {'원본':>8} {'생성':>8}")
for i in sorted(range(29), key=lambda x: -tag_probs[x])[:5]:
    orig = tag_probs[i]
    new  = df_new[f'tag{i}'].mean()
    print(f"tag{i:<4}  {orig:>8.3f} {new:>8.3f}")

# ── 저장 ──────────────────────────────────────
os.makedirs('data', exist_ok=True)
df_new.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"\n저장 완료: {OUTPUT_CSV}")
print(f"파일 크기: {os.path.getsize(OUTPUT_CSV) / 1024 / 1024:.1f} MB")
