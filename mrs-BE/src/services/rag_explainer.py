import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

prompt = PromptTemplate.from_template("""
당신은 음악 추천 전문가입니다.
사용자가 업로드한 이미지에서 다음 태그들이 감지되었고, 아래 곡들이 추천되었습니다.

감지된 분위기/장소 태그: {tags}
추천된 곡 목록: {songs}

이 공간에 왜 이 음악들이 어울리는지 2문장으로 자연스럽게 설명해주세요.
공간의 분위기와 음악의 감성을 연결해서 설명해주세요.
""")

chain = prompt | llm | StrOutputParser()

def explain_recommendation(tags: list, songs: dict) -> str:
    # 1. tags가 만약 문자열로 들어온다면 리스트로 변환 (방어적 코드)
    if isinstance(tags, str):
        tags_str = tags
    else:
        tags_str = ", ".join(tags)

    # 2. songs가 문자열(JSON 형태)로 들어올 경우 딕셔너리로 변환
    if isinstance(songs, str):
        try:
            songs = json.loads(songs)
        except json.JSONDecodeError:
            # 만약 JSON 형식이 아닌 일반 문자열이라면 그대로 사용
            songs_str = songs
            return chain.invoke({"tags": tags_str, "songs": songs_str})

    # 3. 정상적인 딕셔너리 처리
    songs_str = ", ".join([f"{title}({artist})" for title, artist in songs.items()])
    return chain.invoke({"tags": tags_str, "songs": songs_str})