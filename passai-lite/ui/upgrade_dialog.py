"""PassAI Lite — Premium Upgrade Dialog"""

import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath

UPGRADE_URL = "https://micflic.gumroad.com/l/passai"

_SHADOW = 22
_CARD_W = 420
_CARD_H = 444
_W, _H  = _CARD_W + 2 * _SHADOW, _CARD_H + 2 * _SHADOW

_QSS = """
    QDialog { background: transparent; }
    QLabel {
        background: transparent;
        font-family: "Segoe UI Variable", "Segoe UI", Arial;
    }
"""


# ── Card surface ──────────────────────────────────────────────────────────────

class _Card(QWidget):
    """Rounded #181818 card — same pattern as AddEditDialog."""
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 18, 18)
        p.setBrush(QColor("#181818"))
        p.drawPath(path)

        # 1 px subtle border
        p.setPen(QColor(52, 52, 52, 90))
        p.setBrush(Qt.BrushStyle.NoBrush)
        b = QPainterPath()
        b.addRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 17.5, 17.5)
        p.drawPath(b)

        p.end()


# ── Icon widget ───────────────────────────────────────────────────────────────

class _StarIcon(QWidget):
    """Painted ✦ / crown-like icon using a simple diamond + dot motif."""
    def __init__(self, size: int = 44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.width()
        cx, cy = s / 2, s / 2
        r = s * 0.38

        # Outer ring
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 12))
        p.drawEllipse(int(cx - r * 1.35), int(cy - r * 1.35),
                      int(r * 2.7), int(r * 2.7))

        # Inner fill
        p.setBrush(QColor(255, 255, 255, 20))
        p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # Four-point star shape
        from PyQt6.QtCore import QPointF
        star = QPainterPath()
        pts = [
            QPointF(cx,      cy - r),
            QPointF(cx + r * 0.26, cy - r * 0.26),
            QPointF(cx + r,  cy),
            QPointF(cx + r * 0.26, cy + r * 0.26),
            QPointF(cx,      cy + r),
            QPointF(cx - r * 0.26, cy + r * 0.26),
            QPointF(cx - r,  cy),
            QPointF(cx - r * 0.26, cy - r * 0.26),
        ]
        star.moveTo(pts[0])
        for pt in pts[1:]:
            star.lineTo(pt)
        star.closeSubpath()
        p.setBrush(QColor("#FFFFFF"))
        p.drawPath(star)

        p.end()


# ── Upgrade Dialog ────────────────────────────────────────────────────────────

class UpgradeDialog(QDialog):
    """
    Premium upgrade prompt shown when a Lite-edition limit is hit.
    Identical shadow/compositing setup to AddEditDialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(_W, _H)
        self.setStyleSheet(_QSS)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(_SHADOW, _SHADOW, _SHADOW, _SHADOW)
        outer.setSpacing(0)

        self._card = _Card()
        self._card.setFixedSize(_CARD_W, _CARD_H)

        eff = QGraphicsDropShadowEffect(self._card)
        eff.setBlurRadius(32)
        eff.setColor(QColor(0, 0, 0, 150))
        eff.setOffset(0, 10)
        self._card.setGraphicsEffect(eff)

        outer.addWidget(self._card)
        self._build_ui()

    # ── Chrome ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.end()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self._card)
        root.setContentsMargins(36, 22, 36, 28)
        root.setSpacing(0)

        # Close
        close_row = QHBoxLayout()
        close_row.addStretch()
        close = QPushButton("×")
        close.setFixedSize(28, 28)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setAutoDefault(False)
        close.setDefault(False)
        close.clicked.connect(self.reject)
        close.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #3a3a3a; font-size: 22px; padding-bottom: 3px;
            }
            QPushButton:hover { color: #FFFFFF; }
        """)
        close_row.addWidget(close)
        root.addLayout(close_row)
        root.addSpacing(8)

        # Icon
        icon = _StarIcon(40)
        root.addWidget(icon, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addSpacing(14)

        # Title
        title = QLabel("Unlock the full vault")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #FFFFFF; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        root.addWidget(title)
        root.addSpacing(8)

        # Subtitle
        sub = QLabel("You've reached the limit of the Lite version.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size: 13px; color: #757575;")
        root.addWidget(sub)
        root.addSpacing(20)

        # Features box — use objectName so the border only applies to the
        # container itself, not to every QLabel child inside it.
        box = QWidget()
        box.setObjectName("featureBox")
        box.setStyleSheet("""
            #featureBox {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 12px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        bL = QVBoxLayout(box)
        bL.setContentsMargins(18, 14, 18, 14)
        bL.setSpacing(10)

        hdr = QLabel("WHAT YOU GET WITH PRO")
        hdr.setStyleSheet(
            "font-size: 9px; font-weight: 700; color: #555555; "
            "letter-spacing: 1.2px;"
        )
        bL.addWidget(hdr)

        for feat in (
            "Unlimited passwords",
            "Recovery Key restore",
            "Full premium experience",
        ):
            row = QHBoxLayout()
            row.setSpacing(10)
            row.setContentsMargins(0, 0, 0, 0)

            dot = QLabel("✓")
            dot.setFixedSize(18, 18)
            dot.setAlignment(
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
            )
            dot.setStyleSheet(
                "color: #66BB6A; font-size: 12px; font-weight: 700;"
            )
            row.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

            lbl = QLabel(feat)
            lbl.setStyleSheet("font-size: 13px; color: #C8C8C8;")
            row.addWidget(lbl, 1)

            bL.addLayout(row)

        root.addWidget(box)
        root.addSpacing(13)

        # Payment note
        note = QLabel("One-time payment · No subscription")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("font-size: 11px; color: #525252;")
        root.addWidget(note)
        root.addSpacing(20)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        upgrade = QPushButton("Upgrade Now")
        upgrade.setFixedHeight(44)
        upgrade.setCursor(Qt.CursorShape.PointingHandCursor)
        upgrade.setAutoDefault(False)
        upgrade.setDefault(False)
        upgrade.clicked.connect(self._do_upgrade)
        upgrade.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                border-radius: 10px;
                color: #121212;
                font-size: 14px;
                font-weight: 700;
                padding: 0 28px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QPushButton:hover   { background-color: #F0F0F0; }
            QPushButton:pressed { background-color: #DEDEDE; }
        """)
        btn_row.addWidget(upgrade, 1)

        later = QPushButton("Maybe Later")
        later.setFixedHeight(44)
        later.setCursor(Qt.CursorShape.PointingHandCursor)
        later.setAutoDefault(False)
        later.setDefault(False)
        later.clicked.connect(self.reject)
        later.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #262626;
                border-radius: 10px;
                color: #424242;
                font-size: 13px;
                font-weight: 500;
                padding: 0 20px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QPushButton:hover {
                border-color: #3a3a3a;
                color: #757575;
                background-color: rgba(255, 255, 255, 0.025);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        btn_row.addWidget(later)

        root.addLayout(btn_row)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _do_upgrade(self):
        webbrowser.open(UPGRADE_URL)
        self.accept()
