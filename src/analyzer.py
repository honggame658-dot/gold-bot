"""
🤖 AI Analyzer Module
Uses Google Gemini API to analyze the impact of news on Gold and BTC
"""

import os
import google.generativeai as genai
from datetime import datetime
from econ_calendar import get_daily_high_impact_news

# Initialize flag
_initialized = False

def init_gemini():
    """Initialize Gemini API with key from environment"""
    global _initialized
    if _initialized:
        return True
        
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        print('⚠️  GEMINI_API_KEY is not set. AI analysis will be disabled.')
        return False
        
    try:
        genai.configure(api_key=api_key)
        _initialized = True
        return True
    except Exception as e:
        print(f'❌ Error initializing Gemini API: {e}')
        return False

def analyze_news_batch(articles):
    """
    Analyze and translate a batch of articles in one API call to save rate limits.
    Returns a list of dictionaries with translations and analysis.
    """
    if not init_gemini() or not articles:
        return [None] * len(articles)
        
    try:
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        
        # Prepare the prompt for the batch
        prompt = """
        You are a top-tier financial analyst specializing in Gold (XAU/USD).
        I will give you a list of news articles (Title and Details).
        For EACH article, you must provide:
        1. A translation of the Title into KHMER (ភាសាខ្មែរ).
        2. A translation of the Details into KHMER (keep it short, 1-2 sentences).
        3. "impact": ["High", "Medium", "Low"]. (War/Conflicts and US Economic data are usually High/Medium).
        4. "signal": ["🟢 BUY (ទិញ)", "🔴 SELL (លក់)", "🟡 HOLD (រង់ចាំ)"]. (Buy if Gold will go up, Sell if Gold will drop, Hold if neutral).
        5. "analysis": A 1-2 sentence explanation IN KHMER about WHY it impacts GOLD price.
        
        Return the result as a JSON ARRAY of objects, matching the exact order of the input articles.
        Example format:
        [
            {
                "khmer_title": "ចំណងជើងជាភាសាខ្មែរ",
                "khmer_description": "សេចក្តីលម្អិតជាភាសាខ្មែរ...",
                "impact": "High",
                "signal": "🟢 BUY (ទិញ)",
                "analysis": "មាសអាចនឹងឡើងថ្លៃ ព្រោះវិនិយោគិននឹងរត់រកមាសជាទ្រព្យសុវត្ថិភាព..."
            }
        ]
        
        Articles to analyze:
        """
        
        for i, art in enumerate(articles):
            prompt += f"\nArticle {i+1}:\nTitle: {art.get('title')}\nDetails: {art.get('description', '')}\nCategory: {art.get('category', '')}\n"
            
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                text = response.text.strip()
                break
            except Exception as e:
                if '429' in str(e) and attempt < max_retries - 1:
                    print(f"  ⚠️ Rate limit hit, retrying in 60s (Attempt {attempt+1}/{max_retries})")
                    time.sleep(60)
                    continue
                else:
                    raise e
        
        if text.startswith('```json'): text = text[7:]
        if text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
            
        import json
        results = json.loads(text.strip())
        
        # Ensure we return a list of exactly the same length
        if len(results) != len(articles):
            print("  ⚠️ AI returned wrong number of results")
            return [None] * len(articles)
            
        return results
        
    except Exception as e:
        print(f'  ⚠️ AI Batch Analysis Error: {e}')
        return [None] * len(articles)

def analyze_market_summary(prices_text, headlines_text, ta_data="None"):
    """Generate a combined market summary using TA, News, and Economic Calendar"""
    if not init_gemini():
        return "⚠️ ប្រព័ន្ធ AI មិនទាន់រួចរាល់ទេ (បាត់ API Key)។"
        
    try:
        # Fetch today's economic events
        econ_events = get_daily_high_impact_news()
        
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = f"""
        You are an elite, highly accurate quantitative trader specializing in Gold (XAU/USD).
        Your task is to provide a comprehensive market summary and a high-probability trading signal by combining Multiple Timeframe Technical Analysis (MTF TA), Top Headlines, and Today's Economic Calendar.
        
        Prices:
        {prices_text}
        
        Technical Analysis (TA) Indicators (MTF):
        {ta_data}
        
        Today's Economic Events:
        {econ_events}
        
        Top Headlines:
        {headlines_text}
        
        Provide a 3-4 sentence summary IN KHMER LANGUAGE (ភាសាខ្មែរ).
        Focus ONLY on Gold (មាស). Mention if the market is Bullish or Bearish and why. Include analysis of the MTF alignment (e.g. 15m is bullish but 1D is bearish). If there are major Economic Events today, warn the user about potential volatility.
        
        AT THE END of your summary, provide exactly this format:
        
        📊 <b>សូចនាករទីផ្សាររួម (Overall Sentiment):</b>
        🟢 ទិញ (Buy): [X]%
        🔴 លក់ (Sell): [Y]%
        🌡️ កម្រិតអារម្មណ៍ (Fear & Greed Index): [0-100 Score. <40=Fear, 40-60=Neutral, >60=Greed. Write the score and one word in Khmer, e.g., 25 (ភ័យខ្លាច)]
        
        🎯 <b>សញ្ញាជួញដូរ (Trading Signal):</b>
        📍 ចូលផ្សារ (Entry): [If Buy: BUY at $X. If Sell: SELL at $X. If Wait: រង់ចាំសិន (WAIT). WARNING: The Entry price MUST be extremely close to the CURRENT PRICE provided above. DO NOT hallucinate old prices!]
        ✅ ប្រាក់ចំណេញ (TP): $[FINAL NUMBER ONLY. Must be $8-$15 away from Entry]
        ❌ កាត់ខាត (SL): $[FINAL NUMBER ONLY. Must be $3-$5 away from Entry]
        
        CRITICAL TRADING RULES (MUST FOLLOW STRICTLY):
        1. DAY TRADING BIAS: This is an intraday/scalping bot. Rely heavily on the 15m and 1h trends for your signal. If the 1D trend contradicts, DO NOT automatically output WAIT. Instead, provide a BUY or SELL signal based on the shorter timeframes, but warn the user in the footnote to use a smaller lot size. Try to avoid WAIT unless the market is completely flat and directionless.
        2. SUPPORT/RESISTANCE & CURRENT PRICE: Entry prices should ideally be near Pivot Points, S1, R1, or Bollinger Bands. **CRITICAL WARNING: The current year is 2026. Gold is trading around $4000+. DO NOT USE PRICES FROM YOUR TRAINING DATA (e.g., $2000-$2600). YOU MUST BASE YOUR ENTRY STRICTLY ON THE PROVIDED CURRENT PRICE!**
        3. STOP LOSS (SL) & TAKE PROFIT (TP): This is a scalping/intraday bot. Keep SL/TP realistic for day trading!
           - SL MUST be tight: Strictly $3 to $5 away from the Entry Price.
           - TP MUST be moderate: Strictly $8 to $15 away from the Entry Price for a good Risk/Reward ratio.
        4. X and Y sentiment percentages must add up to 100.
        5. You MUST NOT explain the math formula you used for TP/SL. However, you MAY add a helpful footnote starting with "*(ចំណាំ៖ ...)*" at the very bottom to provide risk management advice (e.g. "Because the 1D trend is Bearish, use small lot size").
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Market Summary Error: {e}")
        return "⚠️ សុំទោស AI កំពុងរវល់ ឬមានបញ្ហាបច្ចេកទេស (អាចមកពីទំហំផ្ទុក Free Tier ពេញ)។"
