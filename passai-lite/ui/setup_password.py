"""PassAI — Setup Master Password Window · Gray 900"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont, QIcon, QPainterPath, QRegion, QColor,
    QPainter, QLinearGradient, QBrush
)

from ui.widgets import Icons


class _LockIcon(QWidget):
    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        half = self._sz // 2
        Icons.draw_lock(p, half, half, int(self._sz * 0.68), QColor("#424242"))
        p.end()


class SetupPasswordWindow(QWidget):
    password_created = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassAI — Create Vault")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 500)

        _icon = Path(__file__).parent.parent / "assets" / "icons" / "icon.ico"
        if _icon.exists():
            self.setWindowIcon(QIcon(str(_icon)))

        self._setup_ui()
        self._center()
        self._apply_mask()

    def _apply_mask(self):
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _center(self):
        geo = QApplication.primaryScreen().geometry()
        self.move(
            (geo.width()  - self.width())  // 2,
            (geo.height() - self.height()) // 2,
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1c1c1c"))
        grad.setColorAt(1.0, QColor("#0f0f0f"))
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        border_path = QPainterPath()
        border_path.addRoundedRect(0.5, 0.5, self.width() - 1, self.height() - 1, 20, 20)
        p.setPen(QColor("#242424"))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(border_path)

        p.end()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(44, 52, 44, 44)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wordmark
        wordmark = QLabel("PASSAI")
        wordmark.setFont(QFont("Segoe UI Variable", 9, QFont.Weight.DemiBold))
        wordmark.setStyleSheet("color: #3a3a3a; background: transparent; letter-spacing: 5px;")
        wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(wordmark)

        layout.addSpacing(28)

        # Lock icon
        lock_icon = _LockIcon(38)
        layout.addWidget(lock_icon, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(20)

        # Title
        title = QLabel("Create Your Vault")
        title.setFont(QFont("Segoe UI Variable", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(7)

        subtitle = QLabel("Your master password protects all saved credentials")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #616161; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(34)

        # Input style
        field_style = """
            QLineEdit {
                background-color: #1c1c1c;
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 13px 15px;
                color: #FFFFFF;
                font-size: 14px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
                selection-background-color: #424242;
            }
            QLineEdit:focus {
                border-color: #757575;
                background-color: #1e1e1e;
            }
        """

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Master Password")
        self.password_input.setFixedHeight(50)
        self.password_input.setStyleSheet(field_style)
        self.password_input.returnPressed.connect(self._handle_create)
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setFixedHeight(50)
        self.confirm_input.setStyleSheet(field_style)
        self.confirm_input.returnPressed.connect(self._handle_create)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(22)

        # Create button — white CTA
        self.create_btn = QPushButton("Create Vault")
        self.create_btn.setFont(QFont("Segoe UI Variable", 14, QFont.Weight.Bold))
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.setFixedHeight(50)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                border-radius: 8px;
                color: #121212;
                font-size: 14px;
                font-weight: 700;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QPushButton:hover  { background-color: #F0F0F0; }
            QPushButton:pressed { background-color: #DEDEDE; }
        """)
        self.create_btn.clicked.connect(self._handle_create)
        layout.addWidget(self.create_btn)

        layout.addSpacing(12)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setFont(QFont("Segoe UI", 11))
        self.error_label.setStyleSheet("color: #EF5350; background: transparent;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setFixedHeight(20)
        layout.addWidget(self.error_label)

        layout.addStretch()
        self.password_input.setFocus()

        # ── Close button (top-left, floating) ─────────────────────────────────
        close_btn = QPushButton("×", self)
        close_btn.setFixedSize(32, 32)
        close_btn.move(12, 12)
        close_btn.raise_()
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(QApplication.instance().quit)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #3a3a3a; font-size: 24px;
                padding-bottom: 2px; border-radius: 5px;
            }
            QPushButton:hover {
                color: #9e9e9e;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QPushButton:pressed { color: #FFFFFF; }
        """)

        # ── Version label (top-right, non-interactive) ────────────────────────
        ver = QLabel("1.0L", self)
        ver.setStyleSheet(
            "font-size: 9px; color: #2a2a2a; background: transparent; "
            "letter-spacing: 0.6px; font-family: 'Segoe UI Variable', 'Segoe UI', Arial;")
        ver.setFixedSize(28, 14)
        ver.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ver.move(self.width() - 38, 18)
        ver.raise_()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _handle_create(self):
        from ui.sounds import play_click
        play_click()
        pw      = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not pw:
            self._show_error("Password cannot be empty")
            return
        if len(pw) < 8:
            self._show_error("Password must be at least 8 characters")
            return
        if pw != confirm:
            self._show_error("Passwords do not match")
            return

        from ui.sounds import play_success
        play_success()
        self.error_label.setText("")
        self.password_created.emit(pw)

    def _show_error(self, msg: str):
        from ui.sounds import play_error
        play_error()
        self.error_label.setText(f"  {msg}")
        self.password_input.clear()
        self.confirm_input.clear()
        self.password_input.setFocus()

    def _force_taskbar_entry(self):
        """Force WS_EX_APPWINDOW so the window always appears on the taskbar."""
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style | 0x00040000) & ~0x00000080  # set APPWINDOW, clear TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._force_taskbar_entry()
        from ui.animations import AnimationHelper
        AnimationHelper.window_fade_in(self, duration=200)
        self.raise_()
        self.activateWindow()
