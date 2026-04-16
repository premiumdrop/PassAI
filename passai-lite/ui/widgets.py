# passai/ui/widgets.py — Premium Gray Edition
# Dead code removed: BlurOverlay, ToastNotification, RoundButton

from pathlib import Path
from PyQt6.QtWidgets import QPushButton, QLineEdit, QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import (Qt, pyqtSignal, QPropertyAnimation, QEasingCurve,
                          QTimer, pyqtProperty, QRect, QRectF, QPointF)
from PyQt6.QtGui import (QPainter, QColor, QPen, QPainterPath, QLinearGradient,
                         QRadialGradient, QFont, QPixmap, QBrush)


# ── Icon drawing helpers ───────────────────────────────────────────────────────

class Icons:
    """
    Pure QPainter icon set — no emoji, no external images.
    All icons are geometric and scale cleanly at any size.
    """

    @staticmethod
    def draw_lock(p: QPainter, cx: float, cy: float, size: float,
                  color: QColor) -> None:
        """Minimal padlock — body + shackle arc."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bw = size * 0.68
        bh = size * 0.50
        bx = cx - bw / 2
        by = cy - bh * 0.05

        # Body
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        body = QPainterPath()
        body.addRoundedRect(QRectF(bx, by, bw, bh), 3, 3)
        p.drawPath(body)

        # Shackle (upper arc)
        sw  = size * 0.40
        sh  = size * 0.48
        sx  = cx - sw / 2
        sy  = cy - sh * 0.80
        pen = QPen(color, size * 0.13)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(sx, sy, sw, sh), 0, 180 * 16)

        # Keyhole dot
        p.setPen(Qt.PenStyle.NoPen)
        khole_color = QColor(color)
        khole_color.setAlpha(60)
        p.setBrush(khole_color)
        r = size * 0.065
        p.drawEllipse(QPointF(cx, by + bh * 0.42), r, r)

    @staticmethod
    def draw_eye(p: QPainter, cx: float, cy: float, size: float,
                 color: QColor) -> None:
        """Simple eye icon — almond shape with pupil."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ew  = size * 0.80
        eh  = size * 0.46
        pen = QPen(color, size * 0.11)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Almond outline
        eye_path = QPainterPath()
        eye_path.moveTo(cx - ew / 2, cy)
        eye_path.quadTo(cx, cy - eh,       cx + ew / 2, cy)
        eye_path.quadTo(cx, cy + eh,       cx - ew / 2, cy)
        p.drawPath(eye_path)
        # Pupil
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        pr = size * 0.13
        p.drawEllipse(QPointF(cx, cy), pr, pr)

    @staticmethod
    def draw_search(p: QPainter, cx: float, cy: float, size: float,
                    color: QColor) -> None:
        """Magnifying glass."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cr  = size * 0.30
        ccx = cx - size * 0.08
        ccy = cy - size * 0.08
        pen = QPen(color, size * 0.12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(ccx, ccy), cr, cr)
        # Handle
        hx1 = ccx + cr * 0.70
        hy1 = ccy + cr * 0.70
        p.drawLine(QPointF(hx1, hy1),
                   QPointF(cx + size * 0.34, cy + size * 0.34))

    @staticmethod
    def draw_key(p: QPainter, cx: float, cy: float, size: float,
                 color: QColor) -> None:
        """Simple key — circle head + rectangular shaft with teeth."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        # Head (circle with hole)
        head_r  = size * 0.28
        head_cx = cx - size * 0.14
        p.drawEllipse(QPointF(head_cx, cy), head_r, head_r)
        # Hole
        hole_color = QColor(0, 0, 0, 100)
        p.setBrush(hole_color)
        p.drawEllipse(QPointF(head_cx, cy), head_r * 0.44, head_r * 0.44)
        # Shaft
        p.setBrush(color)
        shaft_x = head_cx + head_r * 0.65
        shaft_w = size * 0.52
        shaft_h = size * 0.15
        p.drawRoundedRect(
            QRectF(shaft_x, cy - shaft_h / 2, shaft_w, shaft_h), 2, 2
        )
        # Teeth (2 small notches)
        tooth_w = shaft_h * 0.50
        tooth_h = shaft_h * 0.60
        for offset in (shaft_w * 0.45, shaft_w * 0.68):
            p.drawRect(QRectF(
                shaft_x + offset, cy + shaft_h / 2, tooth_w, tooth_h
            ))

    @staticmethod
    def draw_plus(p: QPainter, cx: float, cy: float, size: float,
                  color: QColor) -> None:
        """Plus/add icon."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, size * 0.14)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        half = size * 0.34
        p.drawLine(QPointF(cx - half, cy), QPointF(cx + half, cy))
        p.drawLine(QPointF(cx, cy - half), QPointF(cx, cy + half))

    @staticmethod
    def draw_shield(p: QPainter, cx: float, cy: float, size: float,
                    color: QColor) -> None:
        """Shield icon — clean security symbol."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        w = size * 0.70
        h = size * 0.80
        x = cx - w / 2
        y = cy - h / 2
        path = QPainterPath()
        path.moveTo(cx, y)
        path.lineTo(x + w, y + h * 0.28)
        path.quadTo(x + w, y + h * 0.82, cx, y + h)
        path.quadTo(x, y + h * 0.82, x, y + h * 0.28)
        path.closeSubpath()
        p.drawPath(path)


