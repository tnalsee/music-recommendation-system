# 환경 설정

### 1. 가상환경 설정
```bash
cd coconut2\

conda activate coconut2

pip install --upgrade pip
```

### 2. 모듈 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python main.py
```


### 4. 테스트 코드
* 사진 1장
```bash
curl -X POST "http://127.0.0.1:8000/api/upload" -F "images=@test_images/image_2.jpg"
```

* 사진 2장
```bash
curl -X POST "http://127.0.0.1:8000/api/upload" \
-F "images=@test_images/image_2.jpg" \
-F "images=@test_images/image_5.jpg"
```