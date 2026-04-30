import time
import requests
import base64

from ..settings.spotify_config import *
from .image_to_song import get_recommend_songs


# --- Access Token 관리 ---

_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token(client_id, client_secret):
    encoded = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('ascii')
    headers = {"Authorization": f"Basic {encoded}"}
    payload = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", data=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data['access_token'], data.get('expires_in', 3600)

def get_valid_access_token():
    """캐시된 토큰이 만료되었으면 재발급, 유효하면 재사용."""
    now = time.time()
    # 만료 60초 전에 미리 갱신
    if _token_cache["access_token"] is None or now >= _token_cache["expires_at"] - 60:
        token, expires_in = get_access_token(CLIENT_ID, CLIENT_KEY)
        _token_cache["access_token"] = token
        _token_cache["expires_at"] = now + expires_in
    return _token_cache["access_token"]


# --- Spotify 검색 ---

def search_spotify(query, query_type, access_token):
    params = {"q": query, "type": query_type, "limit": "1"}
    response = requests.get(
        "https://api.spotify.com/v1/search",
        params=params,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    data = response.json().get(f'{query_type}s', {}).get('items', [])
    return data[0] if data else None


# --- 메인 함수 ---

def get_song_urls() -> dict:
    """
    추천 곡 목록을 Spotify에서 검색하여 preview URL과 커버 이미지 URL을 반환합니다.

    Returns:
        {
            "urls": List[str],    # preview URL 목록
            "covers": List[str],  # 앨범 커버 이미지 URL 목록
        }
    """
    access_token = get_valid_access_token()
    recommend_songs = get_recommend_songs()  # {song: artist, ...}

    url_list = []
    cover_list = []

    for song, artist in recommend_songs.items():
        track_query = f"{artist} {song}"
        track_data = search_spotify(track_query, "track", access_token)

        if not track_data:
            print(f"No results found for '{song}' by '{artist}'")
            continue

        preview_url = track_data.get('preview_url')
        if preview_url:
            url_list.append(preview_url)

            # 앨범 커버 이미지 추출 (가장 큰 이미지 사용)
            images = track_data.get('album', {}).get('images', [])
            cover_url = images[0]['url'] if images else None
            cover_list.append(cover_url)
        else:
            print(f"No preview URL available for '{song}' by '{artist}'")

    return {
        "urls": url_list,
        "covers": cover_list,
    }






# import requests
# import base64

# from ..settings.spotify_config import *
# from .image_to_song import get_recommend_songs

# def get_access_token(client_id, client_secret):
#     encoded = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('ascii')
#     headers = {"Authorization": f"Basic {encoded}"}
#     payload = {"grant_type": "client_credentials"}
#     response = requests.post("https://accounts.spotify.com/api/token", data=payload, headers=headers)
#     return response.json()['access_token']

# def search_spotify(query, query_type, access_token):
#     params = {"q": query, "type": query_type, "limit": "1"}
#     response = requests.get("https://api.spotify.com/v1/search", params=params, headers={"Authorization": f"Bearer {access_token}"})
#     data = response.json().get(f'{query_type}s', {}).get('items', [])
#     return data[0]


# access_token = get_access_token(CLIENT_ID, CLIENT_KEY)

# album_info = {
#     "Permission to Dance": "BTS",
#     "Super Shy": "뉴진스",
#     "Don't look back in anger": "Oasis",
#     "모든 날, 모든 순간": "폴킴",
#     "다이너마이트": "BTS"
# }

# def test(di):
#     sample = di
#     print(sample)


# # 여기에 똑같이 딕셔너리를 인자값으로 넣어줍니다.
# def get_song_urls():
#     url_list = []
#     album_info = get_recommend_songs()
#     for song, artist in album_info.items():
#         track_query = f"{artist} {song}"
#         track_data = search_spotify(track_query, "track", access_token)

#         if track_data:
#             # print(f"Track Name: {track_data['name']}")
#             # print(f"Artist Name: {', '.join(artist['name'] for artist in track_data['artists'])}")
            
#             # print(f"Preview URL: {track_data['preview_url']}" if 'preview_url' in track_data else "No preview available")
#             url_list.append(track_data['preview_url'])
#         else:
#             print(f"No results found for '{song}' by '{artist}'")
#     return url_list