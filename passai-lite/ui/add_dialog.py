# passai/ui/add_dialog.py — Gray 900 Edition

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QCheckBox,
    QSpinBox, QCompleter, QWidget, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainterPath, QColor, QPainter
from ui.widgets import PasswordLineEdit, StrengthMeter, EyeButton
from core.generator import PasswordGenerator
from ui.toast import show_error, show_success, show_info

COMMON_SERVICES = [
    "Instagram", "Facebook", "Twitter", "TikTok", "Snapchat",
    "LinkedIn", "Reddit", "Discord", "Telegram", "WhatsApp",
    "Gmail", "Outlook", "Yahoo Mail", "ProtonMail", "iCloud",
    "Steam", "Epic Games", "Xbox", "PlayStation", "Nintendo",
    "Netflix", "Spotify", "YouTube", "Amazon Prime", "Disney+",
    "PayPal", "Venmo", "Amazon", "eBay", "Google", "Microsoft",
    "Apple", "Dropbox", "GitHub", "GitLab", "Slack", "Notion",
    "Figma", "Adobe", "Zoom", "Binance", "Coinbase",
]

# ── Base dialog stylesheet ────────────────────────────────────────────────────

_DIALOG_QSS = """
    QDialog {
        background: transparent;
    }
    QLabel {
        color: #BDBDBD;
        font-size: 13px;
        font-weight: 500;
        background: transparent;
        font-family: "Segoe UI Variable", "Segoe UI", Arial;
    }
    QLineEdit, QTextEdit {
        background-color: #1c1c1c;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 9px 13px;
        color: #FFFFFF;
        font-size: 14px;
        font-family: "Segoe UI Variable", "Segoe UI", Arial;
        selection-background-color: #424242;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #757575;
        background-color: #1e1e1e;
    }
    QCheckBox {
        color: #BDBDBD;
        font-size: 13px;
        spacing: 8px;
        font-family: "Segoe UI Variable", "Segoe UI", Arial;
    }
    QCheckBox::indicator {
        width: 17px; height: 17px;
        border-radius: 5px;
        border: 1px solid #282828;
        background: #1c1c1c;
    }
    QCheckBox::indicator:checked {
        background-color: #616161;
        border-color: #757575;
    }
    QCheckBox::indicator:hover {
        border-color: #616161;
    }
    QSpinBox {
        background-color: #1c1c1c;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 6px 10px;
        color: #FFFFFF;
        font-size: 14px;
        font-family: "Segoe UI Variable", "Segoe UI", Arial;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 18px; }
"""


_SHADOW = 22


class _Card(QWidget):
    """Visible card surface — paints its own rounded #181818 background."""
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.setBrush(QColor("#181818"))
        p.drawPath(path)
        p.end()


