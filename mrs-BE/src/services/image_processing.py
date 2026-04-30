import os
import torch
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import torch.nn.functional as F
import io


class ImageProcessor:
    def __init__(self, model_path, num_labels=29):
        # 1. 모델 구조 정의 (HuggingFace의 기본 뼈대)
        self.model = ViTForImageClassification.from_pretrained(
            "google/vit-base-patch16-224-in21k", 
            num_labels=num_labels
        )
        
        try:
            # 2. .pth 파일 전체 로드
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        
            # 3. 체크포인트 내부에서 실제 가중치(model_state_dict)만 꺼내기
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
                print("Found 'model_state_dict' in checkpoint. Extracting weights...")
            else:
                state_dict = checkpoint
                
            # 4. 가중치 로드 (이제는 strict=True로 해도 성공해야 합니다)
            self.model.load_state_dict(state_dict, strict=True)
            print(f"Successfully loaded weights from {model_path}")
            
        except Exception as e:
            print(f"Error loading model weights: {e}")
            # 만약 레이어 이름이 미세하게 다르다면 다시 strict=False를 시도해볼 수 있습니다.
            self.model.load_state_dict(state_dict, strict=False)
            print("Loaded weights with strict=False. Some layers might be missing.")

        self.model.eval()

        # 이미지 프로세서 초기화
        self.image_processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")



    def process_image(self, image_path, new_size=(224, 224), simulate_loss=True):
        img = Image.open(image_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

        if simulate_loss:
            buffer = io.BytesIO()
            resized_img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            resized_img = Image.open(buffer)

        return resized_img
    
    
    def extract_tags(self, image_path, threshold=0.6):
        # 이미지를 처리하고 모델에 입력하기 위해 전처리합니다.
        resized_img = self.process_image(image_path)
        inputs = self.image_processor(images=resized_img, return_tensors="pt")

        # 모델을 사용하여 태그 확률을 예측합니다.
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # 다중 태그 분류이므로 Sigmoid 사용
            probabilities = torch.sigmoid(logits).squeeze() # 차원을 1차원으로 압축 (29,)
            
            # 디버깅용 로그
            print(f"DEBUG - Max Prob: {probabilities.max().item():.4f}")
            
            # 디버깅: 전체 확률 분포 확인
            #print(f"DEBUG - Probabilities: {probabilities.tolist()}") 
            # 디버깅: 모델이 계산한 확률 중 최대값이 얼마인지 확인
            #print(f"DEBUG - Max Probability: {probabilities.max().item():.4f}")
        
            # 임계값 적용하여 0 또는 1로 변환
            predictions = (probabilities >= threshold).int()
            
        # 예측 결과(0/1)와 실제 확률값(0~1)을 모두 numpy 배열로 반환합니다.
        return predictions.cpu().numpy(), probabilities.cpu().numpy()