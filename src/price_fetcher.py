"""
📊 Price Fetcher Module
Fetches Gold (XAU/USD) and Bitcoin (BTC/USD) prices from free APIs
"""

import urllib.request
import json
import time

# Cache to avoid hitting rate limits
_price_cache = {
    'gold': {'price': None, 'change': None, 'timestamp': 0},
    'btc': {'price': None, 'change': None, 'timestamp': 0, 'market_cap': None},
}

CACHE_DURATION = 300  # 5 minutes


def fetch_gold_price():
    """Fetch gold price from free API"""
    cache = _price_cache['gold']
    if cache['price'] and (time.time() - cache['timestamp']) < CACHE_DURATION:
        return cache

    try:
        # Using metals.dev free API
        url = 'https://api.metals.dev/v1/latest?api_key=demo&currency=USD&unit=toz'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'metals' in data and 'gold' in data['metals']:
            price = data['metals']['gold']
            cache.update({
                'price': round(price, 2),
                'change': None,
                'timestamp': time.time()
            })
            return cache
    except Exception:
        pass

    try:
        # Fallback: GoldAPI alternative via frankfurter
        url = 'https://api.frankfurter.app/latest?from=XAU&to=USD'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'rates' in data and 'USD' in data['rates']:
            price = data['rates']['USD']
            cache.update({
                'price': round(price, 2),
                'change': None,
                'timestamp': time.time()
            })
            return cache
    except Exception:
        pass

    try:
        # Fallback 2: Using exchange rate API
        url = 'https://open.er-api.com/v6/latest/XAU'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        if 'rates' in data and 'USD' in data['rates']:
            price = data['rates']['USD']
            cache.update({
                'price': round(price, 2),
                'change': None,
                'timestamp': time.time()
            })
            return cache
    except Exception:
        pass

    return cache


def fetch_btc_price():
    """Fetch BTC price from CoinGecko free API"""
    cache = _price_cache['btc']
    if cache['price'] and (time.time() - cache['timestamp']) < CACHE_DURATION:
        return cache

    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'bitcoin' in data:
            btc = data['bitcoin']
            cache.update({
                'price': btc.get('usd', 0),
                'change': round(btc.get('usd_24h_change', 0), 2),
                'market_cap': btc.get('usd_market_cap', 0),
                'timestamp': time.time()
            })
            return cache
    except Exception:
        pass

    try:
        # Fallback: CoinCap API
        url = 'https://api.coincap.io/v2/assets/bitcoin'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'data' in data:
            btc = data['data']
            cache.update({
                'price': round(float(btc.get('priceUsd', 0)), 2),
                'change': round(float(btc.get('changePercent24Hr', 0)), 2),
                'market_cap': round(float(btc.get('marketCapUsd', 0)), 0),
                'timestamp': time.time()
            })
            return cache
    except Exception:
        pass

    return cache


def format_price(price):
    """Format price with commas"""
    if price is None:
        return 'N/A'
    return f"${price:,.2f}"


def format_change(change):
    """Format price change with emoji"""
    if change is None:
        return ''
    emoji = '📈' if change >= 0 else '📉'
    sign = '+' if change >= 0 else ''
    return f"{emoji} {sign}{change}%"


def get_price_summary():
    """Get formatted price summary for both Gold and BTC"""
    gold = fetch_gold_price()
    btc = fetch_btc_price()
    
    gold_line = f"🥇 Gold (XAU/USD): {format_price(gold['price'])}"
    if gold['change'] is not None:
        gold_line += f" {format_change(gold['change'])}"
    
    btc_line = f"₿ Bitcoin (BTC/USD): {format_price(btc['price'])}"
    if btc['change'] is not None:
        btc_line += f" {format_change(btc['change'])}"
    
    return f"{gold_line}\n{btc_line}"


if __name__ == '__main__':
    print('Testing price fetchers...\n')
    print(get_price_summary())
