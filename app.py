from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

oauth = OAuth(app)
discord = oauth.register(
    name='discord',
    client_id=os.getenv('DISCORD_CLIENT_ID'),
    client_secret=os.getenv('DISCORD_CLIENT_SECRET'),
    access_token_url='https://discord.com/api/oauth2/token',
    access_token_params=None,
    authorize_url='https://discord.com/api/oauth2/authorize',
    authorize_params=None,
    api_base_url='https://discord.com/api/v10/',
    client_kwargs={'scope': 'identify'},
)

@app.route('/')
def index():
    if 'user_token' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user_token = request.form.get('user_token', '').strip()
    
    if not user_token:
        return render_template('index.html', error='User token is required'), 400
    
    # Verify user token by fetching current user
    headers = {'Authorization': user_token}
    resp = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
    
    if resp.status_code != 200:
        return render_template('index.html', error='Invalid user token'), 401
    
    user_data = resp.json()
    session['user_token'] = user_token
    session['user'] = user_data
    
    return redirect(url_for('dashboard'))

@app.route('/login-oauth')
def login_oauth():
    redirect_uri = url_for('callback', _external=True)
    return discord.authorize_redirect(redirect_uri)

@app.route('/callback')
def callback():
    token = discord.authorize_access_token()
    session['token'] = token
    
    resp = discord.get('users/@me')
    user_data = resp.json()
    session['user'] = user_data
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_token' not in session:
        return redirect(url_for('index'))

    user_token = session.get('user_token')
    headers = {'Authorization': user_token}

    # Fetch user's guilds
    resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers)
    
    if resp.status_code != 200:
        return redirect(url_for('index'))
    
    guilds = resp.json()
    return render_template('dashboard.html', user=session['user'], guilds=guilds)

@app.route('/api/guild/<guild_id>/channels')
def get_guild_channels(guild_id):
    if 'user_token' not in session:
        return {'error': 'Unauthorized'}, 401

    user_token = session.get('user_token')
    headers = {'Authorization': user_token}

    try:
        # Fetch channels for this guild
        resp = requests.get(
            f'https://discord.com/api/v10/guilds/{guild_id}/channels',
            headers=headers
        )
        
        if resp.status_code == 200:
            channels = resp.json()
            # Filter only text channels (type 0)
            text_channels = [ch for ch in channels if ch.get('type') == 0]
            return {'channels': text_channels}, 200
        else:
            return {'error': 'Failed to fetch channels'}, resp.status_code
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/send-message', methods=['POST'])
def send_message():
    if 'user_token' not in session:
        return {'error': 'Unauthorized'}, 401

    user_token = session.get('user_token')
    headers = {'Authorization': user_token, 'Content-Type': 'application/json'}
    
    data = request.json
    channels = data.get('channels', [])
    message_content = data.get('message', '').strip()
    
    if not message_content:
        return {'error': 'Message cannot be empty'}, 400
    
    if not channels:
        return {'error': 'No channels selected'}, 400
    
    results = {
        'success': [],
        'failed': []
    }
    
    # Send message to each channel
    for channel in channels:
        channel_id = channel.get('id')
        channel_name = channel.get('name')
        
        try:
            resp = requests.post(
                f'https://discord.com/api/v10/channels/{channel_id}/messages',
                headers=headers,
                json={'content': message_content}
            )
            
            if resp.status_code == 200:
                results['success'].append(channel_name)
            elif resp.status_code == 429:
                # Rate limited - wait and retry
                results['failed'].append(f'{channel_name} (Rate limited)')
            else:
                error_msg = resp.json().get('message', 'Unknown error')
                results['failed'].append(f'{channel_name} ({error_msg})')
        except Exception as e:
            results['failed'].append(f'{channel_name} ({str(e)})')
    
    return results, 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
