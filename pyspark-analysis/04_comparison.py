"""
04_comparison.py
pandas vs PySpark 벤치마크 결과 최종 비교 및 포트폴리오용 수치 정리
"""

import json
import unicodedata

def pad(text, width):
    count = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)
    return text + ' ' * max(0, width - count)

# ── 결과 로드 ─────────────────────────────────
with open('results/pandas_results.json', 'r') as f:
    p = json.load(f)
with open('results/spark_results.json', 'r') as f:
    s = json.load(f)

# ── 비교 테이블 ───────────────────────────────
steps = [
    ('CSV 로드',      'load_sec'),
    ('전처리',        'preprocess_sec'),
    ('co-occurrence', 'cooccurrence_sec'),
    ('상위10 추출',   'top10_sec'),
    ('태그 집계',     'groupby_sec'),
    ('총 소요시간',   'total_sec'),
]

print("=" * 60)
print("  pandas vs PySpark 벤치마크 최종 비교")
print(f"  데이터: {p['rows']:,}행 × 31열 (tag0~tag28 + 기타)")
print("=" * 60)

print(f"\n{pad('항목', 16)} {'pandas':>10} {'PySpark':>11}  {'배율':>8}")
print(f"{'─'*57}")
for label, key in steps:
    pv = p.get(key, 0)
    sv = s.get(key, 0)
    ratio = pv / sv if sv > 0 else 0
    if label == '총 소요시간':
        print(f"{'─'*57}")
    print(f"{pad(label, 16)} {pv:>10.4f}s {sv:>10.4f}s  {'🔺' if ratio < 1 else '✅'}{ratio:>5.1f}x")
print(f"{'─'*57}")

# ── 핵심 수치 ─────────────────────────────────
total_p = p['total_sec']
total_s = s['total_sec']
ratio_total = total_s / total_p

print(f"""
{'='*60}
  핵심 수치
{'='*60}

  데이터 규모    : {p['rows']:,}행 (원본 분포 기반으로 생성, 원본 대비 약 92배 규모)
  pandas 총시간  : {total_p:.2f}초
  PySpark 총시간 : {total_s:.2f}초
  속도 차이      : pandas가 {ratio_total:.1f}배 빠름 (로컬 환경 기준)

  병목 구간 (PySpark):
    - CSV 로드     : {s['load_sec']:.2f}초 (pandas 대비 {s['load_sec']/p['load_sec']:.0f}배 느림)
    - 전처리       : {s['preprocess_sec']:.2f}초 (lazy evaluation + 재캐싱 비용)
    - co-occurrence: {s['cooccurrence_sec']:.2f}초 (explode + self join shuffle 비용)

{'='*60}
  결론
{'='*60}

  로컬 환경(local[4]) + 50만 건 규모에서는 pandas가 약 {ratio_total:.0f}배 빠릅니다.

  PySpark가 느린 원인:
    1. SparkSession은 한 번 초기화 후 재사용하므로 벤치마크에서 제외했으나,
       초기화 자체에 약 14초 소요 → 단발성 실행 시 실질적 오버헤드 존재
    2. local[4] 모드: 단일 머신에서 분산 처리 이점 없음
    3. 50만 건은 단일 머신 메모리 내 처리 가능한 규모 → Spark 이점 발현 안됨
    4. self join 기반 co-occurrence: 대규모 shuffle 발생

  Spark가 유리한 조건:
    - 단일 머신 메모리를 초과하는 규모
    - 다중 노드 클러스터 환경
    - 반복적 ML 연산 (MLlib)

  이번 실험의 의미:
    단순 성능 비교가 아닌, '언제 Spark를 써야 하는가'
    판단 기준을 직접 검증한 실험입니다.
{'='*60}
""")