# ── Traffic Light Buttons ──────────────────────────────────────────────────────

class TrafficLightButton(QPushButton):
    """macOS-style window control button."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color   = QColor(color)
        self.hovered = False
        self.setFixedSize(12, 12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        if self.hovered:
            glow = QColor(self.color)
            glow.setAlpha(50)
            p.setBrush(glow)
            p.drawEllipse(-3, -3, 18, 18)
        p.setBrush(self.color)
        p.drawEllipse(0, 0, 12, 12)
        p.end()


# ── Password Line Edit ─────────────────────────────────────────────────────────

class PasswordLineEdit(QLineEdit):
    """Password input with toggle visibility."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.is_visible = False

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setEchoMode(
            QLineEdit.EchoMode.Normal if self.is_visible
            else QLineEdit.EchoMode.Password
        )


# ── Eye Button (drawn icon, no emoji) ────────────────────────────────────────

class EyeButton(QPushButton):
    """Toggle password visibility — drawn eye, no emoji."""

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hovered = False
        self.setStyleSheet("background: transparent; border: none;")

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        color = QColor("#BDBDBD") if self.hovered else QColor("#757575")
        Icons.draw_eye(p, self.width() / 2, self.height() / 2, 18, color)
        p.end()


# ── Premium Strength Meter ─────────────────────────────────────────────────────

