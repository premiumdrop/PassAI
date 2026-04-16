# passai/core/crypto.py

import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from argon2 import PasswordHasher
from argon2.low_level import hash_secret_raw, Type
import base64

class CryptoManager:
    """Handles all encryption, decryption, and key derivation"""
    
    def __init__(self):
        self.key_length = 32  # 256-bit key for AES-GCM
        
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using Argon2id"""
        key = hash_secret_raw(
            secret=password.encode('utf-8'),
            salt=salt,
            time_cost=3,  # iterations
            memory_cost=65536,  # 64 MB
            parallelism=4,
            hash_len=self.key_length,
            type=Type.ID  # Argon2id
        )
        return key
    
    def generate_salt(self) -> bytes:
        """Generate a random salt"""
        return os.urandom(16)
    
    def encrypt(self, plaintext: str, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt plaintext using AES-GCM
        Returns (ciphertext, nonce)
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes, key: bytes) -> str:
        """Decrypt ciphertext using AES-GCM"""
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    
    def hash_master_password(self, password: str) -> str:
        """Hash master password for verification (Argon2id)"""
        ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
        return ph.hash(password)
    
    def verify_master_password(self, hash_str: str, password: str) -> bool:
        """Verify master password against stored hash"""
        ph = PasswordHasher()
        try:
            ph.verify(hash_str, password)
            return True
        except:
            return False
    
    def encode_base64(self, data: bytes) -> str:
        """Encode bytes to base64 string"""
        return base64.b64encode(data).decode('utf-8')
    
    def decode_base64(self, data: str) -> bytes:
        """Decode base64 string to bytes"""
        return base64.b64decode(data.encode('utf-8'))
    
    def create_session_token(self, password: str) -> str:
        """Create encrypted session token for Remember Me"""
        # Generate random session key
        session_key = os.urandom(32)
        # Encrypt password with session key
        aesgcm = AESGCM(session_key)
        nonce = os.urandom(12)
        encrypted_password = aesgcm.encrypt(nonce, password.encode('utf-8'), None)
        # Combine session_key + nonce + encrypted_password
        token_data = session_key + nonce + encrypted_password
        return self.encode_base64(token_data)
    
    def decrypt_session_token(self, token: str) -> str:
        """Decrypt session token to get password"""
        token_data = self.decode_base64(token)
        session_key = token_data[:32]
        nonce = token_data[32:44]
        encrypted_password = token_data[44:]
        aesgcm = AESGCM(session_key)
        password = aesgcm.decrypt(nonce, encrypted_password, None)
        return password.decode('utf-8')
