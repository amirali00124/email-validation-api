import os
import logging
import threading
import time
import requests
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

db = SQLAlchemy()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for API access
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///email_validator.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Main routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/download')
def download():
    return render_template('download.html')

# Register API routes
from api_routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

def keep_alive():
    """Keep the app alive by pinging it every 5 minutes"""
    def ping_self():
        while True:
            try:
                time.sleep(300)  # Wait 5 minutes
                # Try to ping the health endpoint
                try:
                    # Get the app URL from environment or use localhost for development
                    app_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
                    response = requests.get(f"{app_url}/api/keepalive", timeout=30)
                    if response.status_code == 200:
                        app.logger.info("Keep-alive ping successful")
                    else:
                        app.logger.warning(f"Keep-alive ping failed with status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    app.logger.warning(f"Keep-alive ping failed: {e}")
                except Exception as e:
                    app.logger.error(f"Keep-alive error: {e}")
            except Exception as e:
                app.logger.error(f"Keep-alive thread error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    # Start the keep-alive thread
    ping_thread = threading.Thread(target=ping_self, daemon=True)
    ping_thread.start()
    app.logger.info("Keep-alive service started - pinging every 5 minutes")

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Start keep-alive service in production
    if not app.debug:
        keep_alive()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
