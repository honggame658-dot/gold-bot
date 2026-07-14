"""
🔍 Helper script to find your Telegram Channel ID

Steps:
1. Add your bot as ADMIN to the channel
2. Send a message in the channel  
3. Run: python find_channel_id.py
"""

import urllib.request
import json
import os

# Load token from .env
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

if not TOKEN:
    print('❌ TELEGRAM_BOT_TOKEN is not set in .env file')
    exit(1)

print('🔍 Searching for your Channel ID...')
print('📌 Make sure you have:')
print('   1. Added the bot as ADMIN to your channel')
print('   2. Sent at least ONE message in the channel')
print('')

url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    if not data.get('ok'):
        print('❌ API Error:', data.get('description', 'Unknown error'))
        exit(1)
    
    results = data.get('result', [])
    
    if not results:
        print('⚠️  No updates found.')
        print('')
        print('💡 Try these steps:')
        print('   1. Open your Telegram channel "Gold&New"')
        print('   2. Go to Manage → Administrators → Add Administrator')
        print('   3. Search for your bot and add it as admin')
        print('   4. Send a message in the channel')
        print('   5. Run this script again: python find_channel_id.py')
        exit(0)
    
    print('📋 Found updates! Here are your chats:\n')
    
    seen_chats = set()
    
    for update in results:
        chat = None
        
        if 'message' in update:
            chat = update['message'].get('chat')
        elif 'channel_post' in update:
            chat = update['channel_post'].get('chat')
        elif 'my_chat_member' in update:
            chat = update['my_chat_member'].get('chat')
        
        if chat and chat['id'] not in seen_chats:
            seen_chats.add(chat['id'])
            chat_type = chat.get('type', 'unknown')
            title = chat.get('title', chat.get('first_name', 'N/A'))
            username = f"@{chat['username']}" if 'username' in chat else 'No username'
            
            print(f'  ┌─────────────────────────────────')
            print(f'  │ 📛 Name: {title}')
            print(f'  │ 🆔 Chat ID: {chat["id"]}')
            print(f'  │ 📝 Type: {chat_type}')
            print(f'  │ 👤 Username: {username}')
            print(f'  └─────────────────────────────────')
            print('')
    
    if not seen_chats:
        print('⚠️  Updates found but no chat info. Send a message in your channel and try again.')
    else:
        print('✅ Copy the Chat ID of your channel and paste it into .env file as TELEGRAM_CHAT_ID')

except Exception as e:
    print(f'❌ Error: {e}')
