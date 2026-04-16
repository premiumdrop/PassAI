# passai/core/vault.py

from pathlib import Path
from typing import Optional, List, Dict
import shutil
from datetime import datetime
from core.crypto import CryptoManager
from core.storage import Storage

class Vault:
    """High-level vault management"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.crypto = CryptoManager()
        self.storage: Optional[Storage] = None
        self.encryption_key: Optional[bytes] = None
        self.is_locked = True
        
    def exists(self) -> bool:
        """Check if vault exists"""
        return self.vault_path.exists()
    
    def create(self, master_password: str):
        """Create new vault with master password"""
        if self.exists():
            raise ValueError("Vault already exists")
        
        # Generate salt and hash master password
        salt = self.crypto.generate_salt()
        password_hash = self.crypto.hash_master_password(master_password)
        
        # Initialize storage
        self.storage = Storage(self.vault_path)
        self.storage.initialize_db()
        
        # Store salt and password hash
        self.storage.set_meta('salt', self.crypto.encode_base64(salt))
        self.storage.set_meta('password_hash', password_hash)
        self.storage.set_meta('version', '1.0')
        self.storage.set_meta('created_at', datetime.now().isoformat())
        
        # Derive encryption key
        self.encryption_key = self.crypto.derive_key(master_password, salt)
        self.is_locked = False
    
    def unlock(self, master_password: str) -> bool:
        """Unlock vault with master password"""
        if not self.exists():
            return False
        
        # Open storage
        if not self.storage:
            self.storage = Storage(self.vault_path)
            self.storage.initialize_db()
        
        # Verify password
        stored_hash = self.storage.get_meta('password_hash')
        if not self.crypto.verify_master_password(stored_hash, master_password):
            return False
        
        # Derive encryption key
        salt = self.crypto.decode_base64(self.storage.get_meta('salt'))
        self.encryption_key = self.crypto.derive_key(master_password, salt)
        self.is_locked = False
        
        return True
    
    def lock(self):
        """Lock vault and clear encryption key"""
        self.encryption_key = None
        self.is_locked = True
    
    def is_unlocked(self) -> bool:
        """Check if vault is unlocked"""
        return not self.is_locked
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Change master password (re-encrypts all data)"""
        if self.is_locked:
            return False
        
        # Verify old password
        if not self.unlock(old_password):
            return False
        
        # Get all entries with old key
        old_key = self.encryption_key
        entries = self.storage.get_all_entries(old_key)
        
        # Generate new salt and hash
        new_salt = self.crypto.generate_salt()
        new_hash = self.crypto.hash_master_password(new_password)
        new_key = self.crypto.derive_key(new_password, new_salt)
        
        # Re-encrypt all entries
        for entry in entries:
            self.storage.update_entry(
                entry['id'],
                entry['title'],
                entry['username'],
                entry['password'],
                entry['url'],
                entry['notes'],
                entry['tags'],
                entry['favorite'],
                new_key
            )
        
        # Update meta
        self.storage.set_meta('salt', self.crypto.encode_base64(new_salt))
        self.storage.set_meta('password_hash', new_hash)
        
        self.encryption_key = new_key
        return True
    
    def add_entry(
        self,
        title: str,
        username: str,
        password: str,
        url: str = "",
        notes: str = "",
        tags: List[str] = None,
        favorite: bool = False
    ) -> int:
        """Add new password entry"""
        if self.is_locked:
            raise RuntimeError("Vault is locked")
        
        tags = tags or []
        return self.storage.add_entry(
            title, username, password, url, notes, tags, favorite, self.encryption_key
        )
    
    def update_entry(
        self,
        entry_id: int,
        title: str,
        username: str,
        password: str,
        url: str = "",
        notes: str = "",
        tags: List[str] = None,
        favorite: bool = False
    ):
        """Update existing entry"""
        if self.is_locked:
            raise RuntimeError("Vault is locked")
        
        tags = tags or []
        self.storage.update_entry(
            entry_id, title, username, password, url, notes, tags, favorite, self.encryption_key
        )
    
    def delete_entry(self, entry_id: int):
        """Delete entry"""
        if self.is_locked:
            raise RuntimeError("Vault is locked")
        
        self.storage.delete_entry(entry_id)
    
    def get_all_entries(self) -> List[Dict]:
        """Get all entries"""
        if self.is_locked:
            raise RuntimeError("Vault is locked")
        
        return self.storage.get_all_entries(self.encryption_key)
    
    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Get single entry"""
        if self.is_locked:
            raise RuntimeError("Vault is locked")
        
        return self.storage.get_entry_by_id(entry_id, self.encryption_key)
    
    def create_backup(self):
        """Create backup of vault"""
        if not self.exists():
            return
        
        backup_dir = self.vault_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"vault_backup_{timestamp}.db"
        
        shutil.copy2(self.vault_path, backup_path)
        
        # Keep only last 5 backups
        backups = sorted(backup_dir.glob("vault_backup_*.db"))
        for old_backup in backups[:-5]:
            old_backup.unlink()
    
    def close(self):
        """Close vault"""
        if self.storage:
            self.storage.close()
        self.lock()
