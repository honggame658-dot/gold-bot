import json
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

from src.analyzer import analyze_news_batch

articles = [
    {'title': "DRDGOLD (NYSE:DRD) Stock Looks Fairly Valued Despite Gold Price Selloff", 'description': "A quick look at DRDGOLD.", 'category': 'gold'},
    {'title': "Strategy's Saylor needs clarity in BTC pivot message", 'description': "Bitcoin holding...", 'category': 'btc'}
]

res = analyze_news_batch(articles)
print("Result:")
print(json.dumps(res, indent=2, ensure_ascii=False))
