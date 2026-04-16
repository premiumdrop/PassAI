# passai/ui/toast.py — Premium Toasts · Slide-in from right · Gray 900

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint,
    QPropertyAnimation, QParallelAnimationGroup, QEasingCurve,
    pyqtSignal
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont
from typing import List, Optional


# ── Toast type palette ────────────────────────────────────────────────────────

_STYLES = {
    "success": {
        "bg":     QColor(16, 26, 18),
        "border": QColor(102, 187, 106, 180),
        "dot":    QColor(102, 187, 106),
        "text":   "#A5D6A7",
    },
    "error": {
        "bg":     QColor(28, 14, 14),
        "border": QColor(239, 83, 80, 180),
        "dot":    QColor(239, 83, 80),
        "text":   "#EF9A9A",
    },
    "warning": {
        "bg":     QColor(26, 18, 8),
        "border": QColor(255, 167, 38, 180),
        "dot":    QColor(255, 167, 38),
        "text":   "#FFE082",
    },
    "info": {
        "bg":     QColor(12, 20, 32),
        "border": QColor(66, 165, 245, 180),
        "dot":    QColor(66, 165, 245),
        "text":   "#90CAF9",
    },
}

_TOAST_HEIGHT  = 44
_TOAST_MIN_W   = 200
_MARGIN_RIGHT  = 22
_MARGIN_BOTTOM = 24   # anchored to bottom-right
_SPACING       = 10


# ── Single Toast ──────────────────────────────────────────────────────────────

class Toast(QWidget):
    """Compact, elegant notification — slides in from right, fades out."""

    finished = pyqtSignal()

    def __init__(self, message: str, toast_type: str = "info", parent=None):
        super().__init__(parent)
        self._s = _STYLES.get(toast_type, _STYLES["info"])

        # Child widget — no special window flags
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._build_ui(message)
        self._add_shadow()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self, message: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 18, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Color dot
        dot = QLabel("●")
        dot.setFixedWidth(10)
        dot.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        dot.setStyleSheet(
            f"color: {self._s['dot'].name()}; font-size: 9px; background: transparent;"
        )
        layout.addWidget(dot)

        # Message
        lbl = QLabel(message)
        lbl.setWordWrap(False)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(
            f"color: {self._s['text']}; font-size: 13px; font-weight: 500; "
            f"background: transparent; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        layout.addWidget(lbl)

        lbl.adjustSize()
        w = max(lbl.sizeHint().width() + 56, _TOAST_MIN_W)
        self.setFixedSize(w, _TOAST_HEIGHT)

    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 130))
        shadow.setOffset(0, 6)
        # Note: can't set both shadow + opacity on same widget in Qt
        # Shadow is applied to the parent wrapper if needed; skip for now
        # to avoid double-effect conflict. The border + bg convey depth.

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(r.x(), r.y(), r.width(), r.height(), 10, 10)

        # Background
        p.setBrush(self._s["bg"])
        p.drawPath(path)

        # Border
        border = QPainterPath()
        border.addRoundedRect(0.5, 0.5, r.width() - 1, r.height() - 1, 10, 10)
        p.setPen(self._s["border"])
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(border)

        # Left accent bar
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._s["dot"])
        bar = QPainterPath()
        bar.addRoundedRect(0, 6, 3, r.height() - 12, 1, 1)
        p.drawPath(bar)

        p.end()

    # ── Animations ────────────────────────────────────────────────────────────

    def show_animated(self, x: int, y: int):
        """Slide in from right + fade in."""
        self.move(x + 30, y)
        self.show()
        self.raise_()

        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(260)
        pos_anim.setStartValue(QPoint(x + 30, y))
        pos_anim.setEndValue(QPoint(x, y))
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_anim.setDuration(200)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._show_group = QParallelAnimationGroup(self)
        self._show_group.addAnimation(pos_anim)
        self._show_group.addAnimation(fade_anim)
        self._show_group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)

        QTimer.singleShot(3000, self._begin_hide)

    def _begin_hide(self):
        if not self.isVisible():
            return

        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self._on_done)
        fade_out.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._hide_anim = fade_out

    def _on_done(self):
        self.hide()
        self.finished.emit()
        self.deleteLater()


# ── Toast Manager ─────────────────────────────────────────────────────────────

class ToastManager:
    """Singleton managing a bottom-right stack of toast notifications."""

    _instance: Optional["ToastManager"] = None

    def __init__(self):
        self.active: List[Toast] = []
        self.parent_widget: Optional[QWidget] = None

    @classmethod
    def _inst(cls) -> "ToastManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_parent(cls, widget: QWidget):
        cls._inst().parent_widget = widget

    @classmethod
    def show(cls, message: str, toast_type: str = "info"):
        inst = cls._inst()
        if not inst.parent_widget:
            print(f"[Toast] {toast_type.upper()}: {message}")
            return
        inst._spawn(message, toast_type)

    def _spawn(self, message: str, toast_type: str):
        toast = Toast(message, toast_type, self.parent_widget)
        toast.finished.connect(lambda t=toast: self._on_done(t))
        self.active.append(toast)
        x, y = self._calc_pos(toast)
        toast.show_animated(x, y)

    def _calc_pos(self, new_toast: Toast) -> tuple[int, int]:
        pw = self.parent_widget
        x = pw.width() - new_toast.width() - _MARGIN_RIGHT
        # Stack upward from bottom
        y = pw.height() - _MARGIN_BOTTOM - _TOAST_HEIGHT
        for t in self.active:
            if t is not new_toast and t.isVisible():
                y -= (_TOAST_HEIGHT + _SPACING)
        y = max(50, y)
        return x, y

    def _on_done(self, toast: Toast):
        if toast in self.active:
            self.active.remove(toast)
        self._restack()

    def _restack(self):
        if not self.parent_widget:
            return
        pw = self.parent_widget
        y = pw.height() - _MARGIN_BOTTOM - _TOAST_HEIGHT
        for t in reversed(self.active):
            if t and t.isVisible():
                x = pw.width() - t.width() - _MARGIN_RIGHT
                anim = QPropertyAnimation(t, b"pos")
                anim.setDuration(220)
                anim.setStartValue(t.pos())
                anim.setEndValue(QPoint(x, y))
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
                t._restack_anim = anim
                y -= (_TOAST_HEIGHT + _SPACING)


# ── Convenience helpers ───────────────────────────────────────────────────────

def show_success(message: str): ToastManager.show(message, "success")
def show_info(message: str):    ToastManager.show(message, "info")
def show_warning(message: str): ToastManager.show(message, "warning")
def show_error(message: str):   ToastManager.show(message, "error")
