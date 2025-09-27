from cryptography.fernet import Fernet
from app.core.config import settings

class TokenEncryption:
    """Handles encryption/decryption of OAuth tokens"""
    
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string (e.g., OAuth token)"""
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string"""
        if not encrypted_data:
            return ""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

token_encryption = TokenEncryption()