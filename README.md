# richmondo_schwag
Gonna port interesting slices of Richmond Anthology to spotify. 

Clone this repo
```
cd richmondo_schwag
python3 -m venv envo
source envo/bin/activate
pip3 install -r requirements.txt
export SPOTIPY_CLIENT_ID='<HAHA ID HERE>'
export SPOTIPY_CLIENT_SECRET='<COOL SECRET KEY HERE>'
# Or use a file to do the above
# . my_jazz.sh #a file that exports your
python load_party_tracks.py
```