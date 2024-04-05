# MP3ify

MP3ify is a Python script that allows you to download your liked songs from Spotify as MP3 files. It uses the Spotify API to retrieve information about your liked songs and then searches for corresponding tracks on YouTube. The script then downloads the audio of multiple songs at a time and saves them as an MP3 file.


### Prerequisites:
- Python 3.8+
- `pip` package manager
- Spotify Developer account


### Installation:
1. Clone the repository or download the source code.
1. Open a terminal and navigate to the project directory.
1. Install the required dependencies by running the following command:
```
pip install -r requirements.txt
```


## Configuration
1. Log in to your Spotify Developer account and [create a new application](https://developer.spotify.com/documentation/web-api/concepts/apps) to obtain the client ID and client secret. 
2. Create a .env file in the project directory and add the following lines:
```
SPOTIFY_CLIENT_ID=<your-client-id>
SPOTIFY_CLIENT_SECRET=<your-client-secret>
```
Replace `<your-client-id>` and `<your-client-secret>` with your actual client ID and client secret.


## Usage
Open a terminal in the project directory and run the following command:
```
python mp3ify.py
```
All songs are downloaded to a folder in your `Downloads` directory.


## Customization
You can customize the behavior of the script by modifying the following parameters in `mp3ify.py`:

- `max_results`: The maximum number of search results to consider when searching on YouTube. Default is 5.
- `duration_tolerance`: The tolerance for the difference in duration between the track and the search results. Default is 10s.
- `title_similarity_threshold`: A similarity ratio [0-1] between the track title and the search results. Default is 0.7.
- `artist_similarity_threshold`: A similarity ratio [0-1] between the track artist and the search results. Default is 0.05.