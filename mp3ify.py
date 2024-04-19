import os
from multiprocessing import Pool, Manager
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple
from dotenv import load_dotenv

from spotipy import Spotify
import yt_dlp as youtube_dl # Easy to switch to yt_dlp if youtube_dl is not working
# import youtube_dl

import utils


def get_info_single_track(item: dict) -> dict:
    """
    Extracts information from a dictionary representing a single track and returns a dictionary with the extracted information.

    Args:
        item (dict): A dictionary representing a single track.

    Returns:
        dict: A dictionary containing the extracted information from the track. The dictionary has the following keys:
            - 'artists': A list of strings representing the names of the artists.
            - 'song_name': A string representing the name of the song.
            - 'duration_ms': A float representing the duration of the song in seconds.
            - 'search_query': A string representing a search query for the song.
            - 'full_title': A string representing the full title of the song in the format 'artist1, artist2 - song_name'.
    """
    track = item['track']
    artists, song_name = utils.process_spotify_song_name([artist['name'] for artist in track['artists']], track['name'])
    duration_ms = track['duration_ms']
    search_query = f'{" ".join(artists)} - {song_name} autogenerated'
    full_title = f'{", ".join(artists)} - {song_name}'

    return {'artists': artists,
            'song_name': song_name, 
            'duration_ms': duration_ms / 1000,
            'search_query': search_query,
            'full_title': full_title
            }


def get_info_tracks(liked_songs: dict) -> list:
    """
    Retrieves information for each track in the given list of liked songs.

    Args:
        liked_songs (dict): A dictionary containing information about the liked songs.

    Returns:
        list: A list of track information.
    """
    tracks = []
    for track in liked_songs['items']:
        info = get_info_single_track(track)
        tracks.append(info)
    return tracks


def search_single_track(result, track_info, 
                        duration_tolerance, 
                        title_similarity_threshold, 
                        artist_similarity_threshold
                        ) -> Tuple[str, float, float]:
    """
    Searches for a single track based on the given result and track_info.

    Args:
        result (dict): The result containing track information.
        track_info (dict): The information of the track to search for.
        duration_tolerance (int): The maximum allowed difference in duration between the result and track_info.
        title_similarity_threshold (float): The minimum required similarity ratio between the result's title and track_info's song_name.
        artist_similarity_threshold (float): The minimum required similarity ratio between the result's artist and track_info's artists.

    Returns:
        tuple: A tuple containing the URL of the track, the similarity ratio of the title and the similarity ratio of the artist
    """
    duration_diff = abs(result['duration'] - track_info['duration_ms'])

    if duration_diff > duration_tolerance:
        return None, 0, 0

    artist = result.get('artist', None)
    if artist is None:
        artist, title = utils.process_yt_title(result['title'])
    else: 
        title = result['title']
    
    title_similarity = utils.similarity_ratio(title, track_info['song_name'])
    artist_similarity = utils.similarity_ratio(", ".join(artist), ", ".join(track_info['artists']))

    if title_similarity < title_similarity_threshold or artist_similarity < artist_similarity_threshold:
        return None, title_similarity, artist_similarity

    url = result['webpage_url']
    return url, title_similarity, artist_similarity


def search_youtube_single_track(track_info: dict,
                                max_results: int = 5,
                                duration_tolerance: int = 10,
                                title_similarity_threshold: float = 0.7,
                                artist_similarity_threshold: float = 0.05
                                ) -> Tuple[str, str]:
    """
    Search for a single track on YouTube based on the provided track information.

    Args:
        track_info (dict): A dictionary containing information about the track.
            It should have the following keys:
            - 'search_query' (str): The search query for the track.
            - 'duration_ms' (int): The duration of the track in milliseconds.
            - 'song_name' (str): The name of the song.
            - 'artists' (list): A list of artists associated with the track.

        max_results (int, optional): The maximum number of search results to consider. Defaults to 5.
        duration_tolerance (int, optional): The tolerance for the difference in duration between the track and the search results. Defaults to 10.
        title_similarity_threshold (float, optional): The threshold for the similarity ratio between the track title and the search results. Defaults to 0.8.
        artist_similarity_threshold (float, optional): The threshold for the similarity ratio between the track artist and the search results. Defaults to 0.4.

    Returns:
        tuple: A tuple containing the YouTube URL of the best match and the full title of the track.

    Raises:
        RuntimeError: If there is an error searching YouTube.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f'ytsearch{max_results}:{track_info["search_query"]}', download=False)
        except Exception as e:
            raise RuntimeError(f"Error searching YouTube: {e}")

        matches = []
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(search_single_track, result, track_info, duration_tolerance, title_similarity_threshold, artist_similarity_threshold) for result in search_results['entries']]
            for future in as_completed(futures):
                match = future.result()
                if match[0]:
                    matches.append(match)

        full_title = track_info['full_title']
        if not matches:
            return None, full_title

        yt_url, _, _ = max(matches, key=lambda x: x[1] + x[2])
        print(f"Found: {full_title} at {yt_url}")
        return yt_url, full_title
    

def download_track(track: dict, failed_tracks: list) -> None:
    """
    Downloads a track from YouTube using the provided track information.

    Args:
        track (dict): A dictionary containing information about the track.
        failed_tracks (list): A concurrent list to store the titles of tracks that failed to download.
    
    Returns:
        None
    """
    url, title = search_youtube_single_track(track)
    
    if url is None:
        failed_tracks.append(title)
        return
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320'
        }],
        'outtmpl': os.path.join(utils.format_download_dir(), title.replace(":", ""))
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            print(f"Error downloading {title}: {e}")
            failed_tracks.append(title)


if __name__ == '__main__':
    load_dotenv()
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    sp = Spotify(auth_manager=utils.authenticate(client_id, client_secret))
    liked_songs = sp.current_user_saved_tracks()
    print(f"Detected {liked_songs['total']} liked songs from Spotify.")
    
    tracks = get_info_tracks(liked_songs)

    manager = Manager()
    failed_tracks = manager.list()

    with Pool() as pool:
        pool.starmap(download_track, [(track, failed_tracks) for track in tracks])

    if failed_tracks:
        print("The following tracks failed to download:")
        for track in failed_tracks:
            print(f">>> {track}")
