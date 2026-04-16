"""PassAI — Setup PIN Window · Gray 900"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPainter, QPainterPath, QRegion,
    QLinearGradient, QBrush
)

from ui.widgets import Icons
from ui.unlock_pin import PINSlot


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


class SetupPINWindow(QWidget):
    pin_created = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.pin_value = ""
        self.setWindowTitle("PassAI — Create PIN")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 430)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
        title = QLabel("Create Your PIN")
        title.setFont(QFont("Segoe UI Variable", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(7)

        subtitle = QLabel("Used for quick unlock every time you open PassAI")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #616161; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(38)

        # PIN slot row
        slots_row = QHBoxLayout()
        slots_row.setSpacing(14)
        slots_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slots = []
        for _ in range(4):
            slot = PINSlot()
            slots_row.addWidget(slot)
            self.slots.append(slot)
        layout.addLayout(slots_row)

        layout.addSpacing(14)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setFont(QFont("Segoe UI", 11))
        self.error_label.setStyleSheet("color: #EF5350; background: transparent;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setFixedHeight(20)
        layout.addWidget(self.error_label)

        layout.addSpacing(26)

        # Set PIN button — white CTA
        self.create_btn = QPushButton("Set PIN")
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
            QPushButton:hover   { background-color: #F0F0F0; }
            QPushButton:pressed { background-color: #DEDEDE; }
        """)
        self.create_btn.clicked.connect(self._handle_create)
        layout.addWidget(self.create_btn)

        layout.addStretch()

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

    # ── PIN logic ─────────────────────────────────────────────────────────────

    def _add_digit(self, digit: int):
        from ui.sounds import play_tick
        if len(self.pin_value) < 4:
            self.pin_value += str(digit)
            self._update_display()
            self.error_label.setText("")
            play_tick()

    def _backspace(self):
        from ui.sounds import play_click
        if self.pin_value:
            self.pin_value = self.pin_value[:-1]
            self._update_display()
            self.error_label.setText("")
            play_click()

    def _reset(self):
        self.pin_value = ""
        for slot in self.slots:
            slot.set_filled(False)
        self.error_label.setText("")

    def _update_display(self):
        for i, slot in enumerate(self.slots):
            slot.set_filled(i < len(self.pin_value))

    def _handle_create(self):
        from ui.sounds import play_click, play_success, play_error
        play_click()
        pin = self.pin_value
        if len(pin) != 4:
            play_error()
            self.error_label.setText("  PIN must be exactly 4 digits")
            return
        if not pin.isdigit():
            play_error()
            self.error_label.setText("  Only digits allowed")
            return
        play_success()
        self.pin_created.emit(pin)

    # ── Events ────────────────────────────────────────────────────────────────

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
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            self._add_digit(key - Qt.Key.Key_0)
        elif key == Qt.Key.Key_Backspace:
            self._backspace()
        elif key == Qt.Key.Key_Escape:
            self._reset()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if len(self.pin_value) == 4:
                self._handle_create()
