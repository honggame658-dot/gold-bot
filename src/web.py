import os
import threading
from flask import Flask, render_template, jsonify
from db import get_stats, get_all_vips

app = Flask(__name__)

# Global variable to control the auto broadcast (this will be accessed from index.py too)
BROADCAST_ENABLED = True

@app.route('/')
def index():
    stats = get_stats()
    vips = get_all_vips()
    return render_template('index.html', stats=stats, vips=vips, broadcast_enabled=BROADCAST_ENABLED)

@app.route('/api/toggle_broadcast', methods=['POST'])
def toggle_broadcast():
    global BROADCAST_ENABLED
    BROADCAST_ENABLED = not BROADCAST_ENABLED
    return jsonify({"success": True, "broadcast_enabled": BROADCAST_ENABLED})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    # Run Flask in production using waitress if installed, otherwise built-in
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        app.run(host='0.0.0.0', port=port, use_reloader=False)

def start_web_server():
    """Starts the Flask server in a separate thread"""
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    print(f"🌐 Web Dashboard started in background on port {os.environ.get('PORT', 8080)}")
