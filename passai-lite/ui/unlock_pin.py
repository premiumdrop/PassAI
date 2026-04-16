"""PassAI — Unlock PIN Screen · Keyboard-only · Gray 900"""

from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer,
    QPropertyAnimation, QEasingCurve, pyqtProperty
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPainter, QPainterPath,
    QRegion, QLinearGradient, QBrush
)

from ui.widgets import Icons


class PINSlot(QWidget):
    """Thin horizontal bar — animates from dark (empty) to white (filled)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill = 0.0
        self.setFixedSize(40, 4)

        self._anim = QPropertyAnimation(self, b"fill")
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    @pyqtProperty(float)
    def fill(self):
        return self._fill

    @fill.setter
    def fill(self, v: float):
        self._fill = max(0.0, min(1.0, v))
        self.update()

    def set_filled(self, filled: bool, animate: bool = True):
        target = 1.0 if filled else 0.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._fill)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._fill = target
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = self.rect()

        # Track
        p.setBrush(QColor("#282828"))
        p.drawRoundedRect(r, 2, 2)

        # Animated fill — dark gray → white
        if self._fill > 0.001:
            v = int(0x28 + (0xFF - 0x28) * self._fill)
            p.setBrush(QColor(v, v, v))
            fill_w = max(4, int(r.width() * self._fill))
            p.drawRoundedRect(r.x(), r.y(), fill_w, r.height(), 2, 2)

        p.end()


class _LockIcon(QWidget):
    """Painted lock icon — no emoji."""

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


class UnlockPINWindow(QWidget):
    pin_entered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.pin_value = ""
        self.setWindowTitle("PassAI")
        self.setFixedSize(360, 420)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        _icon = Path(__file__).parent.parent / "assets" / "icons" / "icon.ico"
        if _icon.exists():
            self.setWindowIcon(QIcon(str(_icon)))

        self._setup_ui()
        self._center()
        self._apply_mask()

    # ── Window setup ──────────────────────────────────────────────────────────

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

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Background gradient
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1c1c1c"))
        grad.setColorAt(1.0, QColor("#0f0f0f"))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

        # Subtle border
        border_path = QPainterPath()
        border_path.addRoundedRect(0.5, 0.5, self.width() - 1, self.height() - 1, 20, 20)
        p.setPen(QColor("#242424"))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(border_path)

        p.end()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(52, 56, 52, 52)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wordmark
        wordmark = QLabel("PASSAI")
        wordmark.setFont(QFont("Segoe UI Variable", 9, QFont.Weight.DemiBold))
        wordmark.setStyleSheet("color: #3a3a3a; background: transparent; letter-spacing: 5px;")
        wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(wordmark)

        layout.addSpacing(30)

        # Lock icon
        lock_icon = _LockIcon(38)
        layout.addWidget(lock_icon, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(20)

        # Title
        title = QLabel("Welcome back")
        title.setFont(QFont("Segoe UI Variable", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(7)

        # Subtitle
        subtitle = QLabel("Enter your PIN")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #616161; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(42)

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

        layout.addSpacing(16)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setFont(QFont("Segoe UI", 11))
        self.error_label.setStyleSheet("color: #EF5350; background: transparent;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setFixedHeight(20)
        layout.addWidget(self.error_label)

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
            play_tick()
            if len(self.pin_value) == 4:
                QTimer.singleShot(120, self._submit)

    def _backspace(self):
        from ui.sounds import play_click
        if self.pin_value:
            self.pin_value = self.pin_value[:-1]
            self._update_display()
            self.error_label.setText("")
            play_click()

    def _clear(self):
        self.pin_value = ""
        for slot in self.slots:
            slot.set_filled(False)
        self.error_label.setText("")

    def _update_display(self):
        for i, slot in enumerate(self.slots):
            slot.set_filled(i < len(self.pin_value))

    def _submit(self):
        if len(self.pin_value) == 4:
            self.pin_entered.emit(self.pin_value)

    def show_error(self):
        from ui.sounds import play_error
        from ui.animations import AnimationHelper
        play_error()
        self.error_label.setText("Incorrect PIN — try again")
        QTimer.singleShot(80, lambda: AnimationHelper.shake(self, intensity=11))
        QTimer.singleShot(2200, self._clear)

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
        AnimationHelper.window_fade_in(self, duration=220)
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
            self._clear()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if len(self.pin_value) == 4:
                self._submit()
