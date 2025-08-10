from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
import logging
from datetime import datetime, timedelta
from email_validator import EmailValidator
from models import APIUsage, APIKey, EmailValidationResult, db
from app import limiter

api_bp = Blueprint('api', __name__)
email_validator = EmailValidator()

def get_api_key():
    """Extract API key from request headers or query parameters"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    return api_key

def validate_api_key(api_key):
    """Validate API key and check rate limits"""
    if not api_key:
        return None, "API key is required"
    
    key_obj = APIKey.query.filter_by(key=api_key, is_active=True).first()
    if not key_obj:
        return None, "Invalid API key"
    
    # Check daily rate limits based on tier
    today = datetime.utcnow().date()
    if key_obj.last_request and key_obj.last_request.date() != today:
        key_obj.requests_today = 0
    
    limits = {
        'free': 50,
        'basic': 1500,
        'premium': 6000
    }
    
    if key_obj.requests_today >= limits.get(key_obj.tier, 100):
        return None, f"Rate limit exceeded for {key_obj.tier} tier"
    
    return key_obj, None

def log_api_usage(api_key, endpoint, response_time, status_code, email_count=1):
    """Log API usage for analytics"""
    try:
        usage = APIUsage(
            api_key=api_key,
            endpoint=endpoint,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            response_time=response_time,
            status_code=status_code,
            email_count=email_count
        )
        db.session.add(usage)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to log API usage: {e}")

@api_bp.route('/validate', methods=['POST'])
@limiter.limit("10 per minute")
def validate_email():
    """Validate a single email address"""
    start_time = time.time()
    
    try:
        # Get and validate API key
        api_key = get_api_key()
        key_obj, error = validate_api_key(api_key)
        if error:
            return jsonify({'error': error}), 401
        
        # Get email from request
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email address is required'}), 400
        
        email = data['email'].strip().lower()
        if not email:
            return jsonify({'error': 'Email address cannot be empty'}), 400
        
        # Validate email
        result = email_validator.validate(email)
        
        # Update API key usage
        key_obj.requests_today += 1
        key_obj.last_request = datetime.utcnow()
        db.session.commit()
        
        # Log usage
        response_time = time.time() - start_time
        log_api_usage(api_key, '/validate', response_time, 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Email validation error: {e}")
        response_time = time.time() - start_time
        log_api_usage(api_key or 'unknown', '/validate', response_time, 500)
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/validate/bulk', methods=['POST'])
@limiter.limit("5 per minute")
def validate_bulk():
    """Validate multiple email addresses"""
    start_time = time.time()
    
    try:
        # Get and validate API key
        api_key = get_api_key()
        key_obj, error = validate_api_key(api_key)
        if error:
            return jsonify({'error': error}), 401
        
        # Get emails from request
        data = request.get_json()
        if not data or 'emails' not in data:
            return jsonify({'error': 'Emails array is required'}), 400
        
        emails = data['emails']
        if not isinstance(emails, list):
            return jsonify({'error': 'Emails must be an array'}), 400
        
        if len(emails) > 100:
            return jsonify({'error': 'Maximum 100 emails per request'}), 400
        
        if len(emails) == 0:
            return jsonify({'error': 'At least one email is required'}), 400
        
        # Check if user has enough requests left
        remaining_requests = {
            'free': 50,
            'basic': 1500,
            'premium': 6000
        }.get(key_obj.tier, 50) - key_obj.requests_today
        
        if len(emails) > remaining_requests:
            return jsonify({'error': f'Not enough requests remaining. You have {remaining_requests} requests left.'}), 429
        
        # Validate emails
        results = []
        for email in emails:
            if isinstance(email, str):
                email = email.strip().lower()
                if email:
                    result = email_validator.validate(email)
                    results.append(result)
        
        # Update API key usage
        key_obj.requests_today += len(results)
        key_obj.last_request = datetime.utcnow()
        db.session.commit()
        
        # Log usage
        response_time = time.time() - start_time
        log_api_usage(api_key, '/validate/bulk', response_time, 200, len(results))
        
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'total_valid': sum(1 for r in results if r['is_valid'])
        }), 200
        
    except Exception as e:
        logging.error(f"Bulk validation error: {e}")
        response_time = time.time() - start_time
        log_api_usage(api_key or 'unknown', '/validate/bulk', response_time, 500)
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/domain/reputation', methods=['GET'])
@limiter.limit("20 per minute")
def domain_reputation():
    """Get domain reputation score"""
    start_time = time.time()
    
    try:
        # Get and validate API key
        api_key = get_api_key()
        key_obj, error = validate_api_key(api_key)
        if error:
            return jsonify({'error': error}), 401
        
        domain = request.args.get('domain')
        if not domain:
            return jsonify({'error': 'Domain parameter is required'}), 400
        
        domain = domain.strip().lower()
        result = email_validator.get_domain_reputation(domain)
        
        # Update API key usage
        key_obj.requests_today += 1
        key_obj.last_request = datetime.utcnow()
        db.session.commit()
        
        # Log usage
        response_time = time.time() - start_time
        log_api_usage(api_key, '/domain/reputation', response_time, 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Domain reputation error: {e}")
        response_time = time.time() - start_time
        log_api_usage(api_key or 'unknown', '/domain/reputation', response_time, 500)
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/stats', methods=['GET'])
@limiter.limit("10 per minute")
def get_stats():
    """Get API usage statistics"""
    try:
        api_key = get_api_key()
        key_obj, error = validate_api_key(api_key)
        if error:
            return jsonify({'error': error}), 401
        
        # Get usage stats for this API key
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        total_requests = APIUsage.query.filter_by(api_key=api_key).count()
        today_requests = APIUsage.query.filter_by(api_key=api_key).filter(
            APIUsage.timestamp >= datetime.combine(today, datetime.min.time())
        ).count()
        
        week_requests = APIUsage.query.filter_by(api_key=api_key).filter(
            APIUsage.timestamp >= datetime.combine(week_ago, datetime.min.time())
        ).count()
        
        limits = {
            'free': 50,
            'basic': 1500,
            'premium': 6000
        }
        
        return jsonify({
            'tier': key_obj.tier,
            'daily_limit': limits.get(key_obj.tier, 100),
            'requests_today': key_obj.requests_today,
            'remaining_today': limits.get(key_obj.tier, 100) - key_obj.requests_today,
            'total_requests': total_requests,
            'requests_this_week': week_requests,
            'created_at': key_obj.created_at.isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@api_bp.route('/keepalive', methods=['GET'])
def keep_alive_ping():
    """Keep-alive endpoint for preventing server sleep"""
    return jsonify({
        'status': 'awake',
        'message': 'Server is active',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
