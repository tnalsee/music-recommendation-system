# 🎵 Genie Playlist Pipeline (Airflow DAG)

> Genie Music 플레이리스트 CSV를 읽어 29차원 멀티-핫 태그 벡터로 변환하고 Elasticsearch에 자동 인덱싱하는 데이터 파이프라인

<br>

## 📌 개요

Apache Airflow로 오케스트레이션된 4단계 DAG입니다.  
플레이리스트 CSV에서 29차원 멀티-핫 태그 벡터를 추출·정규화하고,  
Elasticsearch에 bulk 인덱싱하는 전 과정을 자동화합니다.

스케줄: **매주 월요일 새벽 2시** 자동 실행

<br>

## 🏗️ DAG 구조

```
load_tag_csv
     ↓
extract_playlist_tags
     ↓
preprocess
     ↓
index_to_es
```

| Task | 역할 |
|---|---|
| `load_tag_csv` | tag_table3.csv 로드 및 경로 XCom 전달 |
| `extract_playlist_tags` | playlist_id + tag0~tag28 + num_of_songs 추출 |
| `preprocess` | 중복 제거, 결측값 처리, num_of_songs=0 행 제거 |
| `index_to_es` | L2 정규화 → dense_vector bulk 인덱싱 (500개 단위) |

<br>

## ⚙️ 기술 스택

| 항목 | 내용 |
|---|---|
| 오케스트레이션 | Apache Airflow 2.9.1 |
| 벡터 검색 | Elasticsearch 8.13 |
| 인프라 | Docker, Docker Compose |
| 언어 | Python 3.x |
| 주요 라이브러리 | pandas, numpy, elasticsearch-py |

<br>

## 📁 폴더 구조

```
airflow-pipeline/
├── dags/
│   └── playlist_pipeline.py   # DAG 정의
├── data/                       # CSV 데이터 (gitignore)
├── logs/                       # Airflow 로그 (gitignore)
├── plugins/
├── config/
├── Dockerfile                  # elasticsearch 패키지 포함 커스텀 이미지
└── docker-compose.yaml
```

<br>

## 🚀 실행 방법

### 1. Elasticsearch 먼저 실행 (mrs-ES)
```bash
cd ../mrs-ES
docker compose up -d
```

### 2. Airflow 실행
```bash
cd airflow-pipeline
docker compose up -d
```

### 3. DAG 실행
```
http://localhost:8080
ID: airflow / PW: airflow
→ genie_playlist_pipeline DAG 활성화 → ▶ 클릭
```

<br>

## 🔑 설계 포인트

**1. Dockerfile로 의존성 관리**

컨테이너 시작마다 pip install이 실행되는 `_PIP_ADDITIONAL_REQUIREMENTS` 방식 대신,  
`elasticsearch==8.13.0`을 미리 설치한 커스텀 이미지를 빌드했습니다.

```dockerfile
FROM apache/airflow:2.9.1
RUN pip install --no-cache-dir elasticsearch==8.13.0
```

**2. XCom으로 태스크 간 파일 경로 전달**

각 태스크는 처리 결과를 CSV로 저장하고, 파일 경로를 XCom으로 전달합니다.  
중간 결과를 단계별로 파일로 보존해 특정 태스크만 독립적으로 재실행할 수 있습니다.

**3. Bulk 인덱싱 (500개 단위)**

`helpers.bulk()`로 500개 단위 분할 인덱싱을 적용했습니다.  
네트워크 오류 발생 시 재시도 범위를 500개로 제한해 안정성을 높였습니다.

**4. L2 정규화**

인덱싱 전 L2 정규화를 적용해 벡터 크기를 통일했습니다.

```python
norm = np.linalg.norm(vector)
vector = (vector / norm).tolist() if norm > 0 else vector.tolist()
```

**5. host.docker.internal로 외부 ES 연결**

Airflow 컨테이너에서 별도 네트워크의 Elasticsearch에 접근하기 위해  
`host.docker.internal:9200`을 사용했습니다.
