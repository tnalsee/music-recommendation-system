from fastapi import APIRouter, UploadFile, File
from typing import List
from fastapi.responses import PlainTextResponse # 예쁘게 보기위해 추가

from ..utils.image_module import *
from ..services.image_to_song import get_recommend_songs
from ..services.llm_explanation import generate_explanation

router = APIRouter()

@router.post("/upload")
def get_songs_title(images: List[UploadFile] = File(...)):
    # 1. 이전 업로드 디렉토리 초기화
    initialize_upload_directory() 
    
    try:
        # 2. 이미지 저장 및 절대 경로 리스트 반환
        image_paths = save_images_to_directory(images) 
        
        # 3. 추천 함수로부터 4개의 인자를 리턴받음 (곡 리스트, 한글 태그 리스트, 태그 벡터, 확률 딕셔너리)
        songs_dict, tags_korean, tags_vector, prob_dict = get_recommend_songs(image_paths)
        
        # 4. LLM 설명 생성
        explanation = generate_explanation(songs_dict, tags_korean)
        
        # ----- 보기 좋은 형태로 데이터 가공 --------
        # 태그: '휴식(60.2%)', '해변(33.2%)', '여유(24.8%)' 형태로 묶기
        # 단, 확률이 임계값(60%)을 넘는 태그만 화면에 표시하도록 변경
        tag_with_probs = []
        for tag in tags_korean:
            prob = prob_dict[tag]
            if prob >= 60.0:  # 화면 표시 임계값 설정
                tag_with_probs.append(f"'{tag}'({prob}%)")

        # 만약 위 조건에 맞는 태그가 하나도 없다면, 가장 높은 것 하나라도 보여주기 위해 예외 처리
        if not tag_with_probs and tags_korean:
            best_tag = tags_korean[0]
            tag_with_probs.append(f"'{best_tag}'({prob_dict[best_tag]}%)")

        formatted_tags = ", ".join(tag_with_probs)
        
        # 추천 곡: 아티스트-제목 형태로 줄바꿈하여 묶기
        formatted_songs = "\n".join([f"{artist} - {title}" for title, artist in songs_dict.items()])
        
        # 최종 결과 조립
        result_text = f"""
🏷️ 태그벡터 
{tags_vector}

🔎 이미지에서 추출된 태그: {formatted_tags}

🎧 태그 기반 추천 곡 리스트
{formatted_songs}

🪄 추천 이유
{explanation}"""

        # 4. JSON 대신 PlainTextResponse로 텍스트 자체를 반환!
        return PlainTextResponse(content=result_text)

    except Exception as e:
        print(f"ROUTER ERROR: {e}")
        return PlainTextResponse(content=f"오류가 발생했습니다: {e}", status_code=500)