"""
💾 Simple JSON Database Module
Tracks sent articles to avoid duplicates
"""

import json
import os
from datetime import datetime, timezone


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sent_articles.json')


def _ensure_db():
    """Ensure database file and directory exist"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({'sent': [], 'last_fetch': None, 'stats': {'total_sent': 0}, 'users': {}}, f)


def load_db():
    """Load database from JSON file"""
    _ensure_db()
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {'sent': [], 'last_fetch': None, 'stats': {'total_sent': 0}, 'users': {}}


def save_db(db):
    """Save database to JSON file"""
    _ensure_db()
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2, default=str)


def is_article_sent(title):
    """Check if article was already sent"""
    db = load_db()
    import re
    title_key = re.sub(r'[^a-zA-Z0-9]', '', title.lower())[:50]
    return title_key in [item.get('key', '') for item in db['sent']]


def mark_article_sent(title, link=''):
    """Mark article as sent"""
    import re
    db = load_db()
    title_key = re.sub(r'[^a-zA-Z0-9]', '', title.lower())[:50]
    
    db['sent'].append({
        'key': title_key,
        'title': title[:100],
        'link': link,
        'sent_at': datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 500 entries to prevent file from growing too large
    if len(db['sent']) > 500:
        db['sent'] = db['sent'][-500:]
    
    db['stats']['total_sent'] = db['stats'].get('total_sent', 0) + 1
    db['last_fetch'] = datetime.now(timezone.utc).isoformat()
    
    save_db(db)


def get_unsent_articles(articles):
    """Filter out already sent articles"""
    unsent = []
    for article in articles:
        if not is_article_sent(article['title']):
            unsent.append(article)
    return unsent


def get_stats():
    """Get sending statistics"""
    db = load_db()
    return {
        'total_sent': db['stats'].get('total_sent', 0),
        'last_fetch': db.get('last_fetch', 'Never'),
        'tracked_articles': len(db['sent'])
    }


# ==========================================
# VIP MANAGEMENT
# ==========================================

def add_vip(user_id, username, days):
    """Add or extend VIP for a user"""
    from datetime import timedelta
    db = load_db()
    if 'users' not in db:
        db['users'] = {}
        
    user_id_str = str(user_id)
    now = datetime.now(timezone.utc)
    
    if user_id_str in db['users'] and 'expire_at' in db['users'][user_id_str]:
        # Extend
        current_expire = datetime.fromisoformat(db['users'][user_id_str]['expire_at'])
        if current_expire > now:
            new_expire = current_expire + timedelta(days=days)
        else:
            new_expire = now + timedelta(days=days)
    else:
        # New
        new_expire = now + timedelta(days=days)
        
    db['users'][user_id_str] = {
        'username': username,
        'expire_at': new_expire.isoformat(),
        'is_vip': True
    }
    save_db(db)
    return new_expire

def remove_vip(user_id):
    """Remove VIP from a user"""
    db = load_db()
    if 'users' not in db: return False
    user_id_str = str(user_id)
    if user_id_str in db['users']:
        db['users'][user_id_str]['is_vip'] = False
        db['users'][user_id_str]['expire_at'] = datetime.now(timezone.utc).isoformat()
        save_db(db)
        return True
    return False

def is_vip(user_id):
    """Check if user is VIP"""
    db = load_db()
    if 'users' not in db: return False
    user_id_str = str(user_id)
    if user_id_str in db['users']:
        user_data = db['users'][user_id_str]
        if user_data.get('is_vip', False):
            expire_at = datetime.fromisoformat(user_data['expire_at'])
            if expire_at > datetime.now(timezone.utc):
                return True
            else:
                # Expired
                user_data['is_vip'] = False
                save_db(db)
                return False
    return False

def get_all_vips():
    db = load_db()
    return {k: v for k, v in db.get('users', {}).items() if v.get('is_vip', False)}

if __name__ == '__main__':
    print('Testing database...')
    _ensure_db()
    stats = get_stats()
    print(f'Total sent: {stats["total_sent"]}')
    print(f'Last fetch: {stats["last_fetch"]}')
    print(f'Tracked: {stats["tracked_articles"]}')
