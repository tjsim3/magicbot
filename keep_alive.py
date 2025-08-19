from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Discord Bot Status</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f0f0f0; }
                .container { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { color: #28a745; font-weight: bold; }
                .info { margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Discord Bot Status</h1>
                <p class="status">✅ Bot is running and ready!</p>
                <div class="info">
                    <h3>ℹ️ Information</h3>
                    <p>This is a keep-alive endpoint for the Discord bot running on Replit.</p>
                    <p>The bot should be online and responding to commands in your Discord server.</p>
                    <p><strong>Note:</strong> This web interface is only for keeping the bot alive 24/7.</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/status')
def status():
    return {"status": "online", "message": "Discord bot is running"}

def run():
    """Run the Flask app on port 5000"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    """Start the keep-alive server in a separate thread"""
    print("Starting keep-alive server...")
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("Keep-alive server started on port 5000")
