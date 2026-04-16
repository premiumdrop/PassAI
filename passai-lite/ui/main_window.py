"""PassAI Main Window — Gray 900 · QWidget base to eliminate top-clip issue"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QScrollArea, QFrame, QMessageBox, QApplication,
)
from PyQt6.QtCore import (Qt, QTimer, QPoint, QRect, QEvent,
                          QPropertyAnimation, QEasingCurve,
                          QObject, QRunnable, QThreadPool, pyqtSignal)
from PyQt6.QtGui import (
    QPainter, QColor, QIcon, QPainterPath, QRegion,
    QLinearGradient, QBrush, QFont
)
from ui.widgets import (
    TrafficLightButton, SearchBox,
    EntryCard, PasswordLineEdit, StrengthMeter, EyeButton, Icons
)
from ui.add_dialog import AddEditDialog, GeneratorDialog
from ui.toast import ToastManager, show_success, show_info, show_error
from ui.animations import AnimationHelper, DetailsPanelAnimator
from core.vault import Vault
from core.settings import Settings
from core.clipboard import ClipboardManager
from core.icons import IconManager
from core.generator import PasswordGenerator
from ui.upgrade_dialog import UpgradeDialog
from core.edition import MAX_PASSWORDS, EDITION_NAME


# ── Async icon loader ─────────────────────────────────────────────────────────

class _IconSignal(QObject):
    """Lives in main thread; carries icon-ready callbacks across thread boundary."""
    ready = pyqtSignal(int, str)   # (entry_id, icon_path)


class _IconRunnable(QRunnable):
    """Fetches one service icon in a QThreadPool worker thread."""

    def __init__(self, entry_id: int, service_name: str,
                 icon_manager, signal: _IconSignal):
        super().__init__()
        self.entry_id     = entry_id
        self.service_name = service_name
        self.icon_manager = icon_manager
        self.signal       = signal

    def run(self):
        path = self.icon_manager.fetch_icon_blocking(self.service_name)
        if path:
            self.signal.ready.emit(self.entry_id, str(path))


# ── Sidebar panel ─────────────────────────────────────────────────────────────

class SidebarPanel(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#161616"))
        grad.setColorAt(1.0, QColor("#121212"))
        p.fillRect(self.rect(), QBrush(grad))
        p.setPen(QColor("#1e1e1e"))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()


# ── Icon widgets ──────────────────────────────────────────────────────────────

class _BrandKeyIcon(QWidget):
    def __init__(self, size=20, parent=None):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        Icons.draw_key(p, self._sz // 2, self._sz // 2, int(self._sz * 0.85), QColor("#757575"))
        p.end()


class _EmptyLockIcon(QWidget):
    def __init__(self, size=44, parent=None):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        Icons.draw_lock(p, self._sz // 2, self._sz // 2, int(self._sz * 0.72), QColor("#3a3a3a"))
        p.end()


# ── Service icon ──────────────────────────────────────────────────────────────

class ServiceIcon(QWidget):
    _COLORS = [
        ("#757575", "#424242"), ("#616161", "#424242"),
        ("#9e9e9e", "#616161"), ("#bdbdbd", "#757575"),
        ("#424242", "#212121"), ("#616161", "#2a2a2a"),
    ]

    def __init__(self, icon_path, title, size=52, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.title = title
        self.sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPixmap, QRadialGradient
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.icon_path and Path(self.icon_path).exists():
            pix = QPixmap(self.icon_path).scaled(
                self.sz, self.sz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            p.drawPixmap(0, 0, pix)
        else:
            letter = self.title[0].upper() if self.title else "?"
            idx = (ord(letter) - 65) % len(self._COLORS) if letter.isalpha() else 0
            fg, bg_dark = self._COLORS[idx]
            grad = QRadialGradient(self.sz / 2, self.sz / 2, self.sz / 2)
            grad.setColorAt(0.0, QColor(fg))
            grad.setColorAt(1.0, QColor(bg_dark))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, self.sz, self.sz)
            font = QFont("Segoe UI Variable", int(self.sz * 0.38), QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRect(0, 0, self.sz, self.sz), Qt.AlignmentFlag.AlignCenter, letter)
        p.end()


# ── Button factories ──────────────────────────────────────────────────────────

def _ghost_btn(text, min_width=90):
    btn = QPushButton(text)
    btn.setMinimumWidth(min_width)
    btn.setFixedHeight(36)
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
            border-color: #757575;
            color: #FFFFFF;
        }
    """)
    return btn


