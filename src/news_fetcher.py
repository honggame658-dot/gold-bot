"""
📰 News Fetcher Module
Fetches Gold & BTC news from multiple free sources (RSS feeds, free APIs)
"""

import urllib.request
import json
import xml.etree.ElementTree as ET
import html
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote


# Keywords for filtering news
GOLD_KEYWORDS = [
    'gold price', 'gold market', 'gold trading', 'gold rises', 'gold falls',
    'gold surges', 'gold drops', 'XAU', 'gold forecast', 'gold analysis',
    'precious metals', 'gold futures', 'gold spot', 'gold rally',
    'gold demand', 'gold supply', 'bullion', 'gold reserve',
    'មាស', 'តម្លៃមាស', 'ទីផ្សារមាស'
]

BTC_KEYWORDS = [
    'bitcoin', 'BTC', 'crypto', 'cryptocurrency', 'btc price',
    'bitcoin price', 'bitcoin market', 'bitcoin trading',
    'bitcoin rises', 'bitcoin falls', 'bitcoin surges', 'bitcoin drops',
    'bitcoin forecast', 'bitcoin analysis', 'bitcoin rally',
    'crypto market', 'digital currency', 'blockchain',
    'ប៊ីតខញ', 'គ្រីបតូ'
]

WAR_KEYWORDS = [
    'war', 'conflict', 'strike', 'missile', 'attack', 'tension',
    'geopolitical', 'middle east', 'russia', 'ukraine', 'israel',
    'iran', 'military', 'invasion', 'saber-rattling', 'drone',
    'សង្គ្រាម', 'ជម្លោះ', 'វាយប្រហារ', 'មីស៊ីល', 'យោធា',
    'អ៊ីស្រាអែល', 'អ៊ីរ៉ង់', 'រុស្ស៊ី', 'អ៊ុយក្រែន'
]

ALL_KEYWORDS = GOLD_KEYWORDS + BTC_KEYWORDS + WAR_KEYWORDS

# RSS Feed Sources
RSS_SOURCES = [
    {
        'name': 'Kitco Gold News',
        'url': 'https://www.kitco.com/news/rss',
        'category': 'gold'
    },
    {
        'name': 'FXStreet',
        'url': 'https://www.fxstreet.com/rss',
        'category': 'gold'
    },
    {
        'name': 'Investing.com Commodities',
        'url': 'https://www.investing.com/rss/news_25.rss',
        'category': 'gold'
    },
    {
        'name': 'Forex Factory News',
        'url': 'https://www.forexfactory.com/news.xml',
        'category': 'gold'
    },
    {
        'name': 'Google News - Gold',
        'url': 'https://news.google.com/rss/search?q=gold+price+market&hl=en-US&gl=US&ceid=US:en',
        'category': 'gold'
    },
    {
        'name': 'Al Jazeera - Middle East',
        'url': 'https://www.aljazeera.com/xml/rss/all.xml',
        'category': 'war'
    },
    {
        'name': 'Google News - World Conflict',
        'url': 'https://news.google.com/rss/search?q=war+OR+conflict+OR+strike+OR+geopolitical&hl=en-US&gl=US&ceid=US:en',
        'category': 'war'
    },
]


def clean_html(raw_html):
    """Remove HTML tags from string"""
    if not raw_html:
        return ''
    clean = re.sub(r'<[^>]+>', '', raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:300]  # Limit length


def parse_rss_date(date_str):
    """Parse various RSS date formats and ensure it is timezone-aware"""
    if not date_str:
        return datetime.now(timezone.utc)
    
    formats = [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    return datetime.now(timezone.utc)


def is_relevant(title, description=''):
    """Check if article is relevant to Gold or BTC"""
    text = f"{title} {description}".lower()
    
    for keyword in ALL_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


def get_category(title, description=''):
    """Determine if article is about Gold, BTC, or both"""
    text = f"{title} {description}".lower()
    
    is_gold = any(kw.lower() in text for kw in GOLD_KEYWORDS)
    is_btc = any(kw.lower() in text for kw in BTC_KEYWORDS)
    is_war = any(kw.lower() in text for kw in WAR_KEYWORDS)
    
    if is_gold and is_btc:
        return '🥇₿'
    elif is_gold:
        return '🥇'
    elif is_btc:
        return '₿'
    elif is_war:
        return '🌍'
    return '📰'


def fetch_rss(url, source_name, category):
    """Fetch and parse RSS feed"""
    articles = []
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='replace')
        
        root = ET.fromstring(content)
        
        # Handle both RSS 2.0 and Atom feeds
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'media': 'http://search.yahoo.com/mrss/'
        }
        
        # RSS 2.0 format
        items = root.findall('.//item')
        
        # Atom format fallback
        if not items:
            items = root.findall('.//atom:entry', namespaces)
        
        for item in items[:15]:  # Limit to 15 per source
            title = ''
            link = ''
            description = ''
            pub_date = ''
            
            # Try RSS 2.0 tags
            title_el = item.find('title')
            if title_el is not None and title_el.text:
                title = clean_html(title_el.text)
            
            link_el = item.find('link')
            if link_el is not None:
                link = link_el.text or link_el.get('href', '')
            
            desc_el = item.find('description')
            if desc_el is not None and desc_el.text:
                description = clean_html(desc_el.text)
            
            date_el = item.find('pubDate')
            if date_el is not None and date_el.text:
                pub_date = date_el.text
            else:
                # Try Atom date
                date_el = item.find('atom:updated', namespaces) or item.find('atom:published', namespaces)
                if date_el is not None and date_el.text:
                    pub_date = date_el.text
            
            if title and is_relevant(title, description):
                articles.append({
                    'title': title,
                    'link': link.strip() if link else '',
                    'description': description,
                    'source': source_name,
                    'category': get_category(title, description),
                    'pub_date': parse_rss_date(pub_date),
                    'fetched_at': datetime.now(timezone.utc)
                })
    
    except Exception as e:
        print(f'  ⚠️  Error fetching {source_name}: {e}')
    
    return articles


def fetch_all_news():
    """Fetch news from all sources"""
    all_articles = []
    
    print(f'📡 Fetching news from {len(RSS_SOURCES)} sources...')
    
    for source in RSS_SOURCES:
        articles = fetch_rss(source['url'], source['name'], source['category'])
        all_articles.extend(articles)
        print(f'  ✅ {source["name"]}: {len(articles)} articles')
        time.sleep(0.5)  # Be polite to servers
    
    # Sort by publication date (newest first)
    all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # Remove duplicates based on title similarity
    seen_titles = set()
    unique_articles = []
    
    for article in all_articles:
        # Create a simple hash of the title for dedup
        title_key = re.sub(r'[^a-zA-Z0-9]', '', article['title'].lower())[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    print(f'\n📊 Total unique articles: {len(unique_articles)}')
    return unique_articles


if __name__ == '__main__':
    print('Testing news fetcher...\n')
    articles = fetch_all_news()
    
    for i, article in enumerate(articles[:5], 1):
        print(f'\n--- Article {i} ---')
        print(f'  {article["category"]} {article["title"]}')
        print(f'  📅 {article["pub_date"]}')
        print(f'  🌐 {article["source"]}')
        print(f'  🔗 {article["link"][:80]}...' if article["link"] else '')
