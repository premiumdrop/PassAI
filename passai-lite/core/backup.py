# passai/core/backup.py

import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class BackupWorker(QRunnable):
    """Worker for performing backup operations in background"""
    
    class Signals(QObject):
        finished = pyqtSignal(bool, str)  # success, message
        
    def __init__(self, operation: str, vault_path: Path, backup_path: Optional[Path] = None):
        super().__init__()
        self.operation = operation
        self.vault_path = vault_path
        self.backup_path = backup_path
        self.signals = self.Signals()
        
    def run(self):
        """Execute backup operation"""
        try:
            if self.operation == "create":
                BackupManager.create_backup_sync(self.vault_path)
                self.signals.finished.emit(True, "Backup created successfully")
            elif self.operation == "restore":
                BackupManager.restore_backup_sync(self.vault_path, self.backup_path)
                self.signals.finished.emit(True, "Backup restored successfully")
        except Exception as e:
            self.signals.finished.emit(False, str(e))

class BackupManager:
    """Manage automatic and manual encrypted vault backups"""
    
    def __init__(self, vault_path: Path):
        """
        Initialize backup manager.
        
        Args:
            vault_path: Path to the main vault database file
        """
        self.vault_path = vault_path
        self.backup_dir = vault_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.max_backups = 5
        self.auto_backup_days = 3
        
        self.thread_pool = QThreadPool()
        
    def should_auto_backup(self) -> bool:
        """
        Check if an automatic backup should be created.
        
        Returns:
            True if backup is needed, False otherwise
        """
        backups = self.list_backups()
        if not backups:
            return True
            
        # Get most recent backup
        latest_backup = backups[0]
        backup_time = self._parse_backup_timestamp(latest_backup.stem)
        
        if backup_time:
            age = datetime.now() - backup_time
            return age.days >= self.auto_backup_days
            
        return True
    
    def create_backup_async(self, callback=None):
        """
        Create backup asynchronously.
        
        Args:
            callback: Function to call when done (receives success: bool, message: str)
        """
        worker = BackupWorker("create", self.vault_path)
        if callback:
            worker.signals.finished.connect(callback)
        self.thread_pool.start(worker)
    
    @staticmethod
    def create_backup_sync(vault_path: Path) -> Path:
        """
        Create backup synchronously (called by worker thread).
        
        Args:
            vault_path: Path to vault database
            
        Returns:
            Path to created backup file
            
        Raises:
            Exception if backup fails
        """
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault not found: {vault_path}")
        
        backup_dir = vault_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"passai_backup_{timestamp}.passai"
        backup_path = backup_dir / backup_filename
        
        # Copy encrypted database file
        shutil.copy2(vault_path, backup_path)
        
        # Clean up old backups
        BackupManager._cleanup_old_backups(backup_dir, max_backups=5)
        
        return backup_path
    
    def restore_backup_async(self, backup_path: Path, callback=None):
        """
        Restore backup asynchronously.
        
        Args:
            backup_path: Path to backup file to restore
            callback: Function to call when done
        """
        worker = BackupWorker("restore", self.vault_path, backup_path)
        if callback:
            worker.signals.finished.connect(callback)
        self.thread_pool.start(worker)
    
    @staticmethod
    def restore_backup_sync(vault_path: Path, backup_path: Path):
        """
        Restore backup synchronously (called by worker thread).
        
        Args:
            vault_path: Path to vault database
            backup_path: Path to backup file
            
        Raises:
            Exception if restore fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Create a backup of current vault before restoring
        if vault_path.exists():
            safety_backup = vault_path.parent / f"{vault_path.name}.before_restore"
            shutil.copy2(vault_path, safety_backup)
        
        # Restore backup
        shutil.copy2(backup_path, vault_path)
    
    def list_backups(self) -> List[Path]:
        """
        List all available backups, sorted by date (newest first).
        
        Returns:
            List of backup file paths
        """
        if not self.backup_dir.exists():
            return []
        
        backups = list(self.backup_dir.glob("passai_backup_*.passai"))
        # Sort by modification time, newest first
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups
    
    def get_backup_info(self, backup_path: Path) -> Tuple[datetime, int]:
        """
        Get information about a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Tuple of (timestamp, file_size_bytes)
        """
        timestamp = self._parse_backup_timestamp(backup_path.stem)
        if not timestamp:
            timestamp = datetime.fromtimestamp(backup_path.stat().st_mtime)
        
        size = backup_path.stat().st_size
        return timestamp, size
    
    @staticmethod
    def _parse_backup_timestamp(filename: str) -> Optional[datetime]:
        """
        Parse timestamp from backup filename.
        
        Args:
            filename: Backup filename (without extension)
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Extract timestamp from "passai_backup_YYYY-MM-DD_HH-MM-SS"
            parts = filename.split("_")
            if len(parts) >= 4:
                date_str = parts[2]  # YYYY-MM-DD
                time_str = parts[3]  # HH-MM-SS
                datetime_str = f"{date_str} {time_str.replace('-', ':')}"
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except:
            pass
        return None
    
    @staticmethod
    def _cleanup_old_backups(backup_dir: Path, max_backups: int = 5):
        """
        Delete old backups, keeping only the most recent ones.
        
        Args:
            backup_dir: Directory containing backups
            max_backups: Maximum number of backups to keep
        """
        backups = list(backup_dir.glob("passai_backup_*.passai"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Delete old backups
        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except:
                pass
    
    def format_backup_name(self, backup_path: Path) -> str:
        """
        Format backup name for display.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Human-readable backup name with date/time and size
        """
        timestamp, size = self.get_backup_info(backup_path)
        
        # Format timestamp
        time_str = timestamp.strftime("%B %d, %Y at %H:%M")
        
        # Format size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        return f"{time_str} ({size_str})"