def _danger_btn(text, min_width=90):
    btn = QPushButton(text)
    btn.setMinimumWidth(min_width)
    btn.setFixedHeight(36)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: rgba(239, 83, 80, 0.10);
            border: 1px solid rgba(239, 83, 80, 0.25);
            border-radius: 8px;
            color: #EF5350;
            font-size: 13px;
            font-weight: 600;
            padding: 0 14px;
        }
        QPushButton:hover {
            background-color: rgba(239, 83, 80, 0.18);
            border-color: #EF5350;
        }
        QPushButton:pressed {
            background-color: #EF5350;
            color: #FFFFFF;
        }
    """)
    return btn


def _copy_btn(label="Copy"):
    btn = QPushButton(label)
    btn.setFixedHeight(34)
    btn.setMinimumWidth(64)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: rgba(117, 117, 117, 0.10);
            border: 1px solid rgba(117, 117, 117, 0.22);
            border-radius: 7px;
            color: #757575;
            font-size: 12px;
            font-weight: 600;
            padding: 0 12px;
        }
        QPushButton:hover {
            background-color: rgba(117, 117, 117, 0.20);
            border-color: #757575;
            color: #FFFFFF;
        }
        QPushButton:pressed {
            background-color: #616161;
            color: #FFFFFF;
        }
    """)
    return btn


