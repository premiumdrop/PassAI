"""PassAI Lite — v1.0L"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

class PassAI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("PassAI Lite")
        self.app.setStyle("Fusion")
        self.app.setQuitOnLastWindowClosed(False)   # keep alive when window closes

        # ── System tray ───────────────────────────────────────────────────────
        icon_path = Path(__file__).parent / "assets" / "icons" / "icon.ico"
        app_icon  = QIcon(str(icon_path)) if icon_path.exists() else QIcon()

        self.tray = QSystemTrayIcon(app_icon, self.app)
        self.tray.setToolTip("PassAI Lite")

        tray_menu = QMenu()
        act_open = tray_menu.addAction("Open PassAI Lite")
        tray_menu.addSeparator()
        act_quit = tray_menu.addAction("Quit")

        act_open.triggered.connect(self._show_active_window)
        act_quit.triggered.connect(self.app.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        # ─────────────────────────────────────────────────────────────────────

        # Import and show PIN window IMMEDIATELY
        from ui.unlock_pin import UnlockPINWindow
        from core.settings import Settings
        from core.startup import StartupManager

        self.settings = Settings()
        self.startup_manager = StartupManager()
        self.vault = None
        self.main_window = None
        self.pin_window = None

        mode = self.startup_manager.get_startup_mode()

        if mode == 'first_run':
            self.show_password_setup()
        else:
            # SHOW PIN WINDOW INSTANTLY
            self.pin_window = UnlockPINWindow()
            self.pin_window.pin_entered.connect(self.unlock_vault)
            self.pin_window.show()
            self.pin_window.raise_()
            self.pin_window.activateWindow()

            # Load vault in background
            QTimer.singleShot(50, self.load_vault_bg)

    # ── Tray helpers ──────────────────────────────────────────────────────────

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_active_window()

    def _show_active_window(self):
        """Bring the visible window to front, or show unlock if everything is closed."""
        for w in [self.main_window, self.pin_window]:
            if w and w.isVisible():
                w.showNormal()
                w.raise_()
                w.activateWindow()
                return
        # Nothing visible — user closed the window; show unlock screen
        self._reopen_unlock()

    def _reopen_unlock(self):
        """Show a fresh PIN unlock screen and lock the vault."""
        from ui.unlock_pin import UnlockPINWindow
        # Disconnect stale signal connections
        if self.pin_window:
            try:
                self.pin_window.pin_entered.disconnect()
            except Exception:
                pass
        # Lock vault so the user must re-authenticate
        if self.vault:
            try:
                self.vault.lock()
            except Exception:
                pass
        self.pin_window = UnlockPINWindow()
        self.pin_window.pin_entered.connect(self.unlock_vault)
        self.pin_window.show()
        self.pin_window.raise_()
        self.pin_window.activateWindow()

    # ── Vault lifecycle ───────────────────────────────────────────────────────

    def load_vault_bg(self):
        """Load vault in background"""
        from core.vault import Vault
        try:
            self.vault = Vault(self.settings.get_vault_path())
        except Exception:
            pass

    def show_password_setup(self):
        from ui.setup_password import SetupPasswordWindow
        self.pin_window = SetupPasswordWindow()
        self.pin_window.password_created.connect(self.create_vault)
        self.pin_window.show()

    def create_vault(self, password):
        from core.vault import Vault
        from ui.setup_pin import SetupPINWindow
        from core.pin_manager import PINManager

        vault_path = self.settings.get_vault_path()
        vault_path.parent.mkdir(parents=True, exist_ok=True)

        self.vault = Vault(vault_path)
        self.vault.create(password)
        self.vault.unlock(password)
        self.startup_manager.mark_initialized()

        if self.pin_window:
            self.pin_window.close()

        self.pin_window = SetupPINWindow()
        self.pin_window.pin_created.connect(lambda pin: self.save_pin(pin, password))
        self.pin_window.show()

    def save_pin(self, pin, password):
        from core.pin_manager import PINManager
        PINManager(self.settings).set_pin(pin, password)

        if self.pin_window:
            self.pin_window.close()

        self.show_main()

    def unlock_vault(self, pin):
        from core.pin_manager import PINManager
        from core.vault import Vault

        master_pw = PINManager(self.settings).verify_pin(pin)
        if not master_pw:
            if self.pin_window:
                self.pin_window.show_error()
            return

        if not self.vault:
            self.vault = Vault(self.settings.get_vault_path())

        if self.vault.unlock(master_pw):
            if self.pin_window:
                self.pin_window.close()
            from ui.sounds import play_unlock
            play_unlock()
            self.show_main()
        else:
            if self.pin_window:
                self.pin_window.show_error()

    def show_main(self):
        from ui.main_window import MainWindow
        if self.vault and self.vault.is_unlocked():
            self.main_window = MainWindow(self.settings, self.vault)
            self.main_window.show()
            self.pin_window = None  # setup is done; next reopen → unlock screen

    def run(self):
        return self.app.exec()

if __name__ == "__main__":
    passai = PassAI()
    sys.exit(passai.run())
