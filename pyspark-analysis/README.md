# 📊 PySpark vs pandas 벤치마크 — 태그 Co-occurrence 분석

> "언제 Spark를 써야 하는가"를 직접 검증한 실험

<br>

## 📌 개요

음악 추천 시스템의 플레이리스트 태그 데이터를 대상으로,  
pandas와 PySpark의 처리 성능을 동일한 작업 조건에서 비교했습니다.

단순 속도 비교가 아닌, **데이터 규모와 환경에 따른 Spark 적용 기준**을 도출하는 것이 목적입니다.

<br>

## 🗂️ 폴더 구조

```
pyspark-analysis/
├── 01_generate_data.py      # 원본 분포 기반 50만 건 데이터 생성
├── 02_pandas_benchmark.py   # pandas 성능 측정
├── 03_spark_benchmark.py    # PySpark 성능 측정
├── 04_comparison.py         # 결과 비교 및 결론 출력
├── data/                    # CSV 데이터 (gitignore)
└── results/                 # 측정 결과 JSON
```

<br>

## ⚙️ 기술 스택

| 항목 | 내용 |
|---|---|
| 언어 | Python 3.x |
| 분산 처리 | PySpark 4.1.1 (local[4]) |
| 데이터 처리 | pandas, numpy |
| 런타임 | Java 21, Anaconda 가상환경 |

<br>

## 📐 실험 설계

### 데이터

| 항목 | 내용 |
|---|---|
| 원본 | tag_table3.csv — 5,431행 × 31열 |
| 실험용 | 원본 분포 기반으로 500,000행 생성 (약 92배 규모) |
| 태그 구조 | tag0~tag28 (29개) 멀티-핫 인코딩 벡터 |

원본을 단순 복제하지 않고, 태그별 활성화 확률에 ±0.05 노이즈를 추가해  
실제 데이터에 가까운 분포 다양성을 확보했습니다.

### 측정 작업 (pandas·PySpark 동일)

| 단계 | 작업 |
|---|---|
| 1 | CSV 로드 |
| 2 | 전처리 (중복 제거, 결측값 처리) |
| 3 | Co-occurrence matrix 계산 |
| 4 | 상위 10 co-occurrence 쌍 추출 |
| 5 | 태그별 플레이리스트 수 집계 |

**Co-occurrence 계산 방식 차이:**
- pandas + numpy: 태그 행렬 전치 곱 (M^T × M)
- PySpark: explode + self join + groupBy (분산 처리 방식)

<br>

## 📊 벤치마크 결과

| 항목 | pandas | PySpark |
|---|---|---|
| CSV 로드 | 1.28초 | 12.16초 |
| 전처리 | 0.04초 | 12.64초 |
| Co-occurrence | 0.07초 | 8.06초 |
| 상위10 추출 | 0.003초 | 0.57초 |
| 태그 집계 | 0.01초 | 2.01초 |
| **총 소요시간** | **1.41초** | **35.84초** |

**→ 로컬 환경(local[4]) + 50만 건 기준: pandas가 약 25배 빠름**

> SparkSession 초기화(약 14초)는 실제 운영 시 한 번만 실행 후 재사용되므로 벤치마크에서 제외했습니다.  
> 단발성 실행 시에는 초기화 시간도 실질적 오버헤드로 작용합니다.

<br>

## 🔍 분석 및 결론

### PySpark가 느린 원인

1. **local[4] 모드 한계** — 단일 머신에서 분산 처리 이점 없음. 스케줄링 오버헤드만 발생
2. **데이터 규모 미달** — 50만 건은 단일 머신 메모리 내 처리 가능한 규모
3. **Shuffle 비용** — explode + self join이 대규모 shuffle 유발 → 소규모에선 역효과
4. **Lazy evaluation 강제 실행** — cache() 후 count()로 lazy evaluation을 강제 실행하는 과정에서 추가 비용 발생

### Spark가 유리한 조건

- 단일 머신 메모리를 초과하는 데이터 규모
- 다중 노드 클러스터 환경
- 반복적 ML 연산 (MLlib)

### 실험의 의미

> 로컬 환경에서 pandas가 25배 빠른 결과는 **Spark의 실패가 아닙니다.**  
> 이는 Spark가 설계된 환경(대규모 분산 클러스터)과 다른 조건에서 실행했기 때문입니다.  
> 이번 실험을 통해 **데이터 규모와 인프라 환경에 따른 적절한 도구 선택 기준**을 직접 검증했습니다.

<br>

## 🚀 실행 방법

```bash
# 가상환경 활성화
conda activate pyspark-env

cd pyspark-analysis

# 1. 데이터 생성
python 01_generate_data.py

# 2. pandas 벤치마크
python 02_pandas_benchmark.py

# 3. PySpark 벤치마크
python 03_spark_benchmark.py

# 4. 결과 비교
python 04_comparison.py
```

### 환경 요구사항

- Java 17 이상 (PySpark 4.x 요구사항)
- PySpark 4.1.1
- pandas, numpy