class StrengthMeter(QWidget):
    """Animated password-strength bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._strength = 0.0
        self.color     = QColor("#424242")

        self._anim = QPropertyAnimation(self, b"strength_val")
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(lambda: self.update())

    def get_strength_val(self):  return self._strength
    def set_strength_val(self, v): self._strength = v; self.update()

    strength_val = pyqtProperty(float, get_strength_val, set_strength_val)

    def set_strength(self, score: int):
        self._anim.stop()
        self._anim.setStartValue(float(self._strength))
        self._anim.setEndValue(float(score))
        self._anim.start()
        if   score < 25: self.color = QColor("#EF5350")
        elif score < 50: self.color = QColor("#FFA726")
        elif score < 75: self.color = QColor("#FFEE58")
        elif score < 90: self.color = QColor("#66BB6A")
        else:            self.color = QColor("#43A047")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = self.height() // 2
        # Track
        p.setBrush(QColor("#282828"))
        track = QPainterPath()
        track.addRoundedRect(0, 0, self.width(), self.height(), r, r)
        p.drawPath(track)
        # Fill
        if self._strength > 0:
            fw = max(self.height(), int(self.width() * self._strength / 100))
            grad = QLinearGradient(0, 0, fw, 0)
            grad.setColorAt(0, self.color.darker(140))
            grad.setColorAt(1, self.color)
            p.setBrush(QBrush(grad))
            fill = QPainterPath()
            fill.addRoundedRect(0, 0, fw, self.height(), r, r)
            p.drawPath(fill)


# ── Search Box ────────────────────────────────────────────────────────────────

class SearchBox(QLineEdit):
    """Search input with drawn magnify icon — no emoji."""

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(38)
        self.setMaximumHeight(38)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1c1c1c;
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 0 12px 0 36px;
                color: #FFFFFF;
                font-size: 13px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QLineEdit:focus {
                border-color: #757575;
                background-color: #1e1e1e;
            }
            QLineEdit::placeholder-text { color: #424242; }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        Icons.draw_search(p, 16, self.height() / 2, 16, QColor("#424242"))
        p.end()


# ── Entry Card ────────────────────────────────────────────────────────────────

class EntryCard(QWidget):
    """
    Password entry row — minimal, animated hover/selection.
    Selected: thin white left bar + elevated background.
    """

    clicked = pyqtSignal(int)

    _C_DEFAULT  = QColor("#212121")
    _C_HOVER    = QColor("#282828")
    _C_SELECTED = QColor("#2a2a2a")
    _ACCENT_BAR = QColor("#FFFFFF")

    def __init__(self, entry_id: int, icon_path: str, title: str,
                 username: str, favorite: bool, parent=None):
        super().__init__(parent)
        self.entry_id    = entry_id
        self.is_selected = False
        self._bg         = QColor(self._C_DEFAULT)

        self.setMinimumHeight(60)
        self.setMaximumHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._anim = QPropertyAnimation(self, b"bgColor")
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 14, 10)
        layout.setSpacing(12)

        icon_widget = self._build_icon(icon_path, title)
        layout.addWidget(icon_widget)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            "font-weight: 600; font-size: 13px; color: #FFFFFF; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        text_col.addWidget(self.title_lbl)

        disp_user = username if len(username) <= 26 else username[:23] + "…"
        self.user_lbl = QLabel(disp_user)
        self.user_lbl.setStyleSheet(
            "font-size: 11px; color: #616161; background: transparent; "
            "font-family: 'Segoe UI', Arial;"
        )
        text_col.addWidget(self.user_lbl)
        layout.addLayout(text_col, 1)

        if favorite:
            star = QLabel("★")
            star.setStyleSheet(
                "color: #FFA726; font-size: 11px; background: transparent;"
            )
            layout.addWidget(star)

    def _build_icon(self, icon_path: str, title: str) -> QWidget:
        if icon_path and Path(icon_path).exists():
            lbl = QLabel()
            pix = QPixmap(str(icon_path)).scaled(
                30, 30,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl.setPixmap(pix)
            lbl.setFixedSize(32, 32)
            return lbl
        if icon_path and not Path(icon_path).exists():
            # Emoji service icon fallback
            lbl = QLabel(icon_path)
            lbl.setStyleSheet("font-size: 20px; background: transparent;")
            lbl.setFixedSize(32, 32)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return lbl
        return _LetterAvatar(title[0].upper() if title else "?")

    @pyqtProperty(QColor)
    def bgColor(self): return self._bg

    @bgColor.setter
    def bgColor(self, c: QColor):
        self._bg = c
        self._sync_label_colors()
        self.update()

    def _sync_label_colors(self):
        sel = self.is_selected
        self.title_lbl.setStyleSheet(
            f"font-weight: 600; font-size: 13px; background: transparent; "
            f"color: {'#FFFFFF' if sel else '#DEDEDE'}; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        self.user_lbl.setStyleSheet(
            f"font-size: 11px; background: transparent; "
            f"color: {'#757575' if sel else '#616161'};"
        )

    def set_selected(self, selected: bool):
        self.is_selected = selected
        target = self._C_SELECTED if selected else self._C_DEFAULT
        self._anim.stop()
        self._anim.setStartValue(QColor(self._bg))
        self._anim.setEndValue(QColor(target))
        self._anim.start()
        self._sync_label_colors()

    def enterEvent(self, event):
        if not self.is_selected:
            self._anim.stop()
            self._anim.setStartValue(QColor(self._bg))
            self._anim.setEndValue(QColor(self._C_HOVER))
            self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_selected:
            self._anim.stop()
            self._anim.setStartValue(QColor(self._bg))
            self._anim.setEndValue(QColor(self._C_DEFAULT))
            self._anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._bg)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
        p.drawPath(path)
        if self.is_selected:
            p.setBrush(self._ACCENT_BAR)
            bar = QPainterPath()
            bar.addRoundedRect(QRectF(0, 10, 2, self.height() - 20), 1, 1)
            p.drawPath(bar)
        p.end()

    def set_icon(self, icon_path: str) -> None:
        """Replace the icon widget after an async background fetch completes."""
        layout = self.layout()
        item = layout.takeAt(0)
        if item and item.widget():
            item.widget().deleteLater()
        new_icon = self._build_icon(icon_path, self.title_lbl.text())
        layout.insertWidget(0, new_icon)

    def mousePressEvent(self, event):
        from ui.sounds import play_click
        play_click()
        self.clicked.emit(self.entry_id)
        super().mousePressEvent(event)


# ── Letter Avatar ─────────────────────────────────────────────────────────────

class _LetterAvatar(QWidget):
    """Circular avatar with first letter — neutral palette."""

    _COLORS = [
        ("#757575", "#424242"),  # Gray
        ("#4DB6AC", "#00695C"),  # Teal
        ("#7986CB", "#3949AB"),  # Indigo
        ("#4FC3F7", "#0277BD"),  # Blue
        ("#81C784", "#2E7D32"),  # Green
        ("#FFB74D", "#E65100"),  # Orange
    ]

    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter.upper()
        idx = (ord(letter.upper()) - 65) % len(self._COLORS) if letter.isalpha() else 0
        self.fg, self.bg_dark = self._COLORS[idx]
        self.setFixedSize(32, 32)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        grad = QRadialGradient(16, 16, 16)
        grad.setColorAt(0, QColor(self.fg))
        grad.setColorAt(1, QColor(self.bg_dark))
        p.setBrush(QBrush(grad))
        p.drawEllipse(0, 0, 32, 32)
        p.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI Variable", 13, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(QRect(0, 0, 32, 32), Qt.AlignmentFlag.AlignCenter, self.letter)
        p.end()
