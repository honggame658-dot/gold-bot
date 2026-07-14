import yfinance as yf
import pandas as pd
import numpy as np

def run_backtest(period="1y", interval="1d"):
    """
    Runs a simple backtest on historical Gold data based on the AI's core logic:
    Buy when price crosses above SMA50 and RSI is not Overbought.
    Sell when price crosses below SMA50 and RSI is not Oversold.
    Uses ATR for Stop Loss (0.5x) and Take Profit (1.5x).
    """
    print(f"🔄 ទាញយកទិន្នន័យមាស {period} ចុងក្រោយ (Interval: {interval})...")
    gold = yf.Ticker("GC=F")
    df = gold.history(period=period, interval=interval)
    
    if df.empty:
        print("❌ បរាជ័យក្នុងការទាញយកទិន្នន័យ!")
        return
        
    print(f"📊 ទិន្នន័យសរុប: {len(df)} ថ្ងៃ\n")
    
    # Calculate TA
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    ema_gain = gain.ewm(com=13, min_periods=14).mean()
    ema_loss = loss.ewm(com=13, min_periods=14).mean()
    rs = ema_gain / ema_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    df.dropna(inplace=True)
    
    in_position = False
    position_type = None # "BUY" or "SELL"
    entry_price = 0
    tp = 0
    sl = 0
    
    trades = 0
    wins = 0
    losses = 0
    total_profit = 0
    
    for index, row in df.iterrows():
        # Check if we hit TP or SL
        if in_position:
            if position_type == "BUY":
                if row['High'] >= tp:
                    wins += 1
                    total_profit += (tp - entry_price)
                    in_position = False
                elif row['Low'] <= sl:
                    losses += 1
                    total_profit -= (entry_price - sl)
                    in_position = False
            elif position_type == "SELL":
                if row['Low'] <= tp:
                    wins += 1
                    total_profit += (entry_price - tp)
                    in_position = False
                elif row['High'] >= sl:
                    losses += 1
                    total_profit -= (sl - entry_price)
                    in_position = False
                    
        # Check Entry Signals if not in position
        if not in_position:
            # Buy Signal: Crosses above SMA 50, RSI < 70
            if row['Close'] > row['SMA_50'] and df['Close'].shift(1).loc[index] <= df['SMA_50'].shift(1).loc[index] and row['RSI'] < 70:
                in_position = True
                position_type = "BUY"
                entry_price = row['Close']
                tp = entry_price + (row['ATR'] * 1.5)
                sl = entry_price - (row['ATR'] * 0.5)
                trades += 1
                
            # Sell Signal: Crosses below SMA 50, RSI > 30
            elif row['Close'] < row['SMA_50'] and df['Close'].shift(1).loc[index] >= df['SMA_50'].shift(1).loc[index] and row['RSI'] > 30:
                in_position = True
                position_type = "SELL"
                entry_price = row['Close']
                tp = entry_price - (row['ATR'] * 1.5)
                sl = entry_price + (row['ATR'] * 0.5)
                trades += 1

    # Output Results
    print("========================================")
    print("📈 លទ្ធផល Backtest (១ឆ្នាំចុងក្រោយ)")
    print("========================================")
    print(f"ចំនួន Trade សរុប: {trades} ដង")
    print(f"ចំនួនឈ្នះ (Win): {wins} ដង")
    print(f"ចំនួនចាញ់ (Loss): {losses} ដង")
    
    win_rate = (wins / trades * 100) if trades > 0 else 0
    print(f"អត្រាឈ្នះ (Win Rate): {win_rate:.2f}%")
    
    # 1 Lot = 100 oz. Profit is $ per oz.
    print(f"ប្រាក់ចំណេញសរុបប៉ាន់ស្មាន (បើវាយ 1 Lot គ្រប់ស្ពាន): ${total_profit * 100:,.2f}")
    print("========================================")

if __name__ == "__main__":
    run_backtest()
