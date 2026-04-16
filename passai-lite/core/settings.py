# passai/core/settings.py

import json
from pathlib import Path
from typing import Any
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class Settings:
    """Application settings manager"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".passai"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.vault_path = self.config_dir / "vault.db"
        
        # Simple machine-specific key for encrypting saved password
        self.machine_key = self._get_machine_key()
        
        self.defaults = {
            "theme": "dark",
            "clipboard_timeout": 20,
            "auto_lock_minutes": 5,
            "font_family": "default",
            "window_width": 420,
            "window_height": 560,
            "vault_location": str(self.vault_path),
            "remember_password": False,
            "saved_password_enc": ""
        }
        
        self.settings = self.load()
    
    def _get_machine_key(self) -> bytes:
        """Get or create machine-specific encryption key"""
        key_file = self.config_dir / ".mkey"
        if key_file.exists():
            try:
                return base64.b64decode(key_file.read_text())
            except:
                pass
        # Generate new key
        key = AESGCM.generate_key(bit_length=256)
        key_file.write_text(base64.b64encode(key).decode())
        key_file.chmod(0o600)  # Restrict permissions
        return key
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        aesgcm = AESGCM(self.machine_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, password.encode(), None)
        # Combine nonce + ciphertext
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()
    
    def _decrypt_password(self, encrypted: str) -> str:
        """Decrypt stored password"""
        try:
            combined = base64.b64decode(encrypted)
            nonce = combined[:12]
            ciphertext = combined[12:]
            aesgcm = AESGCM(self.machine_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except:
            return ""
    
    def load(self) -> dict:
        """Load settings from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    return {**self.defaults, **loaded}
            except:
                pass
        return self.defaults.copy()
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        self.settings[key] = value
        self.save()
    
    def get_vault_path(self) -> Path:
        """Get vault database path"""
        vault_location = self.settings.get("vault_location", str(self.vault_path))
        return Path(vault_location)
    
    def save_password(self, password: str):
        """Save password for remember me (encrypted)"""
        encrypted = self._encrypt_password(password)
        self.settings["saved_password_enc"] = encrypted
        self.settings["remember_password"] = True
        self.save()
    
    def get_saved_password(self) -> str:
        """Get saved password if remember me enabled"""
        if not self.settings.get("remember_password", False):
            return ""
        encrypted = self.settings.get("saved_password_enc", "")
        if not encrypted:
            return ""
        return self._decrypt_password(encrypted)
    
    def clear_saved_password(self):
        """Clear saved password"""
        self.settings["saved_password_enc"] = ""
        self.settings["remember_password"] = False
        self.save()
