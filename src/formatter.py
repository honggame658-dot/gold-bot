"""
📝 Message Formatter Module
Formats news articles into beautiful Telegram messages
"""

from datetime import datetime, timezone


def format_news_message(articles, price_summary=''):
    """
    Format multiple articles into a single Telegram message
    Uses HTML formatting for Telegram
    """
    if not articles:
        return None
    
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d %H:%M UTC')
    
    # Header
    lines = []
    lines.append('📰 <b>Gold &amp; BTC News Alert</b> 🚨')
    lines.append(f'📅 <i>{date_str}</i>')
    lines.append('')
    
    # Price section
    if price_summary:
        lines.append('━━━━━━━━━━━━━━━━━━━━')
        lines.append('💰 <b>តម្លៃបច្ចុប្បន្ន / Current Prices</b>')
        lines.append('')
        lines.append(price_summary)
        lines.append('')
    
    lines.append('━━━━━━━━━━━━━━━━━━━━')
    lines.append('')
    
    # Articles
    for i, article in enumerate(articles[:5], 1):  # Max 5 articles per message
        category = article.get('category', '📰')
        title = escape_html(article.get('title', 'No title'))
        source = article.get('source', 'Unknown')
        link = article.get('link', '')
        description = article.get('description', '')
        pub_date = article.get('pub_date', now)
        
        if isinstance(pub_date, datetime):
            pub_date_str = pub_date.strftime('%Y-%m-%d %H:%M')
        else:
            pub_date_str = str(pub_date)
        
        lines.append(f'{category} <b>{title}</b>')
        lines.append(f'📅 {pub_date_str} │ 🌐 {escape_html(source)}')
        
        if description:
            desc_short = description[:150]
            if len(description) > 150:
                desc_short += '...'
            lines.append(f'<i>{escape_html(desc_short)}</i>')
        
        # Add AI analysis if present
        ai_data = article.get('ai_analysis')
        if ai_data and isinstance(ai_data, dict):
            lines.append('')
            impact_emoji = '🔥' if ai_data['impact'] == 'High' else '⚡' if ai_data['impact'] == 'Medium' else '❄️'
            lines.append(f"🤖 <b>ការវិភាគពី AI:</b>")
            lines.append(f"កម្រិតឥទ្ធិពល: {impact_emoji} {ai_data['impact']} Impact")
            lines.append(f"សញ្ញាទីផ្សារ: <b>{ai_data.get('signal', '🟡 HOLD (រង់ចាំ)')}</b>")
            lines.append(f"{ai_data.get('analysis', '')}")
        elif isinstance(ai_data, str):
            lines.append('')
            lines.append(f'🤖 <b>ការវិភាគពី AI:</b>\n{ai_data}')
        
        if link:
            lines.append('')
            lines.append(f'🔗 <a href="{link}">អានបន្ថែម / Read more</a>')
        
        lines.append('')
        
        if i < len(articles[:5]):
            lines.append('─ ─ ─ ─ ─ ─ ─ ─ ─ ─')
            lines.append('')
    
    # Footer
    lines.append('━━━━━━━━━━━━━━━━━━━━')
    lines.append('#Gold #XAUUSD #Forex #Trading')
    lines.append('🤖 <i>Gold&amp;New Bot - Auto News</i>')
    
    return '\n'.join(lines)


def format_single_article(article, price_summary=''):
    """Format a single article as a Telegram message"""
    return format_news_message([article], price_summary)


def format_price_alert(price_summary):
    """Format a price-only update"""
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d %H:%M UTC')
    
    lines = [
        '💰 <b>Price Update</b> 📊',
        f'📅 <i>{date_str}</i>',
        '',
        '━━━━━━━━━━━━━━━━━━━━',
        '',
        price_summary,
        '',
        '━━━━━━━━━━━━━━━━━━━━',
        '#Gold #XAUUSD #Price',
        '🤖 <i>Gold&amp;New Bot</i>'
    ]
    
    return '\n'.join(lines)


def format_startup_message():
    """Format bot startup notification"""
    now = datetime.now(timezone.utc)
    
    return (
        '🟢 <b>Gold&amp;New Bot Started!</b>\n'
        f'📅 {now.strftime("%Y-%m-%d %H:%M UTC")}\n'
        '\n'
        '✅ Bot is now monitoring news about:\n'
        '  🥇 Gold (XAU/USD)\n'
        '\n'
        '📡 News will be fetched automatically\n'
        '🤖 <i>Gold&amp;New Bot - Auto News</i>'
    )


def escape_html(text):
    """Escape HTML special characters for Telegram"""
    if not text:
        return ''
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


if __name__ == '__main__':
    # Test formatting
    test_articles = [
        {
            'title': 'Gold prices surge to new record high',
            'description': 'Gold prices hit a new all-time high amid global economic uncertainty.',
            'source': 'Reuters',
            'link': 'https://example.com/gold-news',
            'category': '🥇',
            'pub_date': datetime.now(timezone.utc),
        },
        {
            'title': 'Bitcoin drops below $67,000',
            'description': 'Bitcoin fell 1.2% in the last 24 hours as markets react.',
            'source': 'CoinDesk',
            'link': 'https://example.com/btc-news',
            'category': '₿',
            'pub_date': datetime.now(timezone.utc),
        }
    ]
    
    msg = format_news_message(test_articles, '🥇 Gold: $2,450.30\n₿ BTC: $67,250.00')
    print(msg)
