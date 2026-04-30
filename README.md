# 🎵 이미지 기반 음악 추천 시스템

> 사진 N장으로 분위기에 맞는 음악을 추천하는 AI 파이프라인

<br>

## 📌 프로젝트 개요

업로드한 이미지에서 ViT 모델로 감성 태그를 추출하고,  
Elasticsearch kNN 검색으로 분위기에 맞는 플레이리스트를 추천합니다.  
추천 결과는 LLM이 자연어로 추천 이유를 생성해 사용자에게 전달합니다.

<br>

## 🏗️ 시스템 아키텍처

```
[이미지 입력]
     ↓
[ViT 추론] → 29차원 감성 태그 벡터 (Sigmoid + 임계값 0.6)
     ↓
[Elasticsearch kNN 검색] → 유사 플레이리스트 Top 5 (인기도 기준)
     ↓
[LLM 추천 이유 생성] → 2문장, 존댓말
     ↓
[Flutter 앱 출력]
```

<br>

## 🗂️ 폴더 구조

```
music-recommend-system/
├── mrs-BE/                  # FastAPI 백엔드
│   ├── src/
│   │   ├── api/             # 라우터
│   │   ├── ml/              # ViT 모델 (*.pth 제외)
│   │   ├── services/        # 핵심 비즈니스 로직
│   │   │   ├── image_processing.py       # ViT 추론
│   │   │   ├── recommend_playlist_songs_es.py  # ES kNN 검색
│   │   │   └── llm_explanation.py        # LLM 추천 이유 생성
│   │   └── settings/
│   │       └── config.ini.example        # API 키 설정 예시
│   └── test_images/         # 테스트용 이미지 5장
├── mrs-ES/                  # Elasticsearch + ELK Stack
│   ├── docker-compose.yml   # ES, Kibana, Logstash, Filebeat
│   ├── es_indexer.py        # 플레이리스트 벡터 인덱싱
│   └── benchmark.py         # FAISS vs ES 성능 비교
├── mrs-FE/                  # Flutter 프론트엔드
└── airflow-pipeline/        # 플레이리스트 인덱싱 자동화 파이프라인 (Airflow DAG)
    └── dags/
        └── playlist_pipeline.py
```

<br>

## ⚙️ 기술 스택

| 분류 | 기술 |
|---|---|
| AI 모델 | ViT (vit-base-patch16-224), Hugging Face, PyTorch |
| 벡터 검색 | Elasticsearch 8.13 |
| 모니터링 | Kibana, Logstash, Filebeat |
| 파이프라인 | Apache Airflow 2.9.1 |
| 백엔드 | FastAPI |
| 프론트엔드 | Flutter |
| 인프라 | Docker, Docker Compose |
| 언어 | Python 3.9.6 |

<br>

## 🔑 2가지 데이터 파이프라인

### Pipeline A — 이미지 학습 파이프라인
```
Unsplash 이미지 수집 (Selenium)
→ 리사이징 224×224 + Stratified Split (7:2:1)
→ ViT 전이학습 (Colab, CrossEntropyLoss, AdamW, epoch=10)
→ .pth 저장
```

### Pipeline B — 플레이리스트 인덱싱 파이프라인 (Airflow DAG로 자동화)
```
Genie Music 플레이리스트 CSV 로드 (Airflow: load_tag_csv)
→ 29개 태그 멀티-핫 벡터 추출 (extract_playlist_tags)
→ 중복 제거 · 결측값 처리 (preprocess)
→ Elasticsearch dense_vector bulk 인덱싱 (index_to_es, 500개 단위)
```
스케줄: 매주 월요일 새벽 2시 자동 실행 (`airflow-pipeline/` 모듈)

<br>

## 📊 주요 결과

| 항목 | 수치 |
|---|---|
| 수집 이미지 | 30,121장 |
| 수집 플레이리스트 | 5,431개 |
| ViT Subset Accuracy | 59.18% |
| 전처리 자동화 | 수동 25시간 → 1시간 |
| FAISS vs ES 검색 속도 | 0.72ms vs 71.48ms |
| ES 선택 이유 | 영속성·RESTful·확장성 |

<br>

## 🔍 FAISS → Elasticsearch 마이그레이션

프로토타입 단계에서 FAISS로 검색 기능을 빠르게 검증했지만, 두 가지 운영 문제를 확인했습니다.

- **문제 1.** 인덱스를 메모리에 로드하는 구조 → 서비스 재시작 시 매번 재빌드 필요
- **문제 2.** 검색이 Python 프로세스에 종속 → 서비스 간 독립 운영 불가

**① 인덱스 영속성**, **② 서비스 간 독립 운영**을 핵심 요건으로 정의하고 두 기술을 비교했습니다.

| 항목 | FAISS (기존) | Elasticsearch (전환 후) |
|---|---|---|
| 인덱스 위치 | 서버 메모리 (휘발성) | 독립 컨테이너 (영속성) |
| 검색 방식 | IndexFlatL2 | HNSW 기반 kNN API |
| 운영 환경 | Python 프로세스 내부 | Docker Compose 기반 분리 환경 |
| 인터페이스 | Python 함수 호출 | RESTful API |

**성능 측정 결과**

| 항목 | FAISS | Elasticsearch |
|---|---|---|
| 평균 응답시간 | 0.72ms | 71.48ms |
| p95 응답시간 | 1.42ms | 117.70ms |

ES가 FAISS 대비 약 100배 느리지만, 검색 응답시간 71.48ms는 이미지 업로드 후 추천 결과를 반환하는 서비스 흐름에서 허용 가능한 수준으로 판단했습니다.  
속도보다 **인덱스 영속성과 서비스 분리** 기준으로 Elasticsearch를 선택했습니다.

<br>

## 🚀 실행 방법

### 1. 환경 설정
```bash
cp mrs-BE/src/settings/config.ini.example mrs-BE/src/settings/config.ini
# config.ini에 Spotify, OpenAI API 키 입력
```

### 2. Elasticsearch 실행
```bash
cd mrs-ES
docker compose up -d
python es_indexer.py  # 플레이리스트 벡터 인덱싱
```

### 3. FastAPI 서버 실행
```bash
cd mrs-BE
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### 4. Airflow DAG 실행 (선택)
```bash
cd airflow-pipeline
docker compose up -d
# http://localhost:8080 → genie_playlist_pipeline DAG 실행
```
