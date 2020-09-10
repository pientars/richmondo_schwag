import csv
import pandas as pd
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

SLEEP_BETWEEN_TRACKS = 3


def add_tracks_to_playlist(track_ids_list, playlist_id, spu):
    results = spu.playlist_add_items(playlist_id, track_ids_list, position=None)
    print(results)


def create_playlist(user_id, pl_name, desc, sp):
    playlist_deets = sp.user_playlist_create(user=user_id, name=pl_name, public=False, collaborative=False, description=desc)
    print(playlist_deets)
    return playlist_deets


def import_anthology(anthology_file):
    anth_df = pd.read_csv(anthology_file, delimiter='\t')
    anth_df = anth_df.dropna(subset=['Artist', 'Track'])
    anth_df = anth_df[~(anth_df['Not on Spotify?'] == 'X')]
    print('Loaded {:d} tracks.'.format(anth_df.shape[0]))
    print(anth_df)
    return anth_df


def get_party_subset(anth_df):
    party_df = anth_df[anth_df['Party?'] == 'X']
    print('Filtered down to {:d} party tracks.'.format(party_df.shape[0]))
    return party_df


def search_for_track(artist, track, sp):
    print('Searching for: {:s} - {:s}'.format(artist, track))
    results = sp.search(q='artist:{:s} track:{:s}'.format(artist, track), type='track')
    for res in results['tracks']['items']:
        print('  Artist: {:s} - Track: {:s} - Id: {:s}'.format(res['artists'][0]['name'], res['name'], res['id']))
    if len(results['tracks']['items']) == 0:
        return -1
    first_hit = results['tracks']['items'][0]
    return first_hit


def setup_spotify():
    auth_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def setup_spotify_user():
    scope = 'playlist-modify-private'
    spu = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    return spu


if __name__ == '__main__':
    # Load the richmond anthology data
    anthology_file = 'data/traom.tsv'
    anth_df = import_anthology(anthology_file)
    party_df = get_party_subset(anth_df)

    # Create a client (user-free) instance for searching the api
    sp = setup_spotify()

    # Find track id's for party segment
    track_ids_list = []
    i = 0
    for index, row in party_df.iterrows():
        print('{:d}th track, {:.2f}%'.format(i, 100.0 * i / len(party_df)))
        time.sleep(SLEEP_BETWEEN_TRACKS)
        artist = row['Artist']
        track = row['Track']
        # Get a track
        track = search_for_track(artist, track, sp)
        if track == -1:
            with open('missing_artists.csv', 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow([artist, track])
            continue
        track_ids_list.append(track['id'])
        i += 1
        if i > 10:
            break

    # Create a user-specific spotify instance for editing user X's playlist
    sp_user = setup_spotify_user()

    # Create a playlist
    # TODO programmatically get my userid
    playlist = create_playlist(1211481780,
                               'The Richmond Anthology of Music: Party',
                               'The Richmond Anthology of Music, but just the party tracks!',
                               sp_user)
    pl_id = playlist['id']
    add_tracks_to_playlist(track_ids_list, pl_id, sp_user)


