"""
🤖 Gold & BTC News Telegram Bot - Advanced Version
Uses ApplicationBuilder for commands, JobQueue for scheduled fetching
"""

import os
import time
import json
import asyncio
import sqlite3
from dotenv import load_dotenv

def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            target_price REAL,
            condition TEXT
        )
    ''')
    conn.commit()
    conn.close()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from news_fetcher import fetch_all_news
from price_fetcher import fetch_gold_price, fetch_btc_price
from formatter import format_news_message, format_price_alert
from db import get_unsent_articles, mark_article_sent, get_stats, add_vip, remove_vip, is_vip
from analyzer import analyze_news_batch


def load_env():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)


# ==========================================
# BACKGROUND JOBS
# ==========================================

async def auto_fetch_job(context: ContextTypes.DEFAULT_TYPE):
    """Job that runs every N minutes to fetch news and send to channel"""
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not chat_id:
        return
        
    print(f'⏰ [{time.strftime("%H:%M:%S")}] Starting auto-fetch cycle...')
    
    # 1. Fetch Prices
    gold_price = fetch_gold_price()
    
    price_summary = ""
    if gold_price:
        price_summary += f"🥇 Gold (XAU/USD): {gold_price['price']} {gold_price.get('change_emoji', '')} {gold_price.get('change_percent', '')}\n"
    
    # 2. Fetch News
    all_articles = fetch_all_news()
    
    # 3. Filter New Articles
    unsent = get_unsent_articles(all_articles)
    if not unsent:
        print('✅ No new articles to send.')
        return
        
    print(f'📬 New articles to analyze: {len(unsent)}')
    
    # 4. Analyze and Send in Batches
    batch_size = 5
    sent_count = 0
    from analyzer import analyze_news_batch
    
    for i in range(0, min(len(unsent), 20), batch_size):  # Max 20 articles per cycle to avoid spam
        batch = unsent[i:i + batch_size]
        filtered_batch = []
        
        print(f'  🤖 Analyzing batch of {len(batch)} articles together...')
        ai_results = analyze_news_batch(batch)
        
        for idx, article in enumerate(batch):
            ai_result = ai_results[idx]
            
            if ai_result:
                # Override with Khmer translations
                article['title'] = ai_result.get('khmer_title', article['title'])
                article['description'] = ai_result.get('khmer_description', article.get('description', ''))
                article['ai_analysis'] = ai_result
                
                # FILTER: Only send Medium or High impact news
                impact = ai_result.get('impact', 'Low')
                if impact in ['High', 'Medium']:
                    filtered_batch.append(article)
                else:
                    print(f"    ⏩ Skipped: {article['title'][:20]}... (Low Impact)")
                    mark_article_sent(article['link']) # Mark as sent so we don't process again
            else:
                # If AI fails, fallback to sending it anyway
                filtered_batch.append(article)
                
        await asyncio.sleep(4) # Prevent Gemini API rate limit (15 RPM limit on free tier)
        
        if not filtered_batch:
            continue
            
        # Format message
        message = format_news_message(filtered_batch, price_summary if i == 0 else '')
        
        # Send to Telegram
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            print(f'  ✅ Sent batch of {len(filtered_batch)} high/medium impact articles')
            
            # Mark as sent
            for article in filtered_batch:
                mark_article_sent(article['link'])
                sent_count += 1
                
        except Exception as e:
            print(f'  ❌ Error sending message: {e}')
            
        await asyncio.sleep(3) # Delay between batches
        
    print(f'📊 Stats: Sent {sent_count} important articles this cycle.')
    
    if sent_count > 0:
        print('🤖 Generating overall market summary...')
        from analyzer import analyze_market_summary
        
        # Prepare headlines for summary
        headlines = [a['title'] for a in unsent[:10]] # Top 10 headlines
        headlines_text = "\n".join(f"- {h}" for h in headlines)
        
        from ta_fetcher import fetch_technical_analysis
        ta_data = fetch_technical_analysis()
        
        summary = analyze_market_summary(price_summary, headlines_text, ta_data)
        if summary:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=summary,
                    parse_mode='HTML'
                )
                print('✅ Sent market summary with Buy/Sell percentages.')
            except Exception as e:
                print(f'❌ Error sending summary: {e}')

async def check_econ_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check for High Impact USD news."""
    CHANNEL_ID = os.environ.get('TELEGRAM_CHAT_ID')
    from econ_calendar import check_upcoming_high_impact_news
    msg = check_upcoming_high_impact_news()
    if msg:
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error sending econ alert: {e}")

async def check_price_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check if price crossed user alerts."""
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute('SELECT id, chat_id, target_price, condition FROM price_alerts')
        alerts = c.fetchall()
        
        if not alerts:
            conn.close()
            return
            
        import yfinance as yf
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1d", interval="1m")
        if df.empty:
            conn.close()
            return
            
        current_price = df['Close'].iloc[-1]
        
        for alert_id, chat_id, target_price, condition in alerts:
            triggered = False
            if condition == "UP" and current_price >= target_price:
                triggered = True
            elif condition == "DOWN" and current_price <= target_price:
                triggered = True
                
            if triggered:
                msg = f"🔔 <b>[Price Alert]</b>\nទីផ្សារមាស (XAU/USD) បានរត់ដល់គោលដៅរបស់អ្នកហើយ!\n\nតម្លៃបច្ចុប្បន្ន: <b>${current_price:.2f}</b>"
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
                c.execute('DELETE FROM price_alerts WHERE id = ?', (alert_id,))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error checking price alerts: {e}")

# COMMAND HANDLERS
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "សួស្តី! 👋 ខ្ញុំជា Bot តាមដានព័ត៌មានមាស និង Bitcoin ប្រចាំថ្ងៃ។\n"
        "អ្នកអាចប្រើបញ្ជាខាងក្រោមបាន៖\n"
        "/price - ឆែកមើលតម្លៃបច្ចុប្បន្ន\n"
        "/news - ទាញយកព័ត៌មានក្តៅៗ\n"
        "/analyze - អោយ AI វិភាគទីផ្សារជារួម"
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command"""
    await update.message.reply_text("⏳ កំពុងទាញយកតម្លៃបច្ចុប្បន្ន...")
    
    gold = fetch_gold_price()
    
    text = "📊 <b>តម្លៃទីផ្សារបច្ចុប្បន្ន:</b>\n\n"
    if gold:
        text += f"🥇 <b>Gold (XAU/USD):</b> {gold['price']} {gold.get('change_emoji', '')} {gold.get('change_percent', '')}\n"
        
    await update.message.reply_text(text, parse_mode='HTML')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news command"""
    await update.message.reply_text("⏳ កំពុងស្វែងរកព័ត៌មានក្តៅៗ...")
    
    articles = fetch_all_news()
    if not articles:
        await update.message.reply_text("មិនមានព័ត៌មានថ្មីៗទេនាពេលនេះ។")
        return
        
    from analyzer import analyze_news_batch
    
    # Take top 3 articles
    top_articles = articles[:3]
    
    ai_results = analyze_news_batch(top_articles)
    
    for idx, article in enumerate(top_articles):
        ai_result = ai_results[idx]
        if ai_result:
            article['title'] = ai_result.get('khmer_title', article['title'])
            article['description'] = ai_result.get('khmer_description', article.get('description', ''))
            article['ai_analysis'] = ai_result
            
    msg = format_news_message(top_articles, "🔥 <b>ព័ត៌មានក្តៅៗទើបទទួលបាន:</b>\n")
    await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze command"""
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID') or os.environ.get('TELEGRAM_CHAT_ID')
    user_id = str(update.message.from_user.id)
    chat_id = str(update.message.chat_id)
    
    # VIP Check
    if chat_id != admin_id and user_id != admin_id and not is_vip(user_id):
        await update.message.reply_text("⛔️ សុំទោស! មុខងារនេះសម្រាប់តែសមាជិក VIP ប៉ុណ្ណោះ។ សូមទាក់ទង Admin ដើម្បីទិញកញ្ចប់ VIP ទទួលបាន Signal ជារៀងរាល់ថ្ងៃ!")
        return

    symbol_arg = context.args[0].lower() if context.args else "gold"
    is_btc = symbol_arg == "btc" or symbol_arg == "bitcoin"
    symbol = "BTC-USD" if is_btc else "GC=F"
    asset_name = "Bitcoin (BTC/USD)" if is_btc else "Gold (XAU/USD)"
    
    await update.message.reply_text(f"⏳ កំពុងវិភាគទីផ្សារ {asset_name} សូមរង់ចាំបន្តិច...")
    
    from analyzer import analyze_market_summary
    
    price_text = ""
    if is_btc:
        btc_price = fetch_btc_price()
        if btc_price:
            price_text += f"BTC (BTC/USD): {btc_price['price']}\n"
    else:
        gold = fetch_gold_price()
        if gold:
            price_text += f"Gold (XAU/USD): {gold['price']}\n"
        
    articles = fetch_all_news()
    headlines = [a['title'] for a in articles[:10]]
    headlines_text = "\n".join(f"- {h}" for h in headlines)
    
    from ta_fetcher import fetch_technical_analysis
    ta_data = fetch_technical_analysis(symbol)
    
    summary = analyze_market_summary(price_text, headlines_text, ta_data)
    
    # Generate and send chart first
    try:
        from chart_generator import generate_chart
        chart_path = generate_chart(symbol)
        if chart_path and os.path.exists(chart_path):
            await update.message.reply_photo(photo=open(chart_path, "rb"), caption=f"📊 ទីផ្សារ {asset_name} 15-Min Timeframe")
    except Exception as e:
        print(f"Failed to send chart: {e}")
        
    if summary:
        await update.message.reply_text(summary, parse_mode='HTML')
    else:
        await update.message.reply_text("⚠️ មិនអាចវិភាគទីផ្សារបានទេពេលនេះ។")


# ==========================================
# MAIN ENTRY POINT
# ==========================================

last_broadcast_asset = "gold"

async def auto_broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    """Broadcasts Gold analysis to the main chat every 5 minutes."""
    import web
    if not web.BROADCAST_ENABLED:
        return
        
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not chat_id:
        return
        
    symbol = "GC=F"
    asset_name = "Gold (XAU/USD)"
    
    try:
        from analyzer import analyze_market_summary
        from ta_fetcher import fetch_technical_analysis
        from chart_generator import generate_chart
        
        price_text = ""
        gold = fetch_gold_price()
        if gold: price_text += f"Gold (XAU/USD): {gold['price']}\n"
            
        articles = fetch_all_news()
        headlines = [a['title'] for a in articles[:10]]
        headlines_text = "\n".join(f"- {h}" for h in headlines)
        
        ta_data = fetch_technical_analysis(symbol)
        summary = analyze_market_summary(price_text, headlines_text, ta_data)
        
        chart_path = generate_chart(symbol)
        if chart_path and os.path.exists(chart_path):
            await context.bot.send_photo(chat_id=chat_id, photo=open(chart_path, "rb"), caption=f"🔄 Auto-Broadcast (5-Min): 📊 ទីផ្សារ {asset_name}")
            
        if summary:
            await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode='HTML')
            
    except Exception as e:
        print(f"Auto-broadcast error: {e}")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a price alert. Usage: /alert 2450"""
    try:
        if len(context.args) < 1:
            await update.message.reply_text("សូមប្រើប្រាស់ទម្រង់: /alert [តម្លៃ]\nឧទាហរណ៍: /alert 2450")
            return
            
        target_price = float(context.args[0])
        chat_id = update.message.chat_id
        
        import yfinance as yf
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1d", interval="1m")
        if df.empty:
            await update.message.reply_text("⚠️ មិនអាចទាញយកតម្លៃបច្ចុប្បន្នបានទេ។ សូមសាកល្បងម្តងទៀតនៅពេលក្រោយ។")
            return
            
        current_price = df['Close'].iloc[-1]
        condition = "UP" if target_price > current_price else "DOWN"
        
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute('INSERT INTO price_alerts (chat_id, target_price, condition) VALUES (?, ?, ?)', (chat_id, target_price, condition))
        conn.commit()
        conn.close()
        
        direction = "កើនឡើង" if condition == "UP" else "ធ្លាក់ចុះ"
        await update.message.reply_text(f"✅ បានកំណត់ការរោទ៍ដោយជោគជ័យ!\nពេលមាស{direction}ដល់ ${target_price} (តម្លៃបច្ចុប្បន្ន ${current_price:.2f}) ខ្ញុំនឹងប្រាប់អ្នក។")
    except ValueError:
        await update.message.reply_text("❌ តម្លៃមិនត្រឹមត្រូវ។ សូមបញ្ចូូលជាលេខ។")

# ==========================================
# VIP COMMANDS
# ==========================================

async def addvip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add VIP. Usage: /addvip 123456789 30"""
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID') or os.environ.get('TELEGRAM_CHAT_ID')
    if str(update.message.from_user.id) != admin_id:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("ទម្រង់ខុស! ប្រើ: /addvip [user_id] [ចំនួនថ្ងៃ]\nឧទាហរណ៍: /addvip 123456789 30")
        return
        
    user_id = context.args[0]
    days = int(context.args[1])
    expire = add_vip(user_id, "VIP_User", days)
    
    # Format date nicely
    formatted_date = expire.strftime("%d-%b-%Y")
    await update.message.reply_text(f"✅ ជោគជ័យ! សមាជិក {user_id} បានក្លាយជា VIP រហូតដល់ថ្ងៃទី {formatted_date}។")

async def removevip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove VIP. Usage: /removevip 123456789"""
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID') or os.environ.get('TELEGRAM_CHAT_ID')
    if str(update.message.from_user.id) != admin_id:
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("ទម្រង់ខុស! ប្រើ: /removevip [user_id]")
        return
        
    user_id = context.args[0]
    if remove_vip(user_id):
        await update.message.reply_text(f"✅ ជោគជ័យ! សមាជិក {user_id} ត្រូវបានដកចេញពី VIP។")
    else:
        await update.message.reply_text(f"❌ រកមិនឃើញសមាជិក {user_id} ទេ។")

async def claimadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim Admin privileges if not already set"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    user_id = str(update.message.from_user.id)
    
    with open(env_path, 'r') as f:
        content = f.read()
        
    if 'TELEGRAM_ADMIN_ID' in content:
        await update.message.reply_text("Admin ត្រូវបានកំណត់រួចហើយ! (Admin is already claimed!)")
    else:
        with open(env_path, 'a') as f:
            f.write(f"\nTELEGRAM_ADMIN_ID={user_id}\n")
        os.environ['TELEGRAM_ADMIN_ID'] = user_id
        await update.message.reply_text(f"✅ ជោគជ័យ! ឥឡូវនេះអ្នក (ID: {user_id}) គឺជា Admin របស់ Bot នេះហើយ។ អ្នកអាចប្រើប្រាស់ /addvip, /removevip, និង /analyze បានដោយសេរី។")

def main():
    load_env()
    init_db()
    
    # Start Web Server
    import web
    web.start_web_server()
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in .env")
        return
        
    print("---------------------------------------")
    print("    [ Advanced Gold & BTC News Bot ]   ")
    print("---------------------------------------")
    
    # Initialize application
    app = ApplicationBuilder().token(token).build()
    
    # Add Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("addvip", addvip_command))
    app.add_handler(CommandHandler("removevip", removevip_command))
    app.add_handler(CommandHandler("claimadmin", claimadmin_command))
    
    # Add Scheduled Jobs
    job_queue = app.job_queue
    job_queue.run_repeating(auto_fetch_job, interval=900, first=10)
    job_queue.run_repeating(check_econ_job, interval=600, first=15)
    job_queue.run_repeating(check_price_alerts_job, interval=60, first=5)
    job_queue.run_repeating(auto_broadcast_job, interval=300, first=20) # 5-min auto broadcast
    
    print(f"Bot started! Monitoring enabled.")
    print("Press Ctrl+C to stop")
    
    # Run the bot
    app.run_polling()

if __name__ == '__main__':
    main()
