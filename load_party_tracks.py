import csv
import os
import pandas as pd
import pickle
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

SLEEP_BETWEEN_TRACKS = 2


def add_tracks_to_playlist(track_ids_list, playlist_id, spu):
    results = spu.playlist_add_items(playlist_id, track_ids_list, position=None)
    print(results)


def create_playlist(user_id, pl_name, desc, sp):
    playlist_deets = sp.user_playlist_create(user=user_id, name=pl_name, public=False, collaborative=False, description=desc)
    print(playlist_deets)
    return playlist_deets


def get_artist_track_ids(party_df, sp):
    # Find track id's for party segment
    if os.path.isfile('cached_artist_ids.pkl'):
        cached_artist_ids = pickle.load(open('cached_artist_ids.pkl', 'rb'))
        track_ids_list = [val for val in cached_artist_ids.values()]
        print('Restarted with ids: {}'.format(track_ids_list))
    else:
        cached_artist_ids = {}
        track_ids_list = []
    i = 0
    for index, row in party_df.iterrows():
        print('Track {:d}: {:.2f}%'.format(i, 100.0 * i / len(party_df)))
        i += 1
        time.sleep(SLEEP_BETWEEN_TRACKS)
        artist = row['Artist']
        track = row['Track']
        # Get a track
        track_result = search_for_track(artist, track, sp)
        if track_result == -1:
            with open('missing_artists.csv', 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow([artist, track])
            continue
        cached_artist_ids[artist + track] = track_result['id']
        pickle.dump(cached_artist_ids, open('cached_artist_ids.pkl', 'wb'))
        track_ids_list.append(track_result['id'])

    return track_ids_list


def import_anthology(anthology_file):
    anth_df = pd.read_csv(anthology_file, delimiter='\t')
    anth_df = anth_df.dropna(subset=['Artist', 'Track'])
    anth_df = anth_df[~(anth_df['Not on Spotify?'] == 'X')]
    print('Loaded {:d} tracks from the RAM.'.format(anth_df.shape[0]))
    return anth_df


def get_party_subset(anth_df):
    party_df = anth_df[anth_df['Party?'] == 'X']
    print('Filtered down to {:d} party tracks from the RAM.'.format(party_df.shape[0]))
    return party_df


def search_for_track(artist, track, sp):
    print('Searching for: {:s} - {:s}'.format(artist, track))
    results = sp.search(q='artist:{:s} track:{:s}'.format(artist, track), type='track')
    # for res in results['tracks']['items']:
    if len(results['tracks']['items']) == 0:
        return -1
    res = results['tracks']['items'][0]
    print('  Artist: {:s} - Track: {:s} - Id: {:s}'.format(res['artists'][0]['name'], res['name'], res['id']))
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

    # Get each track id, this may take 30 minutes to avoid rate limiting.
    track_ids_list = get_artist_track_ids(party_df, sp)

    # Create a user-specific spotify instance for editing user X's playlist
    sp_user = setup_spotify_user()

    # Create a playlist
    # TODO programmatically get my userid
    playlist = create_playlist(1211481780,
                               'The Richmond Anthology of Music: Party',
                               'The Richmond Anthology of Music, but just the party tracks! All thanks goes to the RAM!',
                               sp_user)
    pl_id = playlist['id']
    add_tracks_to_playlist(track_ids_list, pl_id, sp_user)


