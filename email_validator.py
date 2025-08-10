import re
import dns.resolver
import requests
import logging
from disposable_domains import DISPOSABLE_DOMAINS

class EmailValidator:
    def __init__(self):
        self.role_accounts = {
            'admin', 'administrator', 'support', 'help', 'info', 'contact',
            'sales', 'marketing', 'noreply', 'no-reply', 'postmaster',
            'webmaster', 'hostmaster', 'abuse', 'security', 'root'
        }
        
    def validate(self, email):
        """Comprehensive email validation"""
        result = {
            'email': email,
            'is_valid': False,
            'syntax_valid': False,
            'domain': None,
            'mx_valid': False,
            'is_disposable': False,
            'is_role_account': False,
            'domain_reputation': 0.0,
            'errors': []
        }
        
        # Basic syntax validation
        if not self._validate_syntax(email):
            result['errors'].append('Invalid email syntax')
            return result
        
        result['syntax_valid'] = True
        
        # Extract domain
        try:
            local, domain = email.rsplit('@', 1)
            result['domain'] = domain.lower()
        except ValueError:
            result['errors'].append('Invalid email format')
            return result
        
        # Check if disposable
        result['is_disposable'] = self._is_disposable(domain)
        if result['is_disposable']:
            result['errors'].append('Disposable email address')
        
        # Check if role account
        result['is_role_account'] = self._is_role_account(local)
        
        # Validate MX records
        result['mx_valid'] = self._validate_mx(domain)
        if not result['mx_valid']:
            result['errors'].append('No valid MX records found')
        
        # Get domain reputation
        result['domain_reputation'] = self._get_domain_reputation_score(domain)
        
        # Overall validity
        result['is_valid'] = (
            result['syntax_valid'] and 
            result['mx_valid'] and 
            not result['is_disposable'] and
            result['domain_reputation'] > 0.3
        )
        
        return result
    
    def _validate_syntax(self, email):
        """Validate email syntax using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_mx(self, domain):
        """Validate MX records for domain"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            return False
    
    def _is_disposable(self, domain):
        """Check if domain is disposable"""
        return domain.lower() in DISPOSABLE_DOMAINS
    
    def _is_role_account(self, local_part):
        """Check if email is a role account"""
        return local_part.lower() in self.role_accounts
    
    def _get_domain_reputation_score(self, domain):
        """Calculate domain reputation score"""
        score = 0.5  # Base score
        
        # Check domain age and popularity (simplified)
        popular_domains = {
            'gmail.com': 0.95,
            'yahoo.com': 0.90,
            'outlook.com': 0.90,
            'hotmail.com': 0.85,
            'aol.com': 0.80,
            'icloud.com': 0.85,
            'protonmail.com': 0.80
        }
        
        if domain in popular_domains:
            score = popular_domains[domain]
        else:
            # For other domains, check basic indicators
            try:
                # Check if domain has A record
                dns.resolver.resolve(domain, 'A')
                score += 0.2
                
                # Check if domain has valid MX
                if self._validate_mx(domain):
                    score += 0.2
                
                # Check domain length (shorter established domains tend to be more reputable)
                if len(domain) < 15:
                    score += 0.1
                
            except Exception:
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def get_domain_reputation(self, domain):
        """Get detailed domain reputation information"""
        result = {
            'domain': domain,
            'reputation_score': self._get_domain_reputation_score(domain),
            'has_mx': self._validate_mx(domain),
            'is_disposable': self._is_disposable(domain),
            'category': 'unknown'
        }
        
        # Categorize domain
        if result['reputation_score'] >= 0.8:
            result['category'] = 'excellent'
        elif result['reputation_score'] >= 0.6:
            result['category'] = 'good'
        elif result['reputation_score'] >= 0.4:
            result['category'] = 'fair'
        else:
            result['category'] = 'poor'
        
        return result
