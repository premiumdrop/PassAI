# passai/core/storage.py

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from core.crypto import CryptoManager

class Storage:
    """SQLite storage with encrypted fields"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.crypto = CryptoManager()
        
    def initialize_db(self):
        """Create database schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Vault metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vault_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Password entries (all sensitive fields stored as encrypted base64)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_encrypted TEXT NOT NULL,
                title_nonce TEXT NOT NULL,
                username_encrypted TEXT NOT NULL,
                username_nonce TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                password_nonce TEXT NOT NULL,
                url_encrypted TEXT NOT NULL,
                url_nonce TEXT NOT NULL,
                notes_encrypted TEXT NOT NULL,
                notes_nonce TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                favorite INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def set_meta(self, key: str, value: str):
        """Store metadata"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
    
    def get_meta(self, key: str) -> Optional[str]:
        """Retrieve metadata"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM vault_meta WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def add_entry(
        self,
        title: str,
        username: str,
        password: str,
        url: str,
        notes: str,
        tags: List[str],
        favorite: bool,
        encryption_key: bytes
    ) -> int:
        """Add new password entry"""
        # Encrypt all sensitive fields
        title_enc, title_nonce = self.crypto.encrypt(title, encryption_key)
        username_enc, username_nonce = self.crypto.encrypt(username, encryption_key)
        password_enc, password_nonce = self.crypto.encrypt(password, encryption_key)
        url_enc, url_nonce = self.crypto.encrypt(url, encryption_key)
        notes_enc, notes_nonce = self.crypto.encrypt(notes, encryption_key)
        
        now = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO entries (
                title_encrypted, title_nonce,
                username_encrypted, username_nonce,
                password_encrypted, password_nonce,
                url_encrypted, url_nonce,
                notes_encrypted, notes_nonce,
                tags, favorite, created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.crypto.encode_base64(title_enc),
            self.crypto.encode_base64(title_nonce),
            self.crypto.encode_base64(username_enc),
            self.crypto.encode_base64(username_nonce),
            self.crypto.encode_base64(password_enc),
            self.crypto.encode_base64(password_nonce),
            self.crypto.encode_base64(url_enc),
            self.crypto.encode_base64(url_nonce),
            self.crypto.encode_base64(notes_enc),
            self.crypto.encode_base64(notes_nonce),
            json.dumps(tags),
            1 if favorite else 0,
            now,
            now
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_entry(
        self,
        entry_id: int,
        title: str,
        username: str,
        password: str,
        url: str,
        notes: str,
        tags: List[str],
        favorite: bool,
        encryption_key: bytes
    ):
        """Update existing entry"""
        title_enc, title_nonce = self.crypto.encrypt(title, encryption_key)
        username_enc, username_nonce = self.crypto.encrypt(username, encryption_key)
        password_enc, password_nonce = self.crypto.encrypt(password, encryption_key)
        url_enc, url_nonce = self.crypto.encrypt(url, encryption_key)
        notes_enc, notes_nonce = self.crypto.encrypt(notes, encryption_key)
        
        now = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE entries SET
                title_encrypted = ?, title_nonce = ?,
                username_encrypted = ?, username_nonce = ?,
                password_encrypted = ?, password_nonce = ?,
                url_encrypted = ?, url_nonce = ?,
                notes_encrypted = ?, notes_nonce = ?,
                tags = ?, favorite = ?, modified_at = ?
            WHERE id = ?
        """, (
            self.crypto.encode_base64(title_enc),
            self.crypto.encode_base64(title_nonce),
            self.crypto.encode_base64(username_enc),
            self.crypto.encode_base64(username_nonce),
            self.crypto.encode_base64(password_enc),
            self.crypto.encode_base64(password_nonce),
            self.crypto.encode_base64(url_enc),
            self.crypto.encode_base64(url_nonce),
            self.crypto.encode_base64(notes_enc),
            self.crypto.encode_base64(notes_nonce),
            json.dumps(tags),
            1 if favorite else 0,
            now,
            entry_id
        ))
        self.conn.commit()
    
    def delete_entry(self, entry_id: int):
        """Delete entry"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()
    
    def get_all_entries(self, encryption_key: bytes) -> List[Dict]:
        """Retrieve and decrypt all entries"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY favorite DESC, modified_at DESC")
        rows = cursor.fetchall()
        
        entries = []
        for row in rows:
            try:
                entry = {
                    'id': row['id'],
                    'title': self.crypto.decrypt(
                        self.crypto.decode_base64(row['title_encrypted']),
                        self.crypto.decode_base64(row['title_nonce']),
                        encryption_key
                    ),
                    'username': self.crypto.decrypt(
                        self.crypto.decode_base64(row['username_encrypted']),
                        self.crypto.decode_base64(row['username_nonce']),
                        encryption_key
                    ),
                    'password': self.crypto.decrypt(
                        self.crypto.decode_base64(row['password_encrypted']),
                        self.crypto.decode_base64(row['password_nonce']),
                        encryption_key
                    ),
                    'url': self.crypto.decrypt(
                        self.crypto.decode_base64(row['url_encrypted']),
                        self.crypto.decode_base64(row['url_nonce']),
                        encryption_key
                    ),
                    'notes': self.crypto.decrypt(
                        self.crypto.decode_base64(row['notes_encrypted']),
                        self.crypto.decode_base64(row['notes_nonce']),
                        encryption_key
                    ),
                    'tags': json.loads(row['tags']),
                    'favorite': bool(row['favorite']),
                    'created_at': row['created_at'],
                    'modified_at': row['modified_at']
                }
                entries.append(entry)
            except Exception as e:
                # Skip corrupted entries
                continue
        
        return entries
    
    def get_entry_by_id(self, entry_id: int, encryption_key: bytes) -> Optional[Dict]:
        """Retrieve single entry by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        try:
            return {
                'id': row['id'],
                'title': self.crypto.decrypt(
                    self.crypto.decode_base64(row['title_encrypted']),
                    self.crypto.decode_base64(row['title_nonce']),
                    encryption_key
                ),
                'username': self.crypto.decrypt(
                    self.crypto.decode_base64(row['username_encrypted']),
                    self.crypto.decode_base64(row['username_nonce']),
                    encryption_key
                ),
                'password': self.crypto.decrypt(
                    self.crypto.decode_base64(row['password_encrypted']),
                    self.crypto.decode_base64(row['password_nonce']),
                    encryption_key
                ),
                'url': self.crypto.decrypt(
                    self.crypto.decode_base64(row['url_encrypted']),
                    self.crypto.decode_base64(row['url_nonce']),
                    encryption_key
                ),
                'notes': self.crypto.decrypt(
                    self.crypto.decode_base64(row['notes_encrypted']),
                    self.crypto.decode_base64(row['notes_nonce']),
                    encryption_key
                ),
                'tags': json.loads(row['tags']),
                'favorite': bool(row['favorite']),
                'created_at': row['created_at'],
                'modified_at': row['modified_at']
            }
        except:
            return None