def _primary_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(42)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #FFFFFF;
            border: none;
            border-radius: 8px;
            color: #121212;
            font-size: 14px;
            font-weight: 700;
            padding: 0 24px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
        }
        QPushButton:hover   { background-color: #F0F0F0; }
        QPushButton:pressed { background-color: #DEDEDE; }
    """)
    return btn


def _ghost_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(42)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #1e1e1e;
            border: 1px solid #282828;
            border-radius: 8px;
            color: #BDBDBD;
            font-size: 14px;
            font-weight: 500;
            padding: 0 24px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
        }
        QPushButton:hover {
            background-color: #242424;
            border-color: #616161;
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
            border-color: #757575;
            color: #FFFFFF;
        }
    """)
    return btn


def _sm_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(38)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #1e1e1e;
            border: 1px solid #282828;
            border-radius: 8px;
            color: #BDBDBD;
            font-size: 13px;
            font-weight: 500;
            padding: 0 14px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
        }
        QPushButton:hover {
            background-color: #242424;
            border-color: #616161;
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
            color: #FFFFFF;
        }
    """)
    return btn


# ── Add / Edit Dialog ─────────────────────────────────────────────────────────

class AddEditDialog(QDialog):
    """Dialog for adding/editing password entries."""

    entry_saved = pyqtSignal(dict)

    def __init__(self, entry: dict = None, parent=None):
        super().__init__(parent)
        self.entry     = entry
        self.is_edit   = entry is not None
        self.generator = PasswordGenerator()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(520 + 2 * _SHADOW)
        self.setStyleSheet(_DIALOG_QSS)

        # Outer layout provides the shadow margin; card is the visible surface
        outer = QVBoxLayout(self)
        outer.setContentsMargins(_SHADOW, _SHADOW, _SHADOW, _SHADOW)
        outer.setSpacing(0)
        self._card = _Card()
        _eff = QGraphicsDropShadowEffect(self._card)
        _eff.setBlurRadius(32)
        _eff.setColor(QColor(0, 0, 0, 150))
        _eff.setOffset(0, 10)
        self._card.setGraphicsEffect(_eff)
        outer.addWidget(self._card)

        self._setup_ui()
        self._load_entry()

    def paintEvent(self, event):
        # Force the dialog window itself to be fully transparent.
        # CompositionMode_Source replaces destination with source (including alpha),
        # so transparent source = fully transparent window.  _Card paints its own
        # rounded background on top via its own paintEvent.
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.end()

    def _setup_ui(self):
        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(12)

        # Title
        title = QLabel("Edit Password" if self.is_edit else "Add New Password")
        title.setStyleSheet(
            "font-size: 19px; font-weight: 700; color: #FFFFFF; "
            "margin-bottom: 2px; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #242424;")
        layout.addWidget(sep)
        layout.addSpacing(4)

        # Service name
        layout.addWidget(self._lbl("SERVICE / APP NAME"))
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("e.g. Instagram, Steam, PayPal…")
        self.service_input.setMinimumHeight(42)
        layout.addWidget(self.service_input)

        completer = QCompleter(COMMON_SERVICES, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.service_input.setCompleter(completer)

        # Username
        layout.addWidget(self._lbl("USERNAME / EMAIL"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username@example.com")
        self.username_input.setMinimumHeight(42)
        layout.addWidget(self.username_input)

        # Password row
        layout.addWidget(self._lbl("PASSWORD"))
        pass_row = QHBoxLayout()
        pass_row.setSpacing(8)

        self.password_input = PasswordLineEdit()
        self.password_input.setPlaceholderText("Enter or generate a password")
        self.password_input.setMinimumHeight(42)
        self.password_input.textChanged.connect(self._update_strength)
        pass_row.addWidget(self.password_input, 1)

        eye_btn = EyeButton(size=38)
        eye_btn.clicked.connect(lambda: self.password_input.toggle_visibility())
        pass_row.addWidget(eye_btn)

        gen_btn = _sm_btn("Generate")
        gen_btn.clicked.connect(self._generate_password)
        pass_row.addWidget(gen_btn)

        layout.addLayout(pass_row)

        # Strength meter
        self.strength_meter = StrengthMeter()
        layout.addWidget(self.strength_meter)
        self.strength_label = QLabel("")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.strength_label.setStyleSheet(
            "font-size: 11px; color: #616161; background: transparent;"
        )
        layout.addWidget(self.strength_label)

        # Notes
        layout.addWidget(self._lbl("NOTES (OPTIONAL)"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any extra info…")
        self.notes_input.setFixedHeight(70)
        layout.addWidget(self.notes_input)

        # Favourite
        self.favorite_check = QCheckBox("Mark as favourite")
        layout.addWidget(self.favorite_check)

        layout.addSpacing(4)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel = _ghost_btn("Cancel")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        save = _primary_btn("Save" if self.is_edit else "Add Password")
        save.clicked.connect(self._save)
        btn_row.addWidget(save)

        layout.addLayout(btn_row)

    def _lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #424242; "
            "background: transparent; letter-spacing: 1.0px; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        return lbl

    def _load_entry(self):
        if self.entry:
            self.service_input.setText(self.entry.get('title', ''))
            self.username_input.setText(self.entry.get('username', ''))
            self.password_input.setText(self.entry.get('password', ''))
            self.notes_input.setPlainText(self.entry.get('notes', ''))
            self.favorite_check.setChecked(self.entry.get('favorite', False))
            self._update_strength()

    def _update_strength(self):
        pw = self.password_input.text()
        if pw:
            score, desc = self.generator.calculate_strength(pw)
            self.strength_meter.set_strength(score)
            self.strength_label.setText(desc)
        else:
            self.strength_meter.set_strength(0)
            self.strength_label.setText("")

    def _generate_password(self):
        pw = self.generator.generate(18, True, True, True, True)
        self.password_input.setText(pw)
        self._update_strength()

    def _save(self):
        service  = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not service:
            show_error("Service name is required")
            self.service_input.setFocus()
            return
        if not username:
            show_error("Username / email is required")
            self.username_input.setFocus()
            return
        if not password:
            show_error("Password cannot be empty")
            self.password_input.setFocus()
            return

        data = {
            'title':    service,
            'username': username,
            'password': password,
            'url':      '',
            'notes':    self.notes_input.toPlainText().strip(),
            'favorite': self.favorite_check.isChecked(),
            'tags':     [],
        }
        if self.is_edit:
            data['id'] = self.entry['id']

        self.entry_saved.emit(data)
        self.accept()


# ── Generator Dialog ──────────────────────────────────────────────────────────

class GeneratorDialog(QDialog):
    """Password generator dialog."""

    password_generated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = PasswordGenerator()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(460 + 2 * _SHADOW)
        self.setStyleSheet(_DIALOG_QSS)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(_SHADOW, _SHADOW, _SHADOW, _SHADOW)
        outer.setSpacing(0)
        self._card = _Card()
        _eff = QGraphicsDropShadowEffect(self._card)
        _eff.setBlurRadius(32)
        _eff.setColor(QColor(0, 0, 0, 150))
        _eff.setOffset(0, 10)
        self._card.setGraphicsEffect(_eff)
        outer.addWidget(self._card)

        self._setup_ui()
        self._generate()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.end()

    def _setup_ui(self):
        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Password Generator")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #FFFFFF; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        layout.addWidget(title)

        # Generated password display
        self.pw_display = QLineEdit()
        self.pw_display.setReadOnly(True)
        self.pw_display.setMinimumHeight(46)
        self.pw_display.setStyleSheet("""
            QLineEdit {
                background-color: #1c1c1c;
                border: 1px solid #424242;
                border-radius: 8px;
                padding: 0 14px;
                color: #BDBDBD;
                font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(self.pw_display)

        self.strength_meter = StrengthMeter()
        layout.addWidget(self.strength_meter)
        self.strength_label = QLabel("")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.strength_label.setStyleSheet(
            "font-size: 11px; color: #616161; background: transparent;"
        )
        layout.addWidget(self.strength_label)

        # Length
        length_row = QHBoxLayout()
        lbl = QLabel("Length:")
        lbl.setStyleSheet(
            "color: #BDBDBD; font-size: 13px; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        length_row.addWidget(lbl)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(18)
        self.length_spin.setFixedWidth(72)
        self.length_spin.valueChanged.connect(self._generate)
        length_row.addWidget(self.length_spin)
        length_row.addStretch()
        layout.addLayout(length_row)

        # Options
        self.uppercase = QCheckBox("Uppercase  A–Z")
        self.uppercase.setChecked(True)
        self.uppercase.stateChanged.connect(self._generate)
        layout.addWidget(self.uppercase)

        self.lowercase = QCheckBox("Lowercase  a–z")
        self.lowercase.setChecked(True)
        self.lowercase.stateChanged.connect(self._generate)
        layout.addWidget(self.lowercase)

        self.digits = QCheckBox("Digits  0–9")
        self.digits.setChecked(True)
        self.digits.stateChanged.connect(self._generate)
        layout.addWidget(self.digits)

        self.symbols = QCheckBox("Symbols  !@#$…")
        self.symbols.setChecked(True)
        self.symbols.stateChanged.connect(self._generate)
        layout.addWidget(self.symbols)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        regen_btn = _ghost_btn("Regenerate")
        regen_btn.clicked.connect(self._generate)
        btn_row.addWidget(regen_btn)

        use_btn = _primary_btn("Use Password")
        use_btn.clicked.connect(self._use)
        btn_row.addWidget(use_btn)

        layout.addLayout(btn_row)

    def _generate(self):
        pw = self.generator.generate(
            length=self.length_spin.value(),
            use_uppercase=self.uppercase.isChecked(),
            use_lowercase=self.lowercase.isChecked(),
            use_digits=self.digits.isChecked(),
            use_symbols=self.symbols.isChecked()
        )
        self.pw_display.setText(pw)
        score, desc = self.generator.calculate_strength(pw)
        self.strength_meter.set_strength(score)
        self.strength_label.setText(desc)

    def _use(self):
        self.password_generated.emit(self.pw_display.text())
        self.accept()

    def get_password(self) -> str:
        return self.pw_display.text()
