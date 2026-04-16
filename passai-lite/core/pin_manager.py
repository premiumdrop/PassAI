"""
4-digit PIN unlock manager
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os
import hashlib

class PINManager:
    """Manage 4-digit PIN for quick unlock"""
    
    __slots__ = ('settings', 'pin_key')
    
    def __init__(self, settings):
        self.settings = settings
        self.pin_key = self._get_pin_key()
    
    def _get_pin_key(self) -> bytes:
        """Get or create PIN encryption key"""
        pin_key_file = self.settings.config_dir / ".pkey"
        
        if pin_key_file.exists():
            try:
                return base64.b64decode(pin_key_file.read_text())
            except Exception:
                pass
        
        # Generate new key
        key = AESGCM.generate_key(bit_length=256)
        try:
            pin_key_file.write_text(base64.b64encode(key).decode())
            pin_key_file.chmod(0o600)
        except Exception:
            pass
        
        return key
    
    def is_enabled(self) -> bool:
        """Check if PIN is enabled"""
        return self.settings.get("pin_enabled", False)
    
    def set_pin(self, pin: str, master_password: str) -> bool:
        """
        Set 4-digit PIN
        
        Args:
            pin: 4-digit PIN
            master_password: Master password (to encrypt)
            
        Returns:
            True if successful
        """
        if len(pin) != 4 or not pin.isdigit():
            return False
        
        try:
            # Encrypt master password with PIN as additional data
            aesgcm = AESGCM(self.pin_key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, master_password.encode(), pin.encode())
            
            # Store encrypted data
            combined = nonce + ciphertext
            self.settings.set("pin_encrypted_password", base64.b64encode(combined).decode())
            self.settings.set("pin_hash", self._hash_pin(pin))
            self.settings.set("pin_enabled", True)
            
            return True
        except Exception:
            return False
    
    def verify_pin(self, pin: str) -> str:
        """
        Verify PIN and return master password
        
        Args:
            pin: 4-digit PIN to verify
            
        Returns:
            Master password if PIN correct, empty string otherwise
        """
        if not self.is_enabled():
            return ""
        
        if len(pin) != 4 or not pin.isdigit():
            return ""
        
        # Verify PIN hash
        stored_hash = self.settings.get("pin_hash", "")
        if self._hash_pin(pin) != stored_hash:
            return ""
        
        try:
            # Decrypt master password
            encrypted_data = base64.b64decode(self.settings.get("pin_encrypted_password", ""))
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            aesgcm = AESGCM(self.pin_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, pin.encode())
            return plaintext.decode()
        except Exception:
            return ""
    
    def disable_pin(self):
        """Disable PIN unlock"""
        self.settings.set("pin_enabled", False)
        self.settings.set("pin_encrypted_password", "")
        self.settings.set("pin_hash", "")
    
    def _hash_pin(self, pin: str) -> str:
        """Simple PIN hash for verification"""
        return hashlib.sha256(pin.encode()).hexdigest()