_SCROLLBAR_STYLE = """
    QScrollArea { background: transparent; border: none; }
    QScrollBar:vertical {
        background: transparent; width: 4px; margin: 0; border: none;
    }
    QScrollBar::handle:vertical {
        background: #2e2e2e; border-radius: 2px; min-height: 24px;
    }
    QScrollBar::handle:vertical:hover { background: #616161; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical
        { height: 0; border: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
        { background: transparent; }
"""


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    """
    PassAI main window.

    Uses QWidget (not QMainWindow) so the layout starts at exactly (0, 0) of
    the window — eliminating the top-clipping issue caused by QMainWindow's
    internal menu-bar offset.  The rounded background is drawn in paintEvent.
    """

    _RADIUS = 18

    def __init__(self, settings: Settings, vault: Vault):
        super().__init__()
        self.settings       = settings
        self.vault          = vault
        self.clipboard      = ClipboardManager(settings.get('clipboard_timeout', 20))
        self.icon_manager   = IconManager()
        self.generator      = PasswordGenerator()
        self.entries           = []
        self.filtered_entries  = []
        self.selected_entry    = None
        self.selected_card     = None
        self.details_animator  = None
        self.drag_position     = None

        self.auto_lock_timer = QTimer()
        self.auto_lock_timer.timeout.connect(self.lock_vault)

        self._icon_signal = _IconSignal()
        self._icon_signal.ready.connect(self._on_icon_ready)
        self._icon_cards: dict = {}

        self._setup_window()
        self._setup_ui()
        self.load_entries()
        ToastManager.set_parent(self)

    # ── Window chrome ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("PassAI Lite")
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "icon.ico"
            if icon_path.exists():
                from PyQt6.QtGui import QIcon
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        W, H = 1060, 680
        self.setFixedSize(W, H)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - W) // 2, (screen.height() - H) // 2)

        # Subtle version label — top-right, non-interactive
        ver = QLabel("1.0L", self)
        ver.setStyleSheet(
            "font-size: 9px; color: #2a2a2a; background: transparent; "
            "letter-spacing: 0.6px; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        ver.setFixedSize(32, 14)
        ver.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ver.move(W - 46, 18)
        ver.raise_()

        self._update_mask()

    def _update_mask(self):
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._RADIUS, self._RADIUS)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()

    def paintEvent(self, event):
        """Draw the rounded dark background — no pen stroke to avoid top line."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._RADIUS, self._RADIUS)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#121212"))
        p.drawPath(path)
        p.end()

    # ── Window state & drag ───────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        # Fade in on first show and on restore from minimize
        if self.windowOpacity() < 0.5:
            AnimationHelper.window_fade_in(self, duration=200)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            # Restored from minimized — fade back in
            if not (self.windowState() & Qt.WindowState.WindowMinimized):
                self.setWindowOpacity(0.0)
                AnimationHelper.window_fade_in(self, duration=180)

    def _animate_minimize(self):
        """Smooth fade-out then minimize."""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(130)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._do_minimize)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._min_anim = anim

    def _do_minimize(self):
        self.showMinimized()
        self.setWindowOpacity(1.0)   # reset so restore fade works

    def mousePressEvent(self, event):
        self._reset_auto_lock()
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def keyPressEvent(self, event):
        self._reset_auto_lock()
        super().keyPressEvent(event)

    # ── UI build ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Body fills the entire window — sidebar covers full height,
        # so there is no separate dark band at the top.
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = self._build_sidebar()
        body.addWidget(self.sidebar)

        self.details_panel = self._build_details_panel()
        body.addWidget(self.details_panel, 1)

        self.details_animator = DetailsPanelAnimator(self.details_panel)
        root.addLayout(body, 1)

        self._reset_auto_lock()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = SidebarPanel()
        sidebar.setFixedWidth(300)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(0)

        # ── Traffic lights (inside sidebar so sidebar bg covers full height) ─
        tl_row = QHBoxLayout()
        tl_row.setContentsMargins(0, 0, 0, 0)
        tl_row.setSpacing(8)

        close_btn = TrafficLightButton("#FF5F57")
        close_btn.clicked.connect(self.close)
        tl_row.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        min_btn = TrafficLightButton("#FEBC2E")
        min_btn.clicked.connect(self._animate_minimize)
        tl_row.addWidget(min_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        max_btn = TrafficLightButton("#28C840")
        max_btn.clicked.connect(lambda: None)
        tl_row.addWidget(max_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        tl_row.addStretch()
        layout.addLayout(tl_row)

        layout.addSpacing(16)

        # ── Brand ─────────────────────────────────────────────────────────────
        brand_row = QHBoxLayout()
        brand_row.setSpacing(9)
        brand_row.addWidget(_BrandKeyIcon(18))
        brand_name = QLabel("PassAI")
        brand_name.setStyleSheet("""
            font-size: 17px; font-weight: 700; color: #FFFFFF;
            background: transparent; letter-spacing: 0.3px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
        """)
        brand_row.addWidget(brand_name)
        lite_badge = QLabel("LITE")
        lite_badge.setStyleSheet("""
            font-size: 8px; font-weight: 700; color: #616161;
            background: #1e1e1e; border: 1px solid #2a2a2a;
            border-radius: 4px; padding: 1px 5px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
            letter-spacing: 0.8px;
        """)
        brand_row.addWidget(lite_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        layout.addSpacing(18)

        # Search
        self.search_box = SearchBox("Search passwords…")
        self.search_box.setFixedHeight(40)
        self.search_box.textChanged.connect(self.filter_entries)
        layout.addWidget(self.search_box)

        layout.addSpacing(10)

        self._new_btn = QPushButton("New Password")
        self._new_btn.setFixedHeight(40)
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; border: none; border-radius: 8px;
                color: #121212; font-size: 13px; font-weight: 700;
                padding: 0 18px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QPushButton:hover   { background-color: #F0F0F0; }
            QPushButton:pressed { background-color: #DEDEDE; }
        """)
        self._new_btn.clicked.connect(self.show_add_dialog)
        layout.addWidget(self._new_btn)

        layout.addSpacing(6)
        self._count_lbl = QLabel(f"0 / {MAX_PASSWORDS} passwords")
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet(
            "font-size: 10px; color: #3a3a3a; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        layout.addWidget(self._count_lbl)

        layout.addSpacing(12)

        # Section label
        hdr = QLabel("PASSWORDS")
        hdr.setStyleSheet("""
            font-size: 9px; font-weight: 700; color: #3a3a3a;
            background: transparent; letter-spacing: 2px;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
        """)
        layout.addWidget(hdr)
        layout.addSpacing(8)

        # Entry list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(_SCROLLBAR_STYLE)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 2, 0)
        self.list_layout.setSpacing(3)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        layout.addSpacing(12)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #1e1e1e;")
        layout.addWidget(div)
        layout.addSpacing(10)

        btm = QHBoxLayout()
        btm.setSpacing(8)
        key_btn = _ghost_btn("KEY")
        key_btn.setToolTip("Recovery Key — available in Pro")
        key_btn.clicked.connect(self.show_key_dialog)
        btm.addWidget(key_btn)
        lock_btn = _ghost_btn("Lock")
        lock_btn.setToolTip("Lock vault")
        lock_btn.clicked.connect(self.sign_out)
        btm.addWidget(lock_btn)
        layout.addLayout(btm)

        return sidebar

    # ── Details panel ─────────────────────────────────────────────────────────

    def _build_details_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("detailsPanel")
        panel.setStyleSheet("QWidget#detailsPanel { background-color: #181818; }")

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(_SCROLLBAR_STYLE)

        sc = QWidget()
        sc.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(sc)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)

        # Empty state
        self.empty_label = QWidget()
        el = QVBoxLayout(self.empty_label)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setContentsMargins(0, 60, 0, 0)

        el_icon = _EmptyLockIcon(44)
        el.addWidget(el_icon, 0, Qt.AlignmentFlag.AlignHCenter)
        el.addSpacing(18)

        el_text = QLabel("Select a password to view details")
        el_text.setStyleSheet(
            "font-size: 15px; color: #3a3a3a; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        el_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(el_text)
        el.addSpacing(6)

        el_hint = QLabel("or click  + New Password  to add one")
        el_hint.setStyleSheet("font-size: 12px; color: #282828; background: transparent;")
        el_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(el_hint)
        layout.addWidget(self.empty_label)
        layout.addStretch()

        # Details form
        self.details_form = QWidget()
        self.details_form.setStyleSheet("background: transparent;")
        self.details_form.hide()
        form = QVBoxLayout(self.details_form)
        form.setSpacing(0)
        form.setContentsMargins(0, 0, 0, 0)

        # Header
        self._hdr_widget = QWidget()
        self._hdr_widget.setStyleSheet("background: transparent;")
        hdr_layout = QHBoxLayout(self._hdr_widget)
        hdr_layout.setContentsMargins(0, 0, 0, 0)
        hdr_layout.setSpacing(16)

        self._hdr_icon_container = QWidget()
        self._hdr_icon_container.setFixedSize(54, 54)
        self._hdr_icon_container.setStyleSheet("background: transparent;")
        hdr_layout.addWidget(self._hdr_icon_container)

        hdr_text = QVBoxLayout()
        hdr_text.setSpacing(3)
        self._hdr_title = QLabel("")
        self._hdr_title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #FFFFFF; background: transparent; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        hdr_text.addWidget(self._hdr_title)
        self._hdr_user = QLabel("")
        self._hdr_user.setStyleSheet("font-size: 12px; color: #616161; background: transparent;")
        hdr_text.addWidget(self._hdr_user)
        hdr_layout.addLayout(hdr_text, 1)

        hdr_actions = QHBoxLayout()
        hdr_actions.setSpacing(8)
        self._edit_btn = _ghost_btn("Edit")
        self._edit_btn.clicked.connect(self.edit_entry)
        hdr_actions.addWidget(self._edit_btn)
        self._delete_btn = _danger_btn("Delete")
        self._delete_btn.clicked.connect(self.delete_entry)
        hdr_actions.addWidget(self._delete_btn)
        hdr_layout.addLayout(hdr_actions)
        form.addWidget(self._hdr_widget)
        form.addSpacing(24)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #242424;")
        form.addWidget(div)
        form.addSpacing(26)

        # Username
        form.addWidget(self._field_label("USERNAME / EMAIL"))
        form.addSpacing(8)
        user_row = QHBoxLayout()
        user_row.setSpacing(10)
        self.detail_username = QLineEdit()
        self.detail_username.setReadOnly(True)
        self.detail_username.setFixedHeight(42)
        self.detail_username.setStyleSheet(self._field_style())
        user_row.addWidget(self.detail_username, 1)
        copy_user = _copy_btn("Copy")
        copy_user.clicked.connect(self.copy_username)
        user_row.addWidget(copy_user)
        form.addLayout(user_row)
        form.addSpacing(22)

        # Password
        form.addWidget(self._field_label("PASSWORD"))
        form.addSpacing(8)
        pass_row = QHBoxLayout()
        pass_row.setSpacing(10)
        self.detail_password = PasswordLineEdit()
        self.detail_password.setReadOnly(True)
        self.detail_password.setFixedHeight(42)
        self.detail_password.setStyleSheet(self._field_style())
        pass_row.addWidget(self.detail_password, 1)
        eye_btn = EyeButton(size=34)
        eye_btn.clicked.connect(lambda: self.detail_password.toggle_visibility())
        pass_row.addWidget(eye_btn)
        copy_pass = _copy_btn("Copy")
        copy_pass.clicked.connect(self.copy_password)
        pass_row.addWidget(copy_pass)
        form.addLayout(pass_row)

        form.addSpacing(10)
        self.detail_strength = StrengthMeter()
        form.addWidget(self.detail_strength)
        form.addSpacing(5)
        self.detail_strength_label = QLabel("")
        self.detail_strength_label.setStyleSheet("font-size: 11px; color: #616161; background: transparent;")
        form.addWidget(self.detail_strength_label)
        form.addSpacing(22)

        # Notes
        form.addWidget(self._field_label("NOTES"))
        form.addSpacing(8)
        self.detail_notes = QTextEdit()
        self.detail_notes.setFixedHeight(90)
        self.detail_notes.setReadOnly(True)
        self.detail_notes.setStyleSheet("""
            QTextEdit {
                background-color: #1c1c1c; border: 1px solid #242424;
                border-radius: 8px; padding: 10px 14px;
                color: #BDBDBD; font-size: 13px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
        """)
        form.addWidget(self.detail_notes)

        layout.addWidget(self.details_form)
        layout.addStretch()
        scroll.setWidget(sc)
        main_layout.addWidget(scroll)
        return panel

    # ── Style helpers ─────────────────────────────────────────────────────────

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #424242; "
            "background: transparent; letter-spacing: 1.2px; "
            "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
        )
        return lbl

    def _field_style(self):
        return """
            QLineEdit {
                background-color: #1c1c1c; border: 1px solid #242424;
                border-radius: 8px; padding: 0 14px;
                color: #FFFFFF; font-size: 14px;
                font-family: "Segoe UI Variable", "Segoe UI", Arial;
            }
            QLineEdit:focus { border-color: #757575; }
        """

    # ── Entry loading / filtering ─────────────────────────────────────────────

    def load_entries(self):
        try:
            self.entries = self.vault.get_all_entries()
            self.filter_entries()
            self._update_limit_ui()
        except Exception as e:
            self.entries = []
            self.filtered_entries = []
            show_error(f"Failed to load entries: {str(e)}")

    def _update_limit_ui(self):
        count = len(self.entries)
        self._count_lbl.setText(f"{count} / {MAX_PASSWORDS} passwords")
        if count >= MAX_PASSWORDS:
            self._count_lbl.setStyleSheet(
                "font-size: 10px; color: #EF5350; background: transparent; "
                "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
            )
        else:
            self._count_lbl.setStyleSheet(
                "font-size: 10px; color: #3a3a3a; background: transparent; "
                "font-family: 'Segoe UI Variable', 'Segoe UI', Arial;"
            )

    def filter_entries(self):
        query = self.search_box.text().lower()
        if query:
            self.filtered_entries = [
                e for e in self.entries
                if query in e['title'].lower() or
                   query in e['username'].lower() or
                   any(query in t.lower() for t in e.get('tags', []))
            ]
        else:
            self.filtered_entries = self.entries.copy()
        self._update_entry_list()

    def _update_entry_list(self):
        if not hasattr(self, 'list_layout'):
            return
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.selected_card = None
        self._icon_cards.clear()
        new_cards = []
        pool = QThreadPool.globalInstance()

        for entry in self.filtered_entries:
            cached = self.icon_manager.get_icon_path_cached(entry['title'])
            icon_display = (str(cached) if cached
                            else self.icon_manager.get_emoji(entry['title']))
            card = EntryCard(
                entry['id'], icon_display,
                entry['title'], entry['username'],
                entry.get('favorite', False)
            )
            card.clicked.connect(self.show_entry_details)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
            new_cards.append(card)
            self._icon_cards[entry['id']] = card
            if self.selected_entry and entry['id'] == self.selected_entry['id']:
                card.set_selected(True)
                self.selected_card = card

            if not cached:
                pool.start(_IconRunnable(
                    entry['id'], entry['title'],
                    self.icon_manager, self._icon_signal,
                ))

        AnimationHelper.stagger_fade_in(new_cards, base_delay=30, duration=200)

    def _on_icon_ready(self, entry_id: int, icon_path: str) -> None:
        """Called in the main thread when a background icon download finishes."""
        card = self._icon_cards.get(entry_id)
        if card is None:
            return
        try:
            card.set_icon(icon_path)
        except RuntimeError:
            pass

    # ── Entry details ─────────────────────────────────────────────────────────

    def show_entry_details(self, entry_id: int):
        entry = next((e for e in self.entries if e['id'] == entry_id), None)
        if not entry:
            return

        if self.selected_card:
            self.selected_card.set_selected(False)

        for i in range(self.list_layout.count() - 1):
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                if isinstance(card, EntryCard) and card.entry_id == entry_id:
                    card.set_selected(True)
                    self.selected_card = card
                    break

        self.selected_entry = entry

        def update_content():
            self.empty_label.hide()
            self.details_form.show()
            self._hdr_title.setText(entry['title'])
            self._hdr_user.setText(entry['username'])

            for child in self._hdr_icon_container.findChildren(QWidget):
                child.deleteLater()
            icon_path = self.icon_manager.get_icon_path(entry['title'])
            icon_path = str(icon_path) if icon_path else self.icon_manager.get_emoji(entry['title'])
            svc = ServiceIcon(icon_path, entry['title'], 52, self._hdr_icon_container)
            svc.move(0, 0)
            svc.show()

            self.detail_username.setText(entry['username'])
            self.detail_password.setText(entry['password'])
            self.detail_notes.setPlainText(entry.get('notes', ''))
            score, desc = self.generator.calculate_strength(entry['password'])
            self.detail_strength.set_strength(score)
            self.detail_strength_label.setText(desc)

        if self.details_animator and not self.details_animator.is_animating:
            self.details_animator.animate_content_change(update_content)
        else:
            update_content()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def show_add_dialog(self):
        if len(self.entries) >= MAX_PASSWORDS:
            UpgradeDialog(self).exec()
            return
        dialog = AddEditDialog(parent=self)
        dialog.entry_saved.connect(self.on_entry_added)
        dialog.exec()

    def on_entry_added(self, entry_data: dict):
        if len(self.entries) >= MAX_PASSWORDS:
            return
        try:
            self.vault.add_entry(
                entry_data['title'], entry_data['username'], entry_data['password'],
                entry_data.get('url', ''), entry_data.get('notes', ''),
                entry_data.get('tags', []), entry_data.get('favorite', False)
            )
            self.load_entries()
            show_success("Password saved successfully")
            self.vault.create_backup()
        except Exception as e:
            show_error(f"Failed to add entry: {str(e)}")

    def edit_entry(self):
        if not self.selected_entry:
            return
        dialog = AddEditDialog(self.selected_entry, parent=self)
        dialog.entry_saved.connect(self.on_entry_updated)
        dialog.exec()

    def on_entry_updated(self, entry_data: dict):
        try:
            self.vault.update_entry(
                entry_data['id'], entry_data['title'], entry_data['username'],
                entry_data['password'], entry_data.get('url', ''),
                entry_data.get('notes', ''), entry_data.get('tags', []),
                entry_data.get('favorite', False)
            )
            self.load_entries()
            self.show_entry_details(entry_data['id'])
            show_success("Password updated successfully")
            self.vault.create_backup()
        except Exception as e:
            show_error(f"Failed to update entry: {str(e)}")

    def delete_entry(self):
        if not self.selected_entry:
            return
        reply = QMessageBox.question(
            self, "Delete Password",
            f"Permanently delete '{self.selected_entry['title']}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.vault.delete_entry(self.selected_entry['id'])
                self.load_entries()
                self.selected_entry = None
                self.selected_card  = None
                self.empty_label.show()
                self.details_form.hide()
                show_info("Entry deleted")
            except Exception as e:
                show_error(f"Failed to delete: {str(e)}")

    def copy_username(self):
        if self.selected_entry:
            self.clipboard.copy(self.selected_entry['username'])
            show_success("Username copied")

    def copy_password(self):
        if self.selected_entry:
            self.clipboard.copy(self.selected_entry['password'])
            show_success("Password copied")

    # ── KEY button (locked in Lite) ───────────────────────────────────────────

    def show_key_dialog(self):
        UpgradeDialog(self).exec()

    # ── Sign out / lock ───────────────────────────────────────────────────────

    def sign_out(self):
        reply = QMessageBox.question(
            self, "Lock Vault",
            "Lock the vault and return to the PIN screen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auto_lock_timer.stop()
                self.vault.lock()
                self.hide()
                from ui.unlock_pin import UnlockPINWindow
                self.unlock_window = UnlockPINWindow()
                self.unlock_window.pin_entered.connect(self.on_reauth)
                self.unlock_window.show()
                self.unlock_window.raise_()
                self.unlock_window.activateWindow()
            except Exception as e:
                print(f"Error during sign out: {e}")

    def on_reauth(self, pin: str):
        from core.pin_manager import PINManager
        try:
            pin_manager    = PINManager(self.settings)
            master_password = pin_manager.verify_pin(pin)
            if not master_password:
                if hasattr(self, 'unlock_window'):
                    self.unlock_window.show_error()
                return
            if self.vault.unlock(master_password):
                if hasattr(self, 'unlock_window'):
                    self.unlock_window.close()
                    delattr(self, 'unlock_window')
                from ui.sounds import play_unlock
                play_unlock()
                self.load_entries()
                self.show()
                self.raise_()
                self.activateWindow()
                self._reset_auto_lock()
        except Exception as e:
            print(f"Reauth error: {e}")

    # ── Auto-lock ─────────────────────────────────────────────────────────────

    def _reset_auto_lock(self):
        timeout_min = self.settings.get('auto_lock_timeout', 5)
        self.auto_lock_timer.stop()
        self.auto_lock_timer.start(timeout_min * 60 * 1000)

    def lock_vault(self):
        self.auto_lock_timer.stop()   # prevent re-firing on already-locked vault
        self.vault.lock()
        self.hide()
        from ui.unlock_pin import UnlockPINWindow
        self.unlock_window = UnlockPINWindow()
        self.unlock_window.pin_entered.connect(self.on_reauth)
        self.unlock_window.show()
