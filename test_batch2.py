import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

from src.analyzer import analyze_news_batch, init_gemini
import google.generativeai as genai

print("Initializing Gemini...")
init_gemini()
print("Gemini initialized.")

articles = [
    {'title': "Ukraine war briefing: Zelenskyy replaces PM", 'description': "A quick look at Ukraine.", 'category': 'world'}
]

print("Calling analyze_news_batch...")
try:
    res = analyze_news_batch(articles)
    print("Result:")
    print(res)
except Exception as e:
    print(f"EXCEPTION: {e}")
