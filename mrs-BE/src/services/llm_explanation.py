from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# API KEY 입력!!
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_explanation(songs_dict: dict, tags: list) -> str:
    """
    추천된 곡 목록과 이미지에서 추출된 태그를 받아
    왜 이 음악이 이 공간에 어울리는지 설명을 생성합니다.
    """
    songs_str = ", ".join([f"{title}({artist})" for title, artist in songs_dict.items()])
    tags_str = ", ".join(tags)

    prompt = f"""
    당신은 감성적인 음악 큐레이터입니다.
    
    다음 태그를 기반으로 사진의 분위기를 해석하고, 음악 추천 이유를 작성하세요.
    
    태그: {tags_str}
    추천곡 목록: {songs_str}

    아래 조건에 맞게 추천 이유를 작성하세요.
    
    [작성 조건] 
    - 반드시 2문장으로 작성
    - 태그 기반 공간 분위기와 음악 감성을 연결하여 설명할 것 
    - 추천 곡 중 정확히 2곡만 선택하여 언급 
    - 곡 표기 형식: ‘아티스트명-곡명’ (따옴표 포함, 예: ‘싸이-낙원’)
    - 모든 문장은 존댓말로 작성 (~습니다 / ~합니다 체만 사용)
    - 반말, 평서형 (~다, ~해준다 등) 절대 사용 금지
    - 감성적이되 담백한 문체 사용
    - 이 음악들이 왜 이 공간과 어울리는 지를 설득하는 표현 사용
        
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    return response.choices[0].message.content