"""
03_spark_benchmark.py
PySpark로 동일한 작업 수행 후 pandas와 시간 비교
"""

import time
import json
import os
import unicodedata

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

TAG_COLS    = [f'tag{i}' for i in range(29)]
INPUT_CSV   = 'data/tag_table_500k.csv'
OUTPUT_JSON = 'results/spark_results.json'

os.makedirs('results', exist_ok=True)

def pad(text, width):
    count = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)
    return text + ' ' * max(0, width - count)

print("=" * 50)
print("SparkSession 초기화 중...")
t = time.time()
spark = SparkSession.builder \
    .appName("playlist_cooccurrence") \
    .master("local[4]") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
print(f"초기화 완료: {time.time() - t:.2f}초 (벤치마크 제외)")

results = {}
total_start = time.time()

print("\n" + "=" * 50)
print("Step 1. CSV 로드")
t = time.time()
df = spark.read.csv(INPUT_CSV, header=True, inferSchema=True)
df.cache()
df.count()
elapsed = time.time() - t
results['load_sec'] = round(elapsed, 4)
print(f"  행 수: {df.count():,}")
print(f"  소요시간: {elapsed:.4f}초")

print("\nStep 2. 전처리")
t = time.time()
df = df.dropDuplicates(['playlist_id'])
df = df.dropna()
df = df.filter(F.col('num_of_songs') > 0)
for col in TAG_COLS:
    df = df.withColumn(col, F.col(col).cast(IntegerType()))
df.cache()
row_count = df.count()
elapsed = time.time() - t
results['preprocess_sec'] = round(elapsed, 4)
print(f"  전처리 후 행 수: {row_count:,}")
print(f"  소요시간: {elapsed:.4f}초")

print("\nStep 3. Co-occurrence matrix 계산")
print("  (explode + self join 방식)")
t = time.time()

df_exploded = df.select(
    'playlist_id',
    F.explode(
        F.array(*[F.when(F.col(c) == 1, F.lit(c)).otherwise(F.lit(None)) for c in TAG_COLS])
    ).alias('tag')
).filter(F.col('tag').isNotNull())

df_co = df_exploded.alias('a').join(
    df_exploded.alias('b'),
    on='playlist_id'
).filter(
    F.col('a.tag') < F.col('b.tag')
).groupBy(
    F.col('a.tag').alias('tag_a'),
    F.col('b.tag').alias('tag_b')
).agg(
    F.count('*').alias('count')
)

df_co.cache()
df_co.count()
elapsed = time.time() - t
results['cooccurrence_sec'] = round(elapsed, 4)
print(f"  소요시간: {elapsed:.4f}초")

print("\nStep 4. 상위 10 co-occurrence 쌍 추출")
t = time.time()
top10 = df_co.orderBy(F.col('count').desc()).limit(10).collect()
elapsed = time.time() - t
results['top10_sec'] = round(elapsed, 4)
print(f"  소요시간: {elapsed:.4f}초")
print(f"\n  [상위 10 co-occurrence 쌍]")
print(f"  {'tag_a':<8} {'tag_b':<8} {'count':>10}")
for row in top10:
    print(f"  {row['tag_a']:<8} {row['tag_b']:<8} {row['count']:>10,}")

print("\nStep 5. 태그별 플레이리스트 수 집계")
t = time.time()
tag_counts = df_exploded.groupBy('tag').agg(
    F.count('*').alias('count')
).orderBy(F.col('count').desc())
top5_tags = tag_counts.limit(5).collect()
elapsed = time.time() - t
results['groupby_sec'] = round(elapsed, 4)
print(f"  소요시간: {elapsed:.4f}초")
print(f"\n  [태그별 플레이리스트 수 상위 5개]")
for row in top5_tags:
    print(f"  {row['tag']}: {row['count']:,}")

total_elapsed = time.time() - total_start
results['total_sec'] = round(total_elapsed, 4)
results['rows'] = row_count
results['partitions'] = 4

print("\n" + "=" * 50)
print(f"PySpark 총 소요시간: {total_elapsed:.4f}초")
print("=" * 50)

pandas_json = 'results/pandas_results.json'
if os.path.exists(pandas_json):
    with open(pandas_json, 'r') as f:
        pandas_results = json.load(f)

    steps = [
        ('CSV 로드',      'load_sec'),
        ('전처리',        'preprocess_sec'),
        ('co-occurrence', 'cooccurrence_sec'),
        ('상위10 추출',   'top10_sec'),
        ('태그 집계',     'groupby_sec'),
        ('총 소요시간',   'total_sec'),
    ]
    rows_data = []
    for label, key in steps:
        p = pandas_results.get(key, 0)
        s = results.get(key, 0)
        ratio = p / s if s > 0 else 0
        arrow = "🔺" if ratio < 1 else "✅"
        rows_data.append((label, p, s, arrow, ratio))

    print(f"\n{'─'*57}")
    print(f"{pad('항목', 16)} {'pandas':>10} {'PySpark':>11}  {'배율':>6}")
    print(f"{'─'*57}")
    for label, p, s, arrow, ratio in rows_data:
        print(f"{pad(label, 16)} {p:>10.4f}s {s:>10.4f}s  {arrow}{ratio:>4.1f}x")
    print(f"{'─'*57}")

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n결과 저장: {OUTPUT_JSON}")

spark.stop()
