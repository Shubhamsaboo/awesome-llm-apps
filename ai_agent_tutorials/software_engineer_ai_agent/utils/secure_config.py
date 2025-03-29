import os
from cryptography.fernet import Fernet
import base64
import hashlib

class SecureConfig:
    def __init__(self, secret_key_env="APP_SECRET_KEY"):
        """Initialize with a secret key from environment or generate one"""
        self.secret_key = os.environ.get(secret_key_env)
        if not self.secret_key:
            self.secret_key = Fernet.generate_key().decode()
            print(f"Generated new secret key. Set this in your environment: {secret_key_env}={self.secret_key}")
        
        # Create encryption key from secret key
        key = hashlib.sha256(self.secret_key.encode()).digest()
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(key))
        
    def encrypt(self, data):
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return None
    
    def store_api_key(self, session_state, api_key):
        """Securely store API key in session state"""
        session_state.encrypted_api_key = self.encrypt(api_key)
    
    def get_api_key(self, session_state):
        """Retrieve API key from session state"""
        if hasattr(session_state, 'encrypted_api_key'):
            return self.decrypt(session_state.encrypted_api_key)
        return None