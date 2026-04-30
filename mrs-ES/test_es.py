from recommend_playlist_songs_es import SimilaritySearch

ss = SimilaritySearch()
ss.build_index()

dummy_tags = [0] * 29
dummy_tags[3] = 1
dummy_tags[14] = 1

results = ss.search_similar_playlists(dummy_tags, k=3)
print("검색 결과:", results)