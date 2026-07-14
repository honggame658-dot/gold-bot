import yfinance as yf
import pandas as pd
import numpy as np

def calculate_ta(df):
    """Calculate advanced TA including RSI, MACD, SMA, ATR, BB, and Pivots"""
    if df.empty or len(df) < 50:
        return None
        
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    ema_gain = gain.ewm(com=13, min_periods=14).mean()
    ema_loss = loss.ewm(com=13, min_periods=14).mean()
    rs = ema_gain / ema_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # SMAs
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # Bollinger Bands (20, 2)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)

    # ATR (Average True Range - 14 period)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    # Pivot Points (Standard) based on previous period
    prev_high = df['High'].shift(1)
    prev_low = df['Low'].shift(1)
    prev_close = df['Close'].shift(1)
    df['Pivot'] = (prev_high + prev_low + prev_close) / 3
    df['R1'] = (2 * df['Pivot']) - prev_low
    df['S1'] = (2 * df['Pivot']) - prev_high

    latest = df.iloc[-1]
    
    rsi = latest.get('RSI', 50)
    macd = latest.get('MACD', 0)
    macd_signal = latest.get('MACD_Signal', 0)
    sma_50 = latest.get('SMA_50', 0)
    sma_200 = latest.get('SMA_200', 0)
    bb_upper = latest.get('BB_Upper', 0)
    bb_lower = latest.get('BB_Lower', 0)
    atr = latest.get('ATR', 0)
    pivot = latest.get('Pivot', 0)
    r1 = latest.get('R1', 0)
    s1 = latest.get('S1', 0)
    price = latest['Close']
    
    # Analysis Logic
    rsi_status = "Neutral"
    if rsi > 70: rsi_status = "Overbought (Bearish bias)"
    elif rsi < 30: rsi_status = "Oversold (Bullish bias)"
        
    macd_status = "Bullish" if macd > macd_signal else "Bearish"
    
    bb_status = "Neutral"
    if price >= bb_upper: bb_status = "At Upper Band (Resistance)"
    elif price <= bb_lower: bb_status = "At Lower Band (Support)"
    
    trend = "Bullish"
    if price > sma_50 and price > sma_200: trend = "Strong Bullish"
    elif price < sma_50 and price < sma_200: trend = "Strong Bearish"
    elif price > sma_50 and price < sma_200: trend = "Sideways Bullish"
    elif price < sma_50 and price > sma_200: trend = "Pullback Bearish"

    return (f"RSI: {rsi:.1f} ({rsi_status}) | MACD: {macd_status} | Trend: {trend} | "
            f"BB: {bb_status} | ATR: {atr:.2f} | Pivot: {pivot:.2f} | R1: {r1:.2f} | S1: {s1:.2f}")

def fetch_technical_analysis(symbol="GC=F"):
    """Fetches 15M, 1H, and 1D data for the given symbol and combines TA."""
    try:
        ticker = yf.Ticker(symbol)
        
        # Fetch Multiple Timeframes
        df_15m = ticker.history(period="5d", interval="15m")
        df_1h = ticker.history(period="1mo", interval="1h")
        df_1d = ticker.history(period="1y", interval="1d")
        
        ta_15m = calculate_ta(df_15m)
        ta_1h = calculate_ta(df_1h)
        ta_1d = calculate_ta(df_1d)
        
        current_price = df_1d['Close'].iloc[-1] if not df_1d.empty else 0
        latest_atr = df_1d['ATR'].iloc[-1] if not df_1d.empty and 'ATR' in df_1d else 10.0
        
        asset_name = "Gold (XAU/USD)" if symbol == "GC=F" else "Bitcoin (BTC/USD)" if symbol == "BTC-USD" else symbol
        
        ta_text = f"[Technical Indicators - {asset_name} - MULTIPLE TIMEFRAMES]\nCurrent Price: ${current_price:.2f}\n"
        ta_text += f"Daily ATR (Volatility for SL/TP): ${latest_atr:.2f}\n\n"
        
        if ta_15m: ta_text += f"► 15-Min Chart (Scalping/Entry):\n  {ta_15m}\n\n"
        if ta_1h: ta_text += f"► 1-Hour Chart (Short-term Trend):\n  {ta_1h}\n\n"
        if ta_1d: ta_text += f"► 1-Day Chart (Macro Trend):\n  {ta_1d}\n"
        
        return ta_text.strip()
    except Exception as e:
        print(f"Error fetching TA data for {symbol}: {e}")
        return f"បញ្ហាក្នុងការទាញយកទិន្នន័យ TA ({symbol}): {e}"

if __name__ == "__main__":
    print(fetch_technical_analysis("GC=F"))
    print("\n---\n")
    print(fetch_technical_analysis("BTC-USD"))
