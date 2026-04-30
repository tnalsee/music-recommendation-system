import pandas as pd
import ast

class RecommendSongs:
    def __init__(self, song_table_path):
        self.song_table_path = song_table_path
        self.song_df = None

    def load_songs(self):     
        self.song_df = pd.read_csv(self.song_table_path, encoding='utf-8')

    def get_top_songs(self, playlist_songs_ids_str, top_n=5):
        # 문자열 리스트를 Python 리스트로 변환
        playlist_songs_ids = ast.literal_eval(playlist_songs_ids_str)

        # DataFrame 내 SONG_ID 열을 문자열로 변환 (비교를 위해)
        self.song_df['SONG_ID'] = self.song_df['SONG_ID'].astype(str)

        # 변환된 리스트 내의 SONG_ID 중 존재하지 않는 ID를 필터링
        valid_song_ids = [str(id) for id in playlist_songs_ids if str(id) in self.song_df['SONG_ID'].values]

        # 존재하는 SONG_ID와 일치하는 행을 찾고, 중복된 SONG_ID 제거
        playlist_songs = self.song_df[self.song_df['SONG_ID'].isin(valid_song_ids)].drop_duplicates(subset=['SONG_ID']).copy()

        # 곡의 인기도를 계산합니다.
        playlist_songs['popularity'] = (
                                        playlist_songs['LISTENER_CNT'] +
                                        playlist_songs['PLAY_CNT'] +
                                        playlist_songs['SONG_LIKE']
                                        )

        # 인기도에 따라 곡을 정렬하고 상위 n곡을 반환합니다.
        top_songs = playlist_songs.sort_values(by='popularity', ascending=False).head(top_n)

        return top_songs[['SONG_ID', 'SONG_TITLE', 'ARTIST_NAME', 'popularity']]