from datetime import datetime

import requests

from flask import Flask, request, redirect, jsonify, session
import urllib.parse

from numpy.random import random
from werkzeug.utils import redirect
import random

app = Flask(__name__)
app.secret_key = 'Place_Holder' # Can be set to anything

# Both from Spoitfy dev app
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "To use the shuffler: <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-modify-playback-state playlist-read-private'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show-dialog': True ##Remove this to make you stop logging in each time
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return  jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_in'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/playlists')

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return  redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }


    randomList = []
    playlistID = '55H3wrtWcniGcDfoglCLIH' # Enter Playlist ID here!
    playlistSize = (requests.get(API_BASE_URL + 'playlists/' + playlistID + '/tracks?limit=1&offset=0',
                                headers=headers)).json()["total"]

    # List of all numbers from 0 to size of the playlist
    for i in range(0,playlistSize):
        randomList.append(i)

    random.shuffle(randomList)
    for i in range(0,playlistSize):
        response = requests.get(API_BASE_URL + 'playlists/' + playlistID + '/tracks?limit=1&offset=' + str(randomList[i]),
                                headers=headers)
        playlists = response.json()
        requests.post(API_BASE_URL + 'me/player/queue?uri=' + playlists["items"][0]["track"]["uri"], headers=headers)

    return jsonify(playlists)

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_in'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)