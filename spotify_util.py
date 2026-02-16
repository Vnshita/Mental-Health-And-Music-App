import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st

client_id = '53c53c585ff84af498b3bc953b51c42a'
client_secret = '136301e37d824cd699473544196a4702'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

def get_spotify_client():
    client_id = st.secrets["spotify"]["client_id"]
    client_secret = st.secrets["spotify"]["client_secret"]
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

def suggest_spotify_tracks(emotion: str):
    """Return top Spotify songs & playlists for a given emotion."""
    sp = get_spotify_client()
    mood_query = emotion.lower()

    # --- Fetch tracks ---
    track_results = sp.search(q=mood_query, type="track", limit=5)
    tracks = []
    for item in track_results["tracks"]["items"]:
        tracks.append({
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "url": item["external_urls"]["spotify"]
        })

    # --- Fetch playlists ---
    playlist_results = sp.search(q=mood_query, type="playlist", limit=5)
    playlists = []
    for item in playlist_results["playlists"]["items"]:
        playlists.append({
            "name": item["name"],
            "url": item["external_urls"]["spotify"]
        })

    return tracks, playlists