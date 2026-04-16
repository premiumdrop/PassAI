"""
Startup Manager - Handles first run vs subsequent runs
"""
import os
import json
from pathlib import Path

class StartupManager:
    """Manages app startup flow"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".passai"
        self.app_dir.mkdir(exist_ok=True)
        self.config_file = self.app_dir / "config.json"
        self.vault_file = self.app_dir / "vault.db"
    
    def is_first_run(self):
        """Check if this is the first time running the app"""
        return not self.vault_file.exists()
    
    def has_pin(self):
        """Check if PIN is configured"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('pin_enabled', False)
        except:
            pass
        return False
    
    def mark_initialized(self):
        """Mark app as initialized"""
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            config['initialized'] = True
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error marking initialized: {e}")
    
    def get_startup_mode(self):
        """
        Determine startup mode:
        - 'first_run': Show vault creation
        - 'pin': Show PIN entry
        - 'password': Show password entry
        """
        if self.is_first_run():
            return 'first_run'
        elif self.has_pin():
            return 'pin'
        else:
            return 'password'
