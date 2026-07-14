import yfinance as yf
import mplfinance as mpf
import pandas as pd
import os

def generate_chart(symbol="GC=F", filepath="chart.png"):
    """
    Downloads 15-minute data for the last 5 days and generates
    a candlestick chart with SMA and Bollinger Bands using mplfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="15m")
        
        if df.empty:
            return None
            
        # We only want the last 50-100 candles for a clean view
        df = df.iloc[-60:]
        
        # Calculate Bollinger Bands
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['STD_20'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
        df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
        
        # Define the custom style
        mc = mpf.make_marketcolors(
            up='green', down='red',
            edge='inherit',
            wick='inherit',
            volume='in',
            ohlc='i'
        )
        s = mpf.make_mpf_style(
            marketcolors=mc,
            base_mpf_style='nightclouds',
            gridcolor='gray',
            gridstyle='--',
            y_on_right=True
        )
        
        # Additional plots: Bollinger Bands
        addplots = []
        if not df['BB_Upper'].isnull().all():
            bb_upper_plot = mpf.make_addplot(df['BB_Upper'], color='fuchsia', alpha=0.5, linestyle='--')
            bb_lower_plot = mpf.make_addplot(df['BB_Lower'], color='fuchsia', alpha=0.5, linestyle='--')
            addplots.extend([bb_upper_plot, bb_lower_plot])
            
        asset_name = "Gold (XAU/USD)" if symbol == "GC=F" else "Bitcoin (BTC/USD)" if symbol == "BTC-USD" else symbol
        
        # Draw and save the chart
        mpf.plot(
            df,
            type='candle',
            style=s,
            title=f'{asset_name} - 15Min',
            ylabel='Price ($)',
            addplot=addplots,
            savefig=dict(fname=filepath, dpi=120, bbox_inches='tight'),
            figsize=(10, 6)
        )
        
        return filepath
    except Exception as e:
        print(f"Error generating chart for {symbol}: {e}")
        return None

if __name__ == "__main__":
    file1 = generate_chart("GC=F", "chart_gold.png")
    print(f"Chart saved to {file1}")
    file2 = generate_chart("BTC-USD", "chart_btc.png")
    print(f"Chart saved to {file2}")
