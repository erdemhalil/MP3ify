import os
from datetime import date
import difflib

from spotipy.oauth2 import SpotifyOAuth

def similarity_ratio(s1: str, s2: str) -> float:
    """
    Calculates the similarity ratio between two strings.

    Parameters:
    s1 (str): The first string.
    s2 (str): The second string.

    Returns:
    float: The similarity ratio between the two strings.
    """
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def format_download_dir() -> str:
    """
    Formats the download directory path based on the current user and date.

    Returns:
        str: The formatted download directory path.
    """
    home = os.path.expanduser("~")
    today = date.today().strftime("%d-%m")
    return os.path.join(home, "Downloads", f"mp3ify_{today}")

def authenticate(client_id: str, client_secret: str, redirect_uri: str = 'http://localhost:6060') -> SpotifyOAuth:
    """
    Authenticates the client with the Spotify API using the provided client ID, client secret, and redirect URI.

    Parameters:
    - client_id (str): The client ID obtained from the Spotify Developer Dashboard.
    - client_secret (str): The client secret obtained from the Spotify Developer Dashboard.
    - redirect_uri (str): The URI to redirect the user after authentication. Defaults to 'http://localhost:6060'.

    Returns:
        SpotifyOAuth: An instance of the SpotifyOAuth class for further API interactions.
    """
    return SpotifyOAuth(client_id=client_id, client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope='user-library-read'
                        )

def process_spotify_song_name(song_artists: list, song_title: str):
    """
    Process the Spotify song name by extracting featured artists and updating the song artists list.

    Args:
        song_artists (list): List of artists associated with the song.
        song_title (str): Title of the song.

    Returns:
        tuple: A tuple containing the updated song artists list and the processed song title.
    """
    artists = []
    feat_strings = [" feat.", " ft.", "(feat.", "(ft."]

    for feat_string in feat_strings:
        if feat_string in song_title:
            title, featured_artists = song_title.split(feat_string)
            featured_artists = [artist.replace(")", "").strip() for artist in featured_artists.split(", " if ", " in featured_artists else "& ")]
            artists.extend(featured_artists)

    if not artists:
        title = song_title

    for artist in artists:
        if artist not in song_artists:
            song_artists.append(artist)
    
    return song_artists, title.strip()

def process_yt_title(yt_title: str):
    """
    Process the YouTube video title by extracting featured artists and the song title.

    Args:
        yt_title (str): Title of the YouTube video.

    Returns:
        tuple: A tuple containing the extracted artists and the processed song title.
    """
    left_artists, right_artists = [], []
    title = None
    left_side, right_side = yt_title.split(" - ", maxsplit=1)

    feat_strings = [" feat.", " ft.", "(feat.", "(ft."]
    for feat_string in feat_strings:
        if feat_string in left_side:
            main_artist, featured_artists = left_side.split(feat_string)
            featured_artists = [artist.replace(")", "").strip() for artist in featured_artists.split(", " if ", " in featured_artists else "& ")]
            left_artists.extend([main_artist.strip()] + featured_artists)

        if feat_string in right_side:
            title, featured_artists = right_side.split(feat_string)
            featured_artists = [artist.replace(")", "").strip() for artist in featured_artists.split(", " if ", " in featured_artists else "& ")]
            right_artists.extend(featured_artists)

    if not left_artists:
        left_artists.append(left_side.strip())

    if not title:
        title = right_side.strip()

    artists = left_artists + right_artists

    return artists, title
