# passai/core/clipboard.py

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

class ClipboardManager:
    """Manage clipboard operations with auto-clear"""
    
    def __init__(self, clear_timeout: int = 20):
        self.clear_timeout = clear_timeout * 1000  # Convert to ms
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._clear_clipboard)
        self.last_copied = None
    
    def copy(self, text: str):
        """Copy text to clipboard with auto-clear"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.last_copied = text
        
        # Start auto-clear timer
        if self.clear_timeout > 0:
            self.timer.start(self.clear_timeout)
    
    def _clear_clipboard(self):
        """Clear clipboard if it still contains our text"""
        clipboard = QApplication.clipboard()
        if clipboard.text() == self.last_copied:
            clipboard.clear()
        self.last_copied = None
    
    def set_timeout(self, seconds: int):
        """Update clear timeout"""
        self.clear_timeout = seconds * 1000
    
    def cancel_clear(self):
        """Cancel pending clear operation"""
        self.timer.stop()
