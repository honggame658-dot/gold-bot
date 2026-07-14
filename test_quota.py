import os
from dotenv import load_dotenv
import google.generativeai as genai

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)

models = [
    'gemini-flash-latest',
    'gemini-flash-lite-latest',
    'gemini-3.5-flash',
    'gemini-2.0-flash-lite',
    'gemini-2.5-flash-lite'
]

for m in models:
    print(f"Testing model: {m}...")
    try:
        model = genai.GenerativeModel(m)
        response = model.generate_content("Say hello")
        print(f"SUCCESS with {m}: {response.text}")
        break
    except Exception as e:
        print(f"FAILED with {m}: {e}")
