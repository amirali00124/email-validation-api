from app import db
from datetime import datetime

class APIUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(64), nullable=False, index=True)
    endpoint = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    response_time = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    email_count = db.Column(db.Integer, default=1)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    tier = db.Column(db.String(20), default='free')  # free, basic, premium
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    requests_today = db.Column(db.Integer, default=0)
    last_request = db.Column(db.DateTime)

class EmailValidationResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    is_valid = db.Column(db.Boolean, nullable=False)
    domain = db.Column(db.String(255))
    mx_valid = db.Column(db.Boolean)
    is_disposable = db.Column(db.Boolean)
    is_role_account = db.Column(db.Boolean)
    domain_reputation = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    api_key = db.Column(db.String(64))
