import sys
import json
import os
import re
import urllib.request
import webbrowser
import platform
import traceback
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTextBrowser, QCheckBox, QComboBox, QStackedWidget,
    QListWidget, QMessageBox, QSystemTrayIcon, QMenu,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QScrollArea, QFrame, QSizePolicy, QVBoxLayout, QHBoxLayout,
    QListWidgetItem, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QColor, QIcon, QAction, QFont, QPainter, QPen, QBrush, QPalette

try:
    if platform.system().lower() in ["windows", "linux", "darwin"]:
        import keyboard
        KEYBOARD_AVAILABLE = True
    else:
        KEYBOARD_AVAILABLE = False
except Exception:
    KEYBOARD_AVAILABLE = False

CURRENT_VERSION = "1.3"
VERSION_URL = "https://raw.githubusercontent.com/Euro1234Aa/MDT/refs/heads/main/version.txt"
DOWNLOAD_URL = "https://github.com/Euro1234Aa/MDT/releases"

# ─── Color palettes ───────────────────────────────────────────────────────────
THEMES = {
    "blue": {
        "bg_dark":    "#0d1117",
        "bg_panel":   "#131922",
        "bg_card":    "#1a2332",
        "bg_item":    "#1e2a3a",
        "bg_item_h":  "#243244",
        "bg_input":   "#111827",
        "border":     "#1f3050",
        "border_h":   "#2563eb",
        "accent":     "#2563eb",
        "accent2":    "#1d4ed8",
        "accent_glow":"#3b82f6",
        "text":       "#e2e8f0",
        "text_dim":   "#64748b",
        "text_muted": "#334155",
        "green":      "#10b981",
        "red":        "#ef4444",
        "yellow":     "#f59e0b",
        "header_bg":  "#0f172a",
        "sidebar_bg": "#0a0f1a",
        "divider":    "#1e293b",
    },
    "dark": {
        "bg_dark":    "#0a0a0a",
        "bg_panel":   "#111111",
        "bg_card":    "#1a1a1a",
        "bg_item":    "#1e1e1e",
        "bg_item_h":  "#252525",
        "bg_input":   "#0d0d0d",
        "border":     "#2a2a2a",
        "border_h":   "#666666",
        "accent":     "#555555",
        "accent2":    "#444444",
        "accent_glow":"#888888",
        "text":       "#d0d0d0",
        "text_dim":   "#666666",
        "text_muted": "#333333",
        "green":      "#10b981",
        "red":        "#ef4444",
        "yellow":     "#f59e0b",
        "header_bg":  "#080808",
        "sidebar_bg": "#060606",
        "divider":    "#1c1c1c",
    },
    "green": {
        "bg_dark":    "#0a1a0a",
        "bg_panel":   "#0f200f",
        "bg_card":    "#142814",
        "bg_item":    "#1a301a",
        "bg_item_h":  "#1e3b1e",
        "bg_input":   "#0a140a",
        "border":     "#1f4020",
        "border_h":   "#22c55e",
        "accent":     "#16a34a",
        "accent2":    "#15803d",
        "accent_glow":"#22c55e",
        "text":       "#dcfce7",
        "text_dim":   "#4ade80",
        "text_muted": "#166534",
        "green":      "#4ade80",
        "red":        "#ef4444",
        "yellow":     "#f59e0b",
        "header_bg":  "#081408",
        "sidebar_bg": "#060f06",
        "divider":    "#1a2e1a",
    },
}

C = dict(THEMES["blue"])


def build_style_main(palette):
    return f"""
QWidget {{
    background-color: {palette['bg_dark']};
    color: {palette['text']};
    font-family: 'Segoe UI', 'Tahoma', sans-serif;
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: {palette['bg_panel']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {palette['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {palette['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {palette['bg_panel']};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {palette['border']};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
"""


STYLE_MAIN = build_style_main(C)

# ─── Animated line edit ───────────────────────────────────────────────────────
class AnimatedLineEdit(QLineEdit):
    _all_instances = []

    def __init__(self, parent=None):
        super().__init__(parent)
        AnimatedLineEdit._all_instances.append(self)
        self._focused = False
        self._hovered = False
        self._base_geom = None
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _save_base(self):
        if self._base_geom is None:
            self._base_geom = self.geometry()

    def _animate_to(self, scale):
        self._save_base()
        g = self._base_geom
        dw = int(g.width() * (scale - 1.0))
        dh = int(g.height() * (scale - 1.0))
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(QRect(g.x() - dw // 2, g.y() - dh // 2,
                                     g.width() + dw, g.height() + dh))
        self._anim.start()

    def enterEvent(self, event):
        self._hovered = True
        if not self._focused:
            self._animate_to(1.03)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self._focused:
            self._animate_to(1.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        for inst in AnimatedLineEdit._all_instances:
            if inst is not self and inst._focused:
                inst._focused = False
                inst._animate_to(1.0)
        self._focused = True
        self._animate_to(1.03)
        super().mousePressEvent(event)

    def focusOutEvent(self, event):
        if not isinstance(QApplication.focusWidget(), AnimatedLineEdit):
            self._focused = False
            if not self._hovered:
                self._animate_to(1.0)
        super().focusOutEvent(event)


# ─── Callsign-aware line edit ─────────────────────────────────────────────────
class CallsignLineEdit(AnimatedLineEdit):
    _current_callsign = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if CallsignLineEdit._current_callsign and event.button() == Qt.MouseButton.LeftButton:
            QTimer.singleShot(60, self._show_popup)

    def _show_popup(self):
        try:
            if self._popup:
                self._popup.close()
        except Exception:
            pass
        popup = CallsignPopup(self, CallsignLineEdit._current_callsign)
        gpos = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(gpos.x() - 8, gpos.y() + 4)
        popup.show()
        self._popup = popup


# ─── Callsign quick-fill popup ────────────────────────────────────────────────
class CallsignPopup(QWidget):
    def __init__(self, parent_input, callsign, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self._target = parent_input
        self._callsign = callsign

        self.setFixedWidth(max(parent_input.width() + 20, 260))
        self.setStyleSheet(f"""
            QWidget {{
                background: {C['bg_card']};
                border: 1px solid {C['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        my_btn = QPushButton(f"👤  {callsign}", self)
        my_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        my_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; border: none; border-radius: 6px;
                color: white; font-size: 12px; font-weight: bold;
                padding: 9px 12px; text-align: left;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
        """)
        my_btn.clicked.connect(self._use_my)
        layout.addWidget(my_btn)

        sep = QLabel("— или введите другой —", self)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet(f"color: {C['text_muted']}; font-size: 10px; background: transparent; border: none; padding: 2px;")
        layout.addWidget(sep)

        self._manual = QLineEdit(self)
        self._manual.setPlaceholderText("Другой позывной...")
        self._manual.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 6px; padding: 7px 10px; color: {C['text']}; font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; }}
        """)
        self._manual.returnPressed.connect(self._use_manual)
        layout.addWidget(self._manual)

        ok_btn = QPushButton("✔  Применить", self)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['bg_item_h']}; border: 1px solid {C['border']};
                border-radius: 6px; color: {C['text']}; font-size: 11px; padding: 7px;
            }}
            QPushButton:hover {{ background: {C['accent']}; color: white; border: 1px solid {C['accent']}; }}
        """)
        ok_btn.clicked.connect(self._use_manual)
        layout.addWidget(ok_btn)

        self.adjustSize()

    def _use_my(self):
        self._target.setText(self._callsign)
        self.close()

    def _use_manual(self):
        text = self._manual.text().strip()
        if text:
            self._target.setText(text)
        self.close()


# ─── Login dialog ─────────────────────────────────────────────────────────────
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.result_callsign = ""
        self.result_nickname = ""
        self._confirmed = False

        self.setWindowTitle("MDT — Вход в систему")
        self.setFixedSize(460, 320)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {C['bg_panel']};
                color: {C['text']};
                font-family: Segoe UI, sans-serif;
            }}
        """)

        hdr = QWidget(self)
        hdr.setGeometry(0, 0, 460, 50)
        hdr.setStyleSheet(f"background: {C['header_bg']}; border-bottom: 1px solid {C['border']};")
        title = QLabel("⚖  MDT  —  ИДЕНТИФИКАЦИЯ ОФИЦЕРА", hdr)
        title.setGeometry(16, 0, 430, 50)
        title.setStyleSheet(f"color: {C['accent_glow']}; font-size: 13px; font-weight: bold; letter-spacing: 1.5px;")

        badge = QLabel("🛡", self)
        badge.setGeometry(190, 60, 80, 60)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("font-size: 36px; background: transparent;")

        nick_lbl = QLabel("Имя и Фамилия (Ник)", self)
        nick_lbl.setGeometry(30, 128, 400, 18)
        nick_lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")

        self.nick_input = QLineEdit(self)
        self.nick_input.setGeometry(30, 148, 400, 36)
        self.nick_input.setPlaceholderText("John Smith")
        self.nick_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 7px; padding: 8px 12px; color: {C['text']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; background: #0f1d30; }}
        """)

        cs_lbl = QLabel("Позывной (Callsign)", self)
        cs_lbl.setGeometry(30, 196, 400, 18)
        cs_lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")

        self.cs_input = QLineEdit(self)
        self.cs_input.setGeometry(30, 216, 400, 36)
        self.cs_input.setPlaceholderText("(275) E Snake PO II")
        self.cs_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 7px; padding: 8px 12px; color: {C['text']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; background: #0f1d30; }}
        """)
        self.cs_input.returnPressed.connect(self._confirm)
        self.nick_input.returnPressed.connect(self.cs_input.setFocus)

        self.enter_btn = QPushButton("ВОЙТИ В СИСТЕМУ", self)
        self.enter_btn.setGeometry(30, 268, 400, 38)
        self.enter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; border: none; border-radius: 8px;
                color: white; font-size: 13px; font-weight: bold; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
            QPushButton:pressed {{ background: #1e40af; }}
        """)
        self.enter_btn.clicked.connect(self._confirm)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _confirm(self):
        cs = self.cs_input.text().strip()
        nick = self.nick_input.text().strip()
        if not cs or not nick:
            for inp, val in [(self.nick_input, nick), (self.cs_input, cs)]:
                if not val:
                    s = inp.styleSheet()
                    inp.setStyleSheet(s + "border: 2px solid #ef4444;")
                    QTimer.singleShot(1500, lambda i=inp, orig=s: i.setStyleSheet(orig))
            return
        self.result_callsign = cs
        self.result_nickname = nick
        self._confirmed = True
        self.accept()

    def get_data(self):
        return self.result_nickname, self.result_callsign


# ─── Icon-only sidebar button ─────────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, icon_char, label, parent=None):
        super().__init__(parent)
        self.icon_char = icon_char
        self.nav_label = label
        self.setFixedSize(56, 56)
        self.setCheckable(True)
        self._update_style(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _update_style(self, active):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['accent']};
                    border: none;
                    border-radius: 10px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 10px;
                    color: {C['text_dim']};
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    background-color: {C['bg_card']};
                    color: {C['text']};
                }}
            """)

    def setActive(self, active):
        self._update_style(active)

    def enterEvent(self, event):
        if not self.isChecked():
            self._update_style(False)
        super().enterEvent(event)


# ─── Section / field label helpers ───────────────────────────────────────────
def make_section_label(text, parent):
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(f"""
        color: {C['text_dim']};
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 0;
        margin: 0;
    """)
    return lbl

def make_field_label(text, parent):
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px; margin-bottom: 2px;")
    return lbl

def styled_input(parent, placeholder=""):
    inp = AnimatedLineEdit(parent)
    inp.setPlaceholderText(placeholder)
    inp.setStyleSheet(f"""
        QLineEdit {{
            background-color: {C['bg_input']};
            border: 1px solid {C['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {C['text']};
            font-size: 12px;
        }}
        QLineEdit:hover {{
            border: 1px solid {C['border_h']};
        }}
        QLineEdit:focus {{
            border: 1px solid {C['accent']};
            background-color: #0f1d30;
        }}
    """)
    return inp

def styled_textedit(parent, placeholder=""):
    te = QTextEdit(parent)
    te.setPlaceholderText(placeholder)
    te.setStyleSheet(f"""
        QTextEdit {{
            background-color: {C['bg_input']};
            border: 1px solid {C['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {C['text']};
            font-size: 12px;
        }}
        QTextEdit:hover {{
            border: 1px solid {C['border_h']};
        }}
        QTextEdit:focus {{
            border: 1px solid {C['accent']};
            background-color: #0f1d30;
        }}
    """)
    return te

def styled_combo(parent):
    cb = QComboBox(parent)
    cb.setStyleSheet(f"""
        QComboBox {{
            background-color: {C['bg_input']};
            border: 1px solid {C['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {C['text']};
            font-size: 12px;
        }}
        QComboBox:hover {{ border: 1px solid {C['border_h']}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{
            background-color: {C['bg_card']};
            border: 1px solid {C['border']};
            color: {C['text']};
            selection-background-color: {C['accent']};
        }}
    """)
    return cb

def styled_button(parent, text, primary=True):
    btn = QPushButton(text, parent)
    if primary:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {C['accent2']}; }}
            QPushButton:pressed {{ background-color: #1e40af; }}
        """)
    else:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['bg_card']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 8px 18px;
                color: {C['text']};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {C['bg_item_h']};
                border: 1px solid {C['border_h']};
            }}
        """)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def styled_checkbox(parent, text):
    cb = QCheckBox(text, parent)
    cb.setStyleSheet(f"""
        QCheckBox {{
            color: {C['text']};
            font-size: 12px;
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 1px solid {C['border']};
            background: {C['bg_input']};
        }}
        QCheckBox::indicator:checked {{
            background: {C['accent']};
            border: 1px solid {C['accent']};
        }}
    """)
    return cb

def divider(parent):
    line = QFrame(parent)
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {C['divider']}; background: {C['divider']}; max-height: 1px;")
    return line


# ─── Card container ───────────────────────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {C['bg_card']};
                border: 1px solid {C['border']};
                border-radius: 8px;
            }}
        """)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()


# ─── Main MDT window ──────────────────────────────────────────────────────────
class MDT(QWidget):
    def __init__(self):
        super().__init__()
        self.base_path = get_base_path()
        self.oldPos = None
        self.hotkey_id = None
        self.theme = "blue"
        self._nav_buttons = []
        self._active_nav = None

        self.setGeometry(100, 60, 1200, 820)
        self.setMinimumSize(1100, 700)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setWindowOpacity(0.5)
        self.setStyleSheet(STYLE_MAIN)

        self.load_settings()
        QTimer.singleShot(3000, self.check_updates)
        self.load_laws()

        self._build_ui()

        # Tray
        self.tray = QSystemTrayIcon(self)
        icon_path = os.path.join(self.base_path, "icon.ico")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(self.style().standardIcon(
                QApplication.style().StandardPixmap.SP_ComputerIcon))
        self.tray.setToolTip("MDT")
        tray_menu = QMenu()
        show_action = QAction("Показать / Скрыть", self)
        quit_action = QAction("Закрыть", self)
        show_action.triggered.connect(self.toggle_window)
        quit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        W, H = self.width(), self.height()

        # ── Header bar ────────────────────────────────────────────────────────
        self.header = QWidget(self)
        self.header.setGeometry(0, 0, W, 48)
        self.header.setStyleSheet(f"background-color: {C['header_bg']}; border-bottom: 1px solid {C['border']};")

        logo_lbl = QLabel("⚖  MDT", self.header)
        logo_lbl.setGeometry(16, 0, 160, 48)
        logo_lbl.setStyleSheet(f"color: {C['accent_glow']}; font-size: 15px; font-weight: bold; letter-spacing: 2px;")

        dept_lbl = QLabel("LAW ENFORCEMENT OFFICER", self.header)
        dept_lbl.setGeometry(180, 0, 350, 48)
        dept_lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 10px; letter-spacing: 1px;")

        self.officer_lbl = QLabel("", self.header)
        self.officer_lbl.setGeometry(W - 500, 0, 200, 48)
        self.officer_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.officer_lbl.setStyleSheet(f"color: {C['text']}; font-size: 11px; font-weight: bold;")

        self.clock_lbl = QLabel("", self.header)
        self.clock_lbl.setGeometry(W - 300, 0, 160, 48)
        self.clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.clock_lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")
        self._update_clock()
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self._update_clock)
        clock_timer.start(1000)

        self.close_btn = QPushButton("✕", self.header)
        self.close_btn.setGeometry(W - 44, 10, 28, 28)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{ background: #1a0a0a; color: {C['red']}; border: 1px solid {C['red']};
                          border-radius: 6px; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ background: #2a0f0f; }}
        """)
        self.close_btn.clicked.connect(self.exit_app)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.hide_btn = QPushButton("−", self.header)
        self.hide_btn.setGeometry(W - 76, 10, 28, 28)
        self.hide_btn.setStyleSheet(f"""
            QPushButton {{ background: {C['bg_card']}; color: {C['text_dim']}; border: 1px solid {C['border']};
                          border-radius: 6px; font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background: {C['bg_item_h']}; color: {C['text']}; }}
        """)
        self.hide_btn.clicked.connect(self.toggle_window)
        self.hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # ── Icon-only nav sidebar ─────────────────────────────────────────────
        NAV_W = 68
        self.nav_bar = QWidget(self)
        self.nav_bar.setGeometry(0, 48, NAV_W, H - 48)
        self.nav_bar.setStyleSheet(f"background-color: {C['sidebar_bg']}; border-right: 1px solid {C['border']};")

        nav_items = [
            ("📋", "INCIDENT"),
            ("🚗", "IMPOUND"),
            ("⚖", "OFFENSE"),
            ("📖", "LAWS"),
            ("📝", "CLAIM"),
            ("🗃", "EVIDENCE"),
            ("🚫", "RESTRAINING"),
            ("🔴", "WANTED"),
            ("🚙", "BOLO"),
            ("🔎", "ПСМ"),
            ("⚙", "SETTINGS"),
        ]

        self.nav_buttons = []
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label, self.nav_bar)
            btn.setText(icon)
            btn.setGeometry(6, 16 + i * 66, 56, 56)

            tooltip = QLabel(label, self.nav_bar)
            tooltip.setGeometry(6, 16 + i * 66 + 40, 56, 14)
            tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tooltip.setStyleSheet(f"color: {C['text_muted']}; font-size: 8px; letter-spacing: 0.5px; background: transparent; border: none;")

            self.nav_buttons.append(btn)

        # ── Main content area ─────────────────────────────────────────────────
        CONTENT_X = NAV_W
        CONTENT_W = W - NAV_W

        self.stack = QStackedWidget(self)
        self.stack.setGeometry(CONTENT_X, 48, CONTENT_W, H - 48)
        self.stack.setStyleSheet("background: transparent;")

        self.page_incident    = QWidget()
        self.page_impound     = QWidget()
        self.page_offense     = QWidget()
        self.page_laws        = QWidget()
        self.page_claim       = QWidget()
        self.page_evidence    = QWidget()
        self.page_restraining = QWidget()
        self.page_wanted      = QWidget()
        self.page_bolo        = QWidget()
        self.page_psm         = QWidget()
        self.page_settings    = QWidget()

        pages = [self.page_incident, self.page_impound, self.page_offense, self.page_laws,
                 self.page_claim, self.page_evidence, self.page_restraining,
                 self.page_wanted, self.page_bolo, self.page_psm, self.page_settings]
        for p in pages:
            p.setStyleSheet(f"background-color: {C['bg_dark']};")
            eff = QGraphicsOpacityEffect(p)
            eff.setOpacity(1)
            p.setGraphicsEffect(eff)
            p.opacity_effect = eff
            self.stack.addWidget(p)

        for i, btn in enumerate(self.nav_buttons):
            page = pages[i]
            btn.clicked.connect(lambda checked, b=btn, p=page: self._nav_click(b, p))

        self.init_incident_page()
        self.init_impound_page()
        self.init_offense_page()
        self.init_laws_page()
        self.init_claim_page()
        self.init_evidence_page()
        self.init_restraining_page()
        self.init_wanted_page()
        self.init_bolo_page()
        self.init_psm_page()
        self.init_settings_page()

        # Copy notification
        self.copy_notify = QLabel("✔  Скопировано", self)
        self.copy_notify.setStyleSheet(f"color: {C['green']}; font-weight: bold; font-size: 13px;"
                                        f"background: {C['bg_card']}; border: 1px solid {C['green']};"
                                        f"border-radius: 6px; padding: 6px 14px;")
        self.copy_notify.adjustSize()
        self.copy_notify.move(W // 2 - 70, H - 60)
        self.copy_notify.raise_()
        self.copy_notify_effect = QGraphicsOpacityEffect(self.copy_notify)
        self.copy_notify.setGraphicsEffect(self.copy_notify_effect)
        self.copy_notify_effect.setOpacity(0)
        self.copy_notify.hide()

        self._nav_click(self.nav_buttons[0], self.page_incident)

    def _update_clock(self):
        self.clock_lbl.setText(datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))

    def _nav_click(self, btn, page):
        for b in self.nav_buttons:
            b.setChecked(False)
            b.setActive(False)
        btn.setChecked(True)
        btn.setActive(True)
        self._switch_page(page)

    def _switch_page(self, page):
        current = self.stack.currentWidget()
        if current == page:
            return
        if current:
            anim_out = QPropertyAnimation(current.opacity_effect, b"opacity")
            anim_out.setDuration(120)
            anim_out.setStartValue(1)
            anim_out.setEndValue(0)
            def on_done():
                self.stack.setCurrentWidget(page)
                anim_in = QPropertyAnimation(page.opacity_effect, b"opacity")
                anim_in.setDuration(150)
                anim_in.setStartValue(0)
                anim_in.setEndValue(1)
                anim_in.start()
                self._anim_in = anim_in
            anim_out.finished.connect(on_done)
            anim_out.start()
            self._anim_out = anim_out
        else:
            self.stack.setCurrentWidget(page)

    # ── INCIDENT page ─────────────────────────────────────────────────────────
    def init_incident_page(self):
        p = self.page_incident
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("📋  РАПОРТ ОБ ИНЦИДЕНТЕ", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        scroll.setWidget(container)
        container.setMinimumHeight(1400)

        PAD = 20
        CW = W - 40

        y = 20
        make_field_label("Инцидент #", container).setGeometry(PAD, y, 200, 18)
        self.incident = styled_input(container, "5485")
        self.incident.setGeometry(PAD, y + 22, 180, 34)

        make_field_label("Позывной", container).setGeometry(PAD + 200, y, 200, 18)
        self.callsign = CallsignLineEdit(container)
        self.callsign.setPlaceholderText("(275) E Snake PO II")
        self.callsign.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 6px; padding: 6px 10px; color: {C['text']}; font-size: 12px;
            }}
            QLineEdit:hover {{ border: 1px solid {C['border_h']}; }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; background-color: #0f1d30; }}
        """)
        self.callsign.setGeometry(PAD + 200, y + 22, 220, 34)

        make_field_label("Время", container).setGeometry(PAD + 440, y, 200, 18)
        self.time = styled_input(container, "дд.мм.гггг чч:мм")
        self.time.setGeometry(PAD + 440, y + 22, 200, 34)

        self.now_btn = styled_button(container, "⏱  Сейчас", False)
        self.now_btn.setGeometry(PAD + 650, y + 22, 110, 34)
        self.now_btn.clicked.connect(self.set_time)

        y += 74
        make_field_label("Подозреваемый", container).setGeometry(PAD, y, 300, 18)
        self.suspect = styled_input(container, "Рег. данные подозреваемого")
        self.suspect.setGeometry(PAD, y + 22, 360, 34)

        make_field_label("Пострадавший", container).setGeometry(PAD + 380, y, 300, 18)
        self.victim = styled_input(container, "Имя Фамилия")
        self.victim.setGeometry(PAD + 380, y + 22, 360, 34)

        y += 74
        make_field_label("Место сцены", container).setGeometry(PAD, y, 600, 18)
        self.scene = styled_input(container, "Route 1 между X-Y, далее р.Альта 7200-7189")
        self.scene.setGeometry(PAD, y + 22, CW - 40, 34)

        y += 74
        make_field_label("Тип вызова", container).setGeometry(PAD, y, 300, 18)
        self.call_type = styled_combo(container)
        self.call_type.setGeometry(PAD, y + 22, 340, 34)
        self.call_type.addItems([
            "Вызов: ограбление дома", "Вызов: кража деталей",
            "Вызов: взлом авто", "Вызов: стрельба",
            "Вызов: угон", "Вызов: кража из авто",
            "Вызов: ограбление человека", "Не остановился", "Вызов: похищение",
            "Вызов: продажа оружия", "Вызов: продажа наркотиков",
            "10-55", "10-66", "Терри стоп",
            "10-55 с переходом на 10-66", "10-66 с арестом"
        ])

        make_field_label("Доставлен", container).setGeometry(PAD + 360, y, 300, 18)
        self.delivered_where = styled_combo(container)
        self.delivered_where.setGeometry(PAD + 360, y + 22, 300, 34)
        self.delivered_where.addItems([
            "LSPDV", "LSPD", "LSCSD (офис шерифа)", "SAHP", "N.O.O.S.E", "Веспуччи"
        ])

        y += 74
        make_section_label("ОБСТОЯТЕЛЬСТВА", container).setGeometry(PAD, y, 400, 18)
        y += 24

        checks = [
            ("По прибытию обнаружен подозреваемый", "cb_found"),
            ("Попытался скрыться",                  "cb_escape"),
            ("Началась погоня",                     "cb_chase"),
            ("Побег пешком",                        "cb_foot"),
            ("Был задержан",                        "cb_caught"),
            ("Доставлен",                           "cb_delivered"),
        ]
        col = 0
        for i, (txt, attr) in enumerate(checks):
            cb = styled_checkbox(container, txt)
            col_x = PAD + (col * 360)
            cb.setGeometry(col_x, y + (i % 3) * 28, 340, 24)
            setattr(self, attr, cb)
            col = 1 if i >= 2 else 0

        y += 110

        # ── Досмотр с изъятием ────────────────────────────────────────────────
        make_section_label("ДОСМОТР С ИЗЪЯТИЕМ", container).setGeometry(PAD, y, 400, 18)
        y += 24
        self.cb_weapon_search = styled_checkbox(container, "Был произведён досмотр с изъятием")
        self.cb_weapon_search.setGeometry(PAD, y, 400, 24)
        y += 32
        make_field_label("Что изъято (каждый предмет с новой строки):", container).setGeometry(PAD, y, 500, 18)
        self.weapon_items = styled_textedit(container, "Glock 19 - 1 ед\nПули 9x19 mm - 200 ед")
        self.weapon_items.setGeometry(PAD, y + 22, CW - 40, 80)
        y += 120

        make_field_label("Дополнительная информация", container).setGeometry(PAD, y, 400, 18)
        self.details = styled_textedit(container, "Подробное описание инцидента...")
        self.details.setGeometry(PAD, y + 22, CW - 40, 90)

        y += 130
        self.generate_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_btn.setGeometry(PAD, y, 160, 36)
        self.generate_btn.clicked.connect(self.generate_report)

        self.copy_btn_inc = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_inc.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_inc.clicked.connect(lambda: self.copy_text(self.result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.result = styled_textedit(container, "Сгенерированный рапорт появится здесь...")
        self.result.setGeometry(PAD, y, CW - 40, 180)

    # ── IMPOUND page ──────────────────────────────────────────────────────────
    def init_impound_page(self):
        p = self.page_impound
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🚗  ЭВАКУАЦИЯ ТРАНСПОРТА", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(700)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60

        fields_row1 = [
            ("Дата", "imp_date", "дд.мм.гггг"),
            ("Номерной знак", "imp_plate", "AAA 000"),
            ("Рег. номер владельца", "imp_reg", "Рег. данные"),
            ("Модель", "imp_model", "Make Model"),
        ]
        fields_row2 = [
            ("Цвет", "imp_color", "Цвет"),
            ("Причина", "imp_reason", "Причина эвакуации"),
            ("Куда", "imp_where", "Место назначения"),
            ("Офицер", "imp_officer", "Позывной"),
        ]

        y = 20
        col_w = CW // 4
        for i, (label, attr, ph) in enumerate(fields_row1):
            x = PAD + i * (col_w + 12)
            make_field_label(label, container).setGeometry(x, y, col_w, 18)
            inp = styled_input(container, ph)
            inp.setGeometry(x, y + 22, col_w, 34)
            setattr(self, attr, inp)

        y += 74
        for i, (label, attr, ph) in enumerate(fields_row2):
            x = PAD + i * (col_w + 12)
            make_field_label(label, container).setGeometry(x, y, col_w, 18)
            if attr == "imp_officer":
                inp = CallsignLineEdit(container)
                inp.setPlaceholderText(ph)
                inp.setStyleSheet(f"""
                    QLineEdit {{
                        background-color: {C['bg_input']}; border: 1px solid {C['border']};
                        border-radius: 6px; padding: 6px 10px; color: {C['text']}; font-size: 12px;
                    }}
                    QLineEdit:hover {{ border: 1px solid {C['border_h']}; }}
                    QLineEdit:focus {{ border: 1px solid {C['accent']}; background-color: #0f1d30; }}
                """)
            else:
                inp = styled_input(container, ph)
            inp.setGeometry(x, y + 22, col_w, 34)
            setattr(self, attr, inp)

        y += 74
        self.generate_imp_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_imp_btn.setGeometry(PAD, y, 160, 36)
        self.generate_imp_btn.clicked.connect(self.generate_impound)

        self.copy_btn_imp = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_imp.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_imp.clicked.connect(lambda: self.copy_text(self.imp_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.imp_result = styled_textedit(container, "Сгенерированный рапорт...")
        self.imp_result.setGeometry(PAD, y, CW, 200)

    # ── OFFENSE page ──────────────────────────────────────────────────────────
    def init_offense_page(self):
        p = self.page_offense
        self.offense_open_block = False
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("⚖  УГОЛОВНОЕ ВЗЫСКАНИЕ", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W - 200, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(900)
        scroll.setWidget(container)

        PAD, CW = 20, W - 260

        y = 20
        fields_r1 = [
            ("Номер", "off_number", "001"),
            ("Дата", "off_date", "дд.мм.гггг"),
            ("Рег. данные", "off_reg", "Регистрационный №"),
        ]
        col_w = (CW - PAD * 2) // 3
        for i, (label, attr, ph) in enumerate(fields_r1):
            x = PAD + i * (col_w + 12)
            make_field_label(label, container).setGeometry(x, y, col_w, 18)
            inp = styled_input(container, ph)
            inp.setGeometry(x, y + 22, col_w, 34)
            setattr(self, attr, inp)

        y += 74
        make_field_label("Имя и Фамилия", container).setGeometry(PAD, y, col_w, 18)
        self.off_name = styled_input(container, "Имя Фамилия")
        self.off_name.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Статья", container).setGeometry(PAD + col_w + 12, y, col_w, 18)
        self.off_article = styled_input(container, "Ст. 60")
        self.off_article.setGeometry(PAD + col_w + 12, y + 22, col_w, 34)

        make_field_label("Срок (мин)", container).setGeometry(PAD + (col_w + 12) * 2, y, col_w, 18)
        self.off_time = styled_input(container, "0")
        self.off_time.setGeometry(PAD + (col_w + 12) * 2, y + 22, col_w, 34)
        self.off_time.textChanged.connect(self.calculate_release_time)

        y += 74
        make_field_label("Штраф ($)", container).setGeometry(PAD, y, col_w, 18)
        self.off_fine = styled_input(container, "0")
        self.off_fine.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Время выхода", container).setGeometry(PAD + col_w + 12, y, col_w, 18)
        self.off_release = styled_input(container, "чч:мм")
        self.off_release.setGeometry(PAD + col_w + 12, y + 22, col_w, 34)

        make_field_label("Личные вещи", container).setGeometry(PAD + (col_w + 12) * 2, y, col_w, 18)
        self.off_items = styled_input(container, "Список вещей")
        self.off_items.setGeometry(PAD + (col_w + 12) * 2, y + 22, col_w, 34)

        y += 74
        make_field_label("Участок", container).setGeometry(PAD, y, col_w, 18)
        self.off_dept = styled_combo(container)
        self.off_dept.setGeometry(PAD, y + 22, col_w, 34)
        self.off_dept.addItems(["LSPD", "LSCSD", "LSPDV", "SAHP", "N.O.O.S.E"])

        make_field_label("Позывной", container).setGeometry(PAD + col_w + 12, y, col_w, 18)
        self.off_callsign = CallsignLineEdit(container)
        self.off_callsign.setPlaceholderText("(275) E Snake PO II")
        self.off_callsign.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 6px; padding: 6px 10px; color: {C['text']}; font-size: 12px;
            }}
            QLineEdit:hover {{ border: 1px solid {C['border_h']}; }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; background-color: #0f1d30; }}
        """)
        self.off_callsign.setGeometry(PAD + col_w + 12, y + 22, col_w, 34)

        y += 74
        self.generate_off_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_off_btn.setGeometry(PAD, y, 160, 36)
        self.generate_off_btn.clicked.connect(self.generate_offense)

        self.copy_btn_off = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_off.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_off.clicked.connect(lambda: self.copy_text(self.off_result))

        self.off_x2_btn = styled_button(container, "✚  X2", False)
        self.off_x2_btn.setGeometry(PAD + 330, y, 100, 36)
        self.off_x2_btn.clicked.connect(self.offense_x2)

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.off_result = styled_textedit(container, "Сгенерированное взыскание...")
        self.off_result.setGeometry(PAD, y, CW, 220)

        # Quick articles panel
        art_panel = QWidget(p)
        art_panel.setGeometry(W - 196, 44, 196, H - 44)
        art_panel.setStyleSheet(f"background: {C['bg_panel']}; border-left: 1px solid {C['border']};")

        lbl2 = QLabel("ПОПУЛЯРНЫЕ\nСТАТЬИ", art_panel)
        lbl2.setGeometry(12, 14, 172, 32)
        lbl2.setStyleSheet(f"color: {C['text_dim']}; font-size: 9px; font-weight: bold; letter-spacing: 1px;")

        article_map = {
            "Неповиновение": "60",
            "Незак. оборот оружия": "41.1",
            "Похищение": "27",
            "Использ. оружия": "53",
            "Кража": "31.1",
            "Грабёж": "32",
            "Разбой": "33",
            "Нарк. до 6 ед.": "39.1",
            "Нарк. 6–50 ед.": "39.2",
            "Нарк. от 50 ед.": "39.3",
            "Сбыт оружия": "41.3",
            "Сбыт оружия (кр.)": "41.4",
            "Кража гос. оружия": "41.6",
        }
        self.article_buttons = []
        for j, (name, art) in enumerate(article_map.items()):
            btn = QPushButton(name, art_panel)
            btn.setGeometry(10, 60 + j * 48, 176, 38)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['bg_card']};
                    border: 1px solid {C['border']};
                    border-radius: 6px;
                    color: {C['text']};
                    font-size: 11px;
                    text-align: left;
                    padding-left: 10px;
                }}
                QPushButton:hover {{
                    background: {C['accent']};
                    border: 1px solid {C['accent']};
                    color: white;
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, a=art: self.insert_article(a))
            self.article_buttons.append(btn)

    # ── LAWS page ─────────────────────────────────────────────────────────────
    def init_laws_page(self):
        p = self.page_laws
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("📖  КОДЕКС ШТАТА САН-АНДРЕАС", hdr)
        lbl.setGeometry(16, 0, 500, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        LIST_W = 300
        self.laws_search = styled_input(p, "🔍  Поиск статьи...")
        self.laws_search.setGeometry(0, 44, LIST_W, 40)
        self.laws_search.setStyleSheet(self.laws_search.styleSheet() +
            "border-radius: 0px; border-left: none; border-top: none; border-right: 1px solid #1f3050;")
        self.laws_search.textChanged.connect(self.search_laws)

        self.laws_list = QListWidget(p)
        self.laws_list.setGeometry(0, 84, LIST_W, H - 84 - 110)
        self.laws_list.setStyleSheet(f"""
            QListWidget {{
                background: {C['bg_panel']};
                border: none;
                border-right: 1px solid {C['border']};
                color: {C['text']};
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {C['divider']};
            }}
            QListWidget::item:selected {{
                background: {C['accent']};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {C['bg_item_h']};
            }}
        """)
        self.laws_list.itemClicked.connect(self.show_law_text)

        # ── Selected articles basket ──────────────────────────────────────────
        self._selected_articles = []
        self._laws_punishment_map = {}
        basket_y = H - 110
        basket = QWidget(p)
        basket.setGeometry(0, basket_y, LIST_W, 110)
        basket.setStyleSheet(f"background: {C['bg_panel']}; border-top: 1px solid {C['border']}; border-right: 1px solid {C['border']};")

        lbl_sel = QLabel("Выбранные статьи:", basket)
        lbl_sel.setGeometry(8, 6, LIST_W - 16, 16)
        lbl_sel.setStyleSheet(f"color: {C['text_dim']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")

        self.laws_selected_lbl = QLabel("—", basket)
        self.laws_selected_lbl.setGeometry(8, 24, LIST_W - 16, 36)
        self.laws_selected_lbl.setWordWrap(True)
        self.laws_selected_lbl.setStyleSheet(f"color: {C['accent_glow']}; font-size: 11px; font-weight: bold;")

        btn_transfer = QPushButton("→ Перенести в Offense", basket)
        btn_transfer.setGeometry(8, 64, 136, 30)
        btn_transfer.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; border: none; border-radius: 6px;
                color: white; font-size: 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
        """)
        btn_transfer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_transfer.clicked.connect(self._transfer_articles_to_offense)

        btn_clear_sel = QPushButton("Очистить", basket)
        btn_clear_sel.setGeometry(152, 64, 136, 30)
        btn_clear_sel.setStyleSheet(f"""
            QPushButton {{
                background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 6px;
                color: {C['text_dim']}; font-size: 10px;
            }}
            QPushButton:hover {{ background: {C['bg_item_h']}; color: {C['text']}; }}
        """)
        btn_clear_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_sel.clicked.connect(self._clear_selected_articles)

        self.laws_text = QTextBrowser(p)
        self.laws_text.setGeometry(LIST_W, 44, W - LIST_W, H - 44)
        self.laws_text.setOpenLinks(False)
        self.laws_text.anchorClicked.connect(self._law_paragraph_clicked)
        self.laws_text.setStyleSheet(f"""
            QTextEdit {{
                background: {C['bg_dark']};
                border: none;
                color: {C['text']};
                font-size: 13px;
                padding: 20px;
                line-height: 1.6;
            }}
        """)

        QTimer.singleShot(150, self.populate_laws_list)

    # ── CLAIM page ────────────────────────────────────────────────────────────
    def init_claim_page(self):
        p = self.page_claim
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("📝  ЗАЯВЛЕНИЕ ГРАЖДАНИНА", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(700)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60
        col_w = (CW - PAD) // 2

        y = 20
        make_field_label("Номер заявления", container).setGeometry(PAD, y, col_w, 18)
        self.claim_number = styled_input(container, "№ заявления")
        self.claim_number.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Время и дата происшествия", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.claim_datetime = styled_input(container, "дд.мм.гггг чч:мм")
        self.claim_datetime.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Заявитель / Пострадавший", container).setGeometry(PAD, y, col_w, 18)
        self.claim_victim = styled_input(container, "Имя Фамилия")
        self.claim_victim.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Подозреваемый", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.claim_suspect = styled_input(container, "Имя Фамилия")
        self.claim_suspect.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Дополнительная информация", container).setGeometry(PAD, y, CW, 18)
        self.claim_details = styled_textedit(container, "Подробное описание...")
        self.claim_details.setGeometry(PAD, y + 22, CW, 100)

        y += 140
        self.generate_claim_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_claim_btn.setGeometry(PAD, y, 160, 36)
        self.generate_claim_btn.clicked.connect(self.generate_claim)

        self.copy_btn_claim = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_claim.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_claim.clicked.connect(lambda: self.copy_text(self.claim_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.claim_result = styled_textedit(container, "Сгенерированное заявление...")
        self.claim_result.setGeometry(PAD, y, CW, 180)

    # ── EVIDENCE page ─────────────────────────────────────────────────────────
    def init_evidence_page(self):
        p = self.page_evidence
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🗃  КОМНАТА УЛИК (EVIDENCE ROOM)", hdr)
        lbl.setGeometry(16, 0, 500, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(700)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60

        y = 20
        make_field_label("Действие", container).setGeometry(PAD, y, 200, 18)
        self.evidence_action = styled_combo(container)
        self.evidence_action.setGeometry(PAD, y + 22, 200, 34)
        self.evidence_action.addItems(["Положил", "Взял"])

        make_field_label("Позывной", container).setGeometry(PAD + 220, y, 300, 18)
        self.evidence_callsign = CallsignLineEdit(container)
        self.evidence_callsign.setPlaceholderText("(275) E Snake PO II")
        self.evidence_callsign.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['bg_input']}; border: 1px solid {C['border']};
                border-radius: 6px; padding: 6px 10px; color: {C['text']}; font-size: 12px;
            }}
            QLineEdit:hover {{ border: 1px solid {C['border_h']}; }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; background-color: #0f1d30; }}
        """)
        self.evidence_callsign.setGeometry(PAD + 220, y + 22, 300, 34)

        y += 74
        make_field_label("Имя и Фамилия офицера", container).setGeometry(PAD, y, CW, 18)
        self.evidence_name = styled_input(container, "Имя Фамилия")
        self.evidence_name.setGeometry(PAD, y + 22, 400, 34)

        y += 74
        make_field_label("Что положил / взял", container).setGeometry(PAD, y, CW, 18)
        self.evidence_items = styled_textedit(container, "Список предметов...")
        self.evidence_items.setGeometry(PAD, y + 22, CW, 120)

        y += 160
        self.generate_evidence_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_evidence_btn.setGeometry(PAD, y, 160, 36)
        self.generate_evidence_btn.clicked.connect(self.generate_evidence)

        self.copy_btn_evidence = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_evidence.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_evidence.clicked.connect(lambda: self.copy_text(self.evidence_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.evidence_result = styled_textedit(container, "Сгенерированный акт улик...")
        self.evidence_result.setGeometry(PAD, y, CW, 180)

    # ── RESTRAINING page ──────────────────────────────────────────────────────
    def init_restraining_page(self):
        p = self.page_restraining
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🚫  ЗАПРЕТИТЕЛЬНЫЙ ПРИКАЗ", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(900)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60
        col_w = (CW - 20) // 3

        y = 20
        make_field_label("Тип приказа", container).setGeometry(PAD, y, col_w, 18)
        self.res_type = styled_combo(container)
        self.res_type.setGeometry(PAD, y + 22, col_w, 34)
        self.res_type.addItems(["Обязующий приказ", "Ограждающий приказ", "Запретительный приказ"])

        make_field_label("Дата", container).setGeometry(PAD + col_w + 10, y, col_w, 18)
        self.res_date = styled_input(container, "дд.мм.гггг")
        self.res_date.setGeometry(PAD + col_w + 10, y + 22, col_w, 34)

        make_field_label("Номер приказа", container).setGeometry(PAD + (col_w + 10) * 2, y, col_w, 18)
        self.res_number = styled_input(container, "№ приказа")
        self.res_number.setGeometry(PAD + (col_w + 10) * 2, y + 22, col_w, 34)

        y += 74
        make_field_label("Рег. данные", container).setGeometry(PAD, y, col_w, 18)
        self.res_reg = styled_input(container, "Рег. №")
        self.res_reg.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Имя и Фамилия", container).setGeometry(PAD + col_w + 10, y, col_w, 18)
        self.res_name = styled_input(container, "Имя Фамилия")
        self.res_name.setGeometry(PAD + col_w + 10, y + 22, col_w, 34)

        make_field_label("Срок действия до", container).setGeometry(PAD + (col_w + 10) * 2, y, col_w, 18)
        self.res_until = styled_input(container, "дд.мм.гггг")
        self.res_until.setGeometry(PAD + (col_w + 10) * 2, y + 22, col_w, 34)

        y += 74
        make_field_label("Что обязан сделать / что запрещено", container).setGeometry(PAD, y, CW, 18)
        self.res_text = styled_textedit(container, "Содержание приказа...")
        self.res_text.setGeometry(PAD, y + 22, CW, 90)

        y += 130
        self.res_notified = styled_checkbox(container, "УВЕДОМЛЁН")
        self.res_notified.setGeometry(PAD, y, 160, 28)

        make_field_label("Статус приказа", container).setGeometry(PAD + 180, y - 6, 200, 18)
        self.res_status = styled_combo(container)
        self.res_status.setGeometry(PAD + 180, y + 16, 220, 34)
        self.res_status.addItems(["ИСПОЛНЕНО", "НЕ ИСПОЛНЕНО"])

        y += 60
        make_field_label("Примечание", container).setGeometry(PAD, y, CW, 18)
        self.res_note = styled_textedit(container, "Дополнительные пометки...")
        self.res_note.setGeometry(PAD, y + 22, CW, 80)

        y += 120
        self.generate_res_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_res_btn.setGeometry(PAD, y, 160, 36)
        self.generate_res_btn.clicked.connect(self.generate_restraining)

        self.copy_btn_res = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_res.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_res.clicked.connect(lambda: self.copy_text(self.res_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.res_result = styled_textedit(container, "Сгенерированный приказ...")
        self.res_result.setGeometry(PAD, y, CW, 120)

    # ── WANTED page ───────────────────────────────────────────────────────────
    def init_wanted_page(self):
        p = self.page_wanted
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🔴  РАЗЫСКИВАЕТСЯ ПОДОЗРЕВАЕМЫЙ (WANTED)", hdr)
        lbl.setGeometry(16, 0, 500, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(700)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60
        col_w = (CW - 20) // 2

        y = 20
        make_field_label("Номер записи (#)", container).setGeometry(PAD, y, col_w, 18)
        self.wanted_number = styled_input(container, "1519")
        self.wanted_number.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Имя и Фамилия подозреваемого", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.wanted_name = styled_input(container, "Damien Stone")
        self.wanted_name.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Рег. номер", container).setGeometry(PAD, y, col_w, 18)
        self.wanted_plate = styled_input(container, "55YF")
        self.wanted_plate.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Причина розыска (статья)", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.wanted_reason = styled_input(container, "27")
        self.wanted_reason.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Прикреплённый инцидент-репорт #", container).setGeometry(PAD, y, col_w, 18)
        self.wanted_incident = styled_input(container, "5171")
        self.wanted_incident.setGeometry(PAD, y + 22, col_w, 34)

        y += 74
        make_field_label("Доп. информация", container).setGeometry(PAD, y, CW, 18)
        self.wanted_info = styled_textedit(container, "Участвовал в похищении человека...")
        self.wanted_info.setGeometry(PAD, y + 22, CW, 90)

        y += 130
        self.generate_wanted_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_wanted_btn.setGeometry(PAD, y, 160, 36)
        self.generate_wanted_btn.clicked.connect(self.generate_wanted)

        self.copy_btn_wanted = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_wanted.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_wanted.clicked.connect(lambda: self.copy_text(self.wanted_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.wanted_result = styled_textedit(container, "Сгенерированный WANTED...")
        self.wanted_result.setGeometry(PAD, y, CW, 180)

    # ── BOLO page ─────────────────────────────────────────────────────────────
    def init_bolo_page(self):
        p = self.page_bolo
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🚙  РАЗЫСКИВАЕТСЯ ТРАНСПОРТ (BOLO)", hdr)
        lbl.setGeometry(16, 0, 500, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(700)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60
        col_w = (CW - 20) // 2

        y = 20
        make_field_label("Номер записи (#)", container).setGeometry(PAD, y, col_w, 18)
        self.bolo_number = styled_input(container, "298")
        self.bolo_number.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Марка / Модель ТС", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.bolo_model = styled_input(container, "Victor")
        self.bolo_model.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Рег. номер ТС", container).setGeometry(PAD, y, col_w, 18)
        self.bolo_plate = styled_input(container, "0OFO376B")
        self.bolo_plate.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Владелец (рег. данные)", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.bolo_owner = styled_input(container, "06TQ")
        self.bolo_owner.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Причина розыска", container).setGeometry(PAD, y, col_w, 18)
        self.bolo_reason = styled_input(container, "Похищение с Черного Фонаря")
        self.bolo_reason.setGeometry(PAD, y + 22, col_w, 34)

        make_field_label("Прикреплённый инцидент-репорт #", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.bolo_incident = styled_input(container, "4949")
        self.bolo_incident.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)

        y += 74
        make_field_label("Доп. информация", container).setGeometry(PAD, y, CW, 18)
        self.bolo_info = styled_textedit(container, "В случае обнаружения машины БЕЗ владельца...")
        self.bolo_info.setGeometry(PAD, y + 22, CW, 90)

        y += 130
        self.generate_bolo_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_bolo_btn.setGeometry(PAD, y, 160, 36)
        self.generate_bolo_btn.clicked.connect(self.generate_bolo)

        self.copy_btn_bolo = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_bolo.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_bolo.clicked.connect(lambda: self.copy_text(self.bolo_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.bolo_result = styled_textedit(container, "Сгенерированный BOLO...")
        self.bolo_result.setGeometry(PAD, y, CW, 180)

    # ── ПСМ page ──────────────────────────────────────────────────────────────
    def init_psm_page(self):
        p = self.page_psm
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("🔎  ПЕРВЫЕ СЛЕДСТВЕННЫЕ МЕРОПРИЯТИЯ (ПСМ)", hdr)
        lbl.setGeometry(16, 0, 600, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        scroll = QScrollArea(p)
        scroll.setGeometry(0, 44, W, H - 44)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg_dark']};")
        container.setMinimumHeight(1100)
        scroll.setWidget(container)

        PAD, CW = 20, W - 60
        col_w = (CW - 20) // 2

        y = 20
        make_field_label("Департамент", container).setGeometry(PAD, y, col_w, 18)
        self.psm_dept = styled_combo(container)
        self.psm_dept.setGeometry(PAD, y + 22, col_w, 34)
        self.psm_dept.addItems(["LSPD", "SAHP", "LSCSD", "N.O.O.S.E"])

        make_field_label("Тип происшествия", container).setGeometry(PAD + col_w + 20, y, col_w, 18)
        self.psm_type = styled_combo(container)
        self.psm_type.setGeometry(PAD + col_w + 20, y + 22, col_w, 34)
        self.psm_type.addItems([
            "Ограбление магазина 24/7",
            "Угон транспортного средства",
            "Нападение на офицера",
            "Нападение на офицера с кражей гос. имущества",
            "Угон транспорта правоохранительных органов",
            "Угон транспорта EMS/FD",
            "Перестрелка",
            "Найден труп",
        ])
        self.psm_type.currentTextChanged.connect(self._psm_type_changed)

        y += 74
        make_field_label("Место происшествия / дистрикт", container).setGeometry(PAD, y, CW - 40, 18)
        self.psm_location = styled_input(container, "Конкретное место или номер дистрикта...")
        self.psm_location.setGeometry(PAD, y + 22, CW - 40, 34)

        y += 74
        self.psm_details_label = make_section_label("ДЕТАЛИ РАССЛЕДОВАНИЯ", container)
        self.psm_details_label.setGeometry(PAD, y, 400, 18)
        y += 24

        # ── Checkboxes (shown for non-24/7 types) ─────────────────────────────
        self.psm_checks_widget = QWidget(container)
        self.psm_checks_widget.setGeometry(PAD, y, CW, 210)
        self.psm_checks_widget.setStyleSheet("background: transparent;")

        cw      = self.psm_checks_widget
        FRAME_W = (CW - 16) // 2
        CB_W    = FRAME_W - 24

        frame_style = (
            f"QFrame {{ background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 8px; }}"
        )
        lbl_style = (
            f"color: {C['text_dim']}; font-size: 9px; font-weight: bold; letter-spacing: 1.5px;"
            " background: transparent; border: none;"
        )

        # ── Left frame — гос. имущество / офицер ───────────────────────────
        left_f = QFrame(cw)
        left_f.setGeometry(0, 0, FRAME_W, 200)
        left_f.setStyleSheet(frame_style)

        lbl_l = QLabel("ГОС. ИМУЩЕСТВО / ОФИЦЕР", left_f)
        lbl_l.setGeometry(12, 10, CB_W, 16)
        lbl_l.setStyleSheet(lbl_style)

        lcy = 34
        self.psm_cb_theft = styled_checkbox(left_f, "Кража имущества с авто")
        self.psm_cb_theft.setGeometry(12, lcy, CB_W, 24); lcy += 30
        self.psm_cb_prints_car = styled_checkbox(left_f, "Потожировые следы с авто")
        self.psm_cb_prints_car.setGeometry(12, lcy, CB_W, 24); lcy += 30
        self.psm_cb_dashcam = styled_checkbox(left_f, "Изучены записи с Dashcam")
        self.psm_cb_dashcam.setGeometry(12, lcy, CB_W, 24); lcy += 30
        self.psm_cb_officer_gear = styled_checkbox(left_f, "Кража снаряжения офицера")
        self.psm_cb_officer_gear.setGeometry(12, lcy, CB_W, 24)

        # ── Right frame — против гражданских ───────────────────────────────
        right_f = QFrame(cw)
        right_f.setGeometry(FRAME_W + 16, 0, FRAME_W, 200)
        right_f.setStyleSheet(frame_style)

        lbl_r = QLabel("ПРОТИВ ГРАЖДАНСКИХ", right_f)
        lbl_r.setGeometry(12, 10, CB_W, 16)
        lbl_r.setStyleSheet(lbl_style)

        rcy = 34
        self.psm_cb_cameras = styled_checkbox(right_f, "Запрошен видео с камер")
        self.psm_cb_cameras.setGeometry(12, rcy, CB_W, 24); rcy += 30
        self.psm_cb_witnesses = styled_checkbox(right_f, "Опрос свидетелей из числа местных жителей")
        self.psm_cb_witnesses.setGeometry(12, rcy, CB_W, 24); rcy += 30
        self.psm_cb_shells = styled_checkbox(right_f, "Собраны гильзы для экспертизы")
        self.psm_cb_shells.setGeometry(12, rcy, CB_W, 24); rcy += 30
        self.psm_cb_prints_room = styled_checkbox(right_f, "Потожировые следы с помещения")
        self.psm_cb_prints_room.setGeometry(12, rcy, CB_W, 24); rcy += 30
        self.psm_cb_prints_civ_car = styled_checkbox(right_f, "Отпечатки с гражданского авто")
        self.psm_cb_prints_civ_car.setGeometry(12, rcy, CB_W, 24)

        y += 226

        self.generate_psm_btn = styled_button(container, "⚙  Сгенерировать")
        self.generate_psm_btn.setGeometry(PAD, y, 160, 36)
        self.generate_psm_btn.clicked.connect(self.generate_psm)

        self.copy_btn_psm = styled_button(container, "📋  Скопировать", False)
        self.copy_btn_psm.setGeometry(PAD + 170, y, 150, 36)
        self.copy_btn_psm.clicked.connect(lambda: self.copy_text(self.psm_result))

        y += 50
        make_section_label("РЕЗУЛЬТАТ", container).setGeometry(PAD, y, 400, 18)
        y += 22
        self.psm_result = styled_textedit(container, "Сгенерированный ПСМ...")
        self.psm_result.setGeometry(PAD, y, CW, 220)

        # Initial visibility
        self._psm_type_changed("Ограбление магазина 24/7")

    def _psm_type_changed(self, text):
        visible = text != "Ограбление магазина 24/7"
        self.psm_checks_widget.setVisible(visible)
        self.psm_details_label.setVisible(visible)

    def _psm_dept_prefix(self):
        d = self.psm_dept.currentText()
        if d == "LSCSD":
            return "Помощник шерифа LSCSD"
        elif d == "SAHP":
            return "Офицер SAHP"
        elif d == "N.O.O.S.E":
            return "Агент N.O.O.S.E"
        else:
            return f"Офицер {d}"

    def generate_psm(self):
        prefix   = self._psm_dept_prefix()
        ptype    = self.psm_type.currentText()
        location = self.psm_location.text().strip()
        PING     = "<@&1156593586951958630>"

        if ptype == "Ограбление магазина 24/7":
            loc_str = f", {location}" if location else ""
            text = (
                f"Расследование {PING}\n"
                "```cs\n"
                f"#{prefix}, совместно с криминалистами, проводит первые следственные мероприятия на сцене по ограблению магазина 24/7{loc_str}:\n"
                '1. "Опрос работников магазина"\n'
                "  1.1 Какую сумму похитил грабитель?\n"
                "  1.2 Что помимо денег могло быть похищено?\n"
                '2. "Записи с камер видеонаблюдения"\n'
                "  2.1 Как проходило ограбление? Когда прибыли подозреваемые?\n"
                "  2.2 Как выглядели подозреваемые, видны ли какие-либо отличительные признаки? Если снимали маски, будут ли с кем-либо визуальные совпадения?\n"
                "  2.3 Будут ли совпадения с базой данных LEO о подозреваемых?\n"
                '3. "Криминалисты проводят обследования места преступления"\n'
                "  3.1 Проводится сбор потожировых следов с сейфа, кассы, дверных ручек. С кем будут совпадения?\n"
                "  3.2 Дополнительно осматривая магазин могут ли найти какой либо мусор, окурки или же другие предметы, на которое могут остаться ДНК?\n"
                "```"
            )
            self.type_text(self.psm_result, text)
            return

        # ── Остальные типы ────────────────────────────────────────────────────
        type_map = {
            "Угон транспортного средства":                  "угону гражданского транспорта",
            "Нападение на офицера":                         "нападению на офицера",
            "Нападение на офицера с кражей гос. имущества": "нападению на офицера с кражей государственного имущества",
            "Угон транспорта правоохранительных органов":   "угону транспорта правоохранительных органов",
            "Угон транспорта EMS/FD":                       "угону транспорта EMS/FD",
            "Перестрелка":                                  "перестрелке",
            "Найден труп":                                  "обнаружению трупа",
        }
        desc = type_map.get(ptype, ptype.lower())
        location_part = f", {location}:" if location else ":"
        header = f"#{prefix}, совместно с криминалистами, проводит первые следственные мероприятия на сцене по {desc}{location_part}"

        sections = []

        # ── Гос. имущество / офицер ───────────────────────────────────────────
        if self.psm_cb_theft.isChecked():
            sections.append(
                '"Проводится инвентаризация по служебному снаряжению транспорта:"\n'
                "   1. Что именно пропало из служебного транспорта?\n"
                "   2. Удастся ли по камерам или свидетелям установить, кто именно забрал снаряжение из транспорта?"
            )

        if self.psm_cb_prints_car.isChecked():
            sections.append(
                '"Снимаются отпечатки пальцев и потожировые следы со служебного транспорта:"\n'
                "   1. Снимаются следы с руля, АКПП, дверных ручек, дэш-панели. С кем совпадение по базе LEO?\n"
                "   2. Будут ли найдены ДНК-следы? Удастся ли идентифицировать личность?"
            )

        if self.psm_cb_dashcam.isChecked():
            sections.append(
                '"Изучаются записи с Dashcam служебного транспорта:"\n'
                "   1. Воссоздается полная хронология событий. Что именно зафиксировано на записи?\n"
                "   2. Удастся ли идентифицировать лица подозреваемых? С кем совпадение по базе LEO?\n"
                "   3. Если подозреваемые использовали транспорт — удалось ли зафиксировать рег. номер?"
            )

        if self.psm_cb_officer_gear.isChecked():
            sections.append(
                '"Проводится инвентаризация по украденным снаряжениям офицера:"\n'
                "   1. Что именно пропало из снаряжения офицера?\n"
                "   2. Сможет ли камера или свидетели описать того, кто украл снаряжение офицера?"
            )

        # ── Против гражданских ────────────────────────────────────────────────
        if self.psm_cb_cameras.isChecked():
            sections.append(
                '"Запрашиваются видео с камер видеонаблюдения CCTV:"\n'
                "   1. Воссоздается полная хронология сцены. Что именно произошло?\n"
                "   2. Как выглядели подозреваемые? (цвет кожи, во что одеты, отличительные черты)\n"
                "   3. Если подозреваемые были без масок — их лица пробиваются по базе LEO. С кем совпадение?\n"
                "   4. Если был транспорт — удалось ли зафиксировать рег. номер? Кто владелец?"
            )

        if self.psm_cb_witnesses.isChecked():
            sections.append(
                '"Опрашиваются свидетели места преступления:"\n'
                "   1. Как свидетель опишет подозреваемых? (цвет кожи, во что одеты, отличительные черты)\n"
                "   2. Сколько человек было? В каком направлении скрылись?\n"
                "   3. Был ли транспорт? Марка, цвет, запомнили ли рег. номер или его часть?"
            )

        if self.psm_cb_shells.isChecked():
            sections.append(
                '"Собираются гильзы и отправляются на баллистическую, дактилоскопическую и ДНК-экспертизы:"\n'
                "   1. Какому калибру соответствует размер гильз? Какая модель оружия могла использоваться?\n"
                "   2. Будут ли найдены четкие отпечатки пальцев на гильзах? С кем совпадение по базе LEO?\n"
                "   3. Удастся ли снять ДНК-следы с гильз? Кому они принадлежат?"
            )

        if self.psm_cb_prints_room.isChecked():
            sections.append(
                '"Криминалисты проводят сбор потожировых следов с места преступления:"\n'
                "   1. Снимаются следы с мебели, дверных ручек, замков и поверхностей. С кем совпадение по базе LEO?\n"
                "   2. Осматривается территория на наличие окурков, мусора или предметов с возможными следами ДНК?\n"
                "   3. Удастся ли идентифицировать личность?"
            )

        if self.psm_cb_prints_civ_car.isChecked():
            sections.append(
                '"Снимаются отпечатки пальцев и потожировые следы с гражданского транспорта:"\n'
                "   1. Будут ли найдены какие-либо посторонние следы ДНК/Отпечатки пальцев ?\n"
                "   2. Будут ли совпадения по базе LEO? Кому принадлежат отпечатки?\n"
                "   3. Удастся ли идентифицировать личность через ДНК-экспертизу?"
            )

        body = "\n".join(sections) if sections else ""
        text = (
            f"Расследование {PING}\n"
            "```cs\n"
            f"{header}\n"
            + (body + "\n" if body else "")
            + "```"
        )
        self.type_text(self.psm_result, text)

    # ── SETTINGS page ─────────────────────────────────────────────────────────
    def init_settings_page(self):
        p = self.page_settings
        W, H = 1132, 772

        hdr = QWidget(p)
        hdr.setGeometry(0, 0, W, 44)
        hdr.setStyleSheet(f"background: {C['bg_panel']}; border-bottom: 1px solid {C['border']};")
        lbl = QLabel("⚙  НАСТРОЙКИ", hdr)
        lbl.setGeometry(16, 0, 400, 44)
        lbl.setStyleSheet(f"color: {C['text']}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")

        card = QWidget(p)
        card.setGeometry(20, 64, 500, 285)
        card.setStyleSheet(f"background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 10px;")

        make_section_label("ГОРЯЧИЕ КЛАВИШИ", card).setGeometry(20, 20, 300, 18)
        make_field_label("Горячая клавиша для показа/скрытия MDT", card).setGeometry(20, 46, 400, 18)

        self.hotkey_input = AnimatedLineEdit(card)
        self.hotkey_input.setText(self.hotkey)
        self.hotkey_input.setGeometry(20, 68, 200, 34)
        self.hotkey_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg_input']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {C['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {C['accent']}; }}
        """)

        make_section_label("ТЕМА ОФОРМЛЕНИЯ", card).setGeometry(20, 120, 300, 18)
        make_field_label("Цвет интерфейса", card).setGeometry(20, 146, 300, 18)

        self.theme_box = styled_combo(card)
        self.theme_box.setGeometry(20, 168, 200, 34)
        self.theme_box.addItems(["blue", "dark", "green"])
        self.theme_box.setCurrentText(self.theme)

        self.save_settings_btn = styled_button(card, "💾  Сохранить")
        self.save_settings_btn.setGeometry(20, 218, 150, 36)
        self.save_settings_btn.clicked.connect(self.save_settings)

        change_btn = styled_button(card, "🔄  Сменить офицера", False)
        change_btn.setGeometry(185, 218, 170, 36)
        change_btn.clicked.connect(self._change_officer)

        ver_lbl = QLabel(f"MDT версия {CURRENT_VERSION}", p)
        ver_lbl.setGeometry(20, 365, 300, 24)
        ver_lbl.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px;")

    # ── Window events ─────────────────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        W, H = self.width(), self.height()

        if hasattr(self, 'header'):
            self.header.setGeometry(0, 0, W, 48)

            if hasattr(self, 'close_btn'):
                self.close_btn.move(W - 44, 10)

            if hasattr(self, 'hide_btn'):
                self.hide_btn.move(W - 76, 10)

            if hasattr(self, 'clock_lbl'):
                self.clock_lbl.setGeometry(W - 300, 0, 160, 48)

            if hasattr(self, 'officer_lbl'):
                self.officer_lbl.setGeometry(W - 500, 0, 200, 48)

        if hasattr(self, 'nav_bar'):
            self.nav_bar.setGeometry(0, 48, 68, H - 48)

        if hasattr(self, 'stack'):
            self.stack.setGeometry(68, 48, W - 68, H - 48)

        if hasattr(self, 'copy_notify'):
            self.copy_notify.move(W // 2 - 70, H - 60)

    def enterEvent(self, event):
        self.setWindowOpacity(1.0)

    def leaveEvent(self, event):
        if QApplication.activePopupWidget() is None:
            self.setWindowOpacity(0.5)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if event.position().y() <= 48:
                delta = event.globalPosition().toPoint() - self.oldPos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    # ── Logic methods ─────────────────────────────────────────────────────────
    def set_time(self):
        self.time.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))

    def copy_text(self, textbox):
        QApplication.clipboard().setText(textbox.toPlainText())
        self.copy_notify.show()
        self.copy_notify.raise_()
        self.fade_in = QPropertyAnimation(self.copy_notify_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()
        def fade_out():
            self.fade_out_anim = QPropertyAnimation(self.copy_notify_effect, b"opacity")
            self.fade_out_anim.setDuration(500)
            self.fade_out_anim.setStartValue(1)
            self.fade_out_anim.setEndValue(0)
            self.fade_out_anim.finished.connect(self.copy_notify.hide)
            self.fade_out_anim.start()
        self.copy_timer = QTimer()
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(fade_out)
        self.copy_timer.start(2000)

    def type_text(self, textbox, text, speed=8):
        textbox.clear()
        self._typing_text = text
        self._typing_index = 0
        def type_step():
            if self._typing_index < len(self._typing_text):
                textbox.insertPlainText(self._typing_text[self._typing_index])
                self._typing_index += 1
            else:
                self.typing_timer.stop()
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(type_step)
        self.typing_timer.start(speed)

    def calculate_release_time(self):
        try:
            minutes = int(self.off_time.text())
            release = datetime.now() + timedelta(minutes=minutes)
            self.off_release.setText(release.strftime("%H:%M"))
        except Exception:
            pass

    def insert_article(self, article):
        self.off_article.setText(article)

    def _build_circumstance_narrative(self):
        """Build a fluent narrative from checked circumstance boxes."""
        cs      = self.callsign.text()
        suspect = self.suspect.text()
        place   = self.delivered_where.currentText()
        call    = self.call_type.currentText()

        found     = self.cb_found.isChecked()
        escaped   = self.cb_escape.isChecked()
        chase     = self.cb_chase.isChecked()
        foot      = self.cb_foot.isChecked()
        caught    = self.cb_caught.isChecked()
        delivered = self.cb_delivered.isChecked()

        # Build sentence progressively
        sentence = f"{cs} отреагировал на вызов ({call})."
        detail = ""

        if found:
            detail = "По прибытию был обнаружен подозреваемый"
            if escaped:
                detail += ", который попытался скрыться"
                if chase:
                    detail += ", вследствие чего началась погоня"
                    if foot:
                        detail += " (пешком)"
                    if caught:
                        detail += f" и после успешного преследования подозреваемого, он был задержан"
                        if suspect:
                            detail += f" и идентифицирован как \"{suspect}\""
                else:
                    if caught:
                        detail += " и был задержан"
                        if suspect:
                            detail += f", идентифицирован как \"{suspect}\""
            else:
                if caught:
                    detail += " и задержан"
                    if suspect:
                        detail += f", идентифицирован как \"{suspect}\""
            detail += "."
            if delivered:
                detail += f" После всего был доставлен в {place}."
        elif caught:
            detail = f"Подозреваемый был задержан"
            if suspect:
                detail += f" и идентифицирован как \"{suspect}\""
            detail += "."
            if delivered:
                detail += f" Доставлен в {place}."
        elif delivered:
            detail = f"Доставлен в {place}."

        if detail:
            return sentence + "\n" + detail
        return sentence

    def generate_report(self):
        suspect = self.suspect.text()
        call    = self.call_type.currentText()
        cs      = self.callsign.text()
        place   = self.delivered_where.currentText()
        story_parts = []

        # ── Special call types ────────────────────────────────────────────────
        if call == "Вызов: продажа оружия":
            if self.cb_escape.isChecked():
                block = (
                    "Поступил вызов о продаже оружия.\n"
                    "По прибытию на сцену был замечен гражданский который передавал человеку некий предмет похожий на оружие, "
                    "из-за чего была предпринята попытка задержания по подозрению в незаконном обороте огнестрельного оружия.\n"
                    "Подозреваемый попытался скрыться от сотрудников правопорядка, и после длительного/недлительного преследования был задержан.\n"
                    f"Им оказался {suspect}.\n"
                    "Указанный гражданин был задержан с поличным при передаче огнестрельного оружия покупателю."
                )
            else:
                block = (
                    "Поступил вызов о продаже оружия.\n"
                    "По прибытию на сцену был замечен гражданский, который передавал человеку некий предмет похожий на оружия.\n"
                    f"Им оказался {suspect}.\n"
                    "Указанный гражданин был задержан с поличным при передаче огнестрельного оружия покупателю."
                )
            if self.cb_delivered.isChecked():
                block += f"\nДоставлен в {place}."
            story_parts.append(block)

        elif call == "Вызов: продажа наркотиков":
            if self.cb_escape.isChecked():
                block = (
                    "Поступил вызов о продаже наркотиков.\n"
                    "По прибытию на сцену был замечен гражданин передающий человеку некий пакетик, "
                    "из-за чего была предпринята попытка задержания по подозрению в незаконном обороте наркотических веществ. "
                    f"Подозреваемый попытался скрыться от сотрудников LSSD, в связи с чем к подозреваемому были применены спецсредства. "
                    f"Им оказался {suspect}. "
                    "Указанный гражданин был задержан с поличным при передаче наркотических веществ покупателю."
                )
            else:
                block = (
                    "Поступил вызов о продаже наркотиков.\n"
                    "По прибытию на сцену был замечен гражданин передающий человеку некий пакетик "
                    "из-за чего был задержан по подозрению в незаконном обороте наркотических веществ. "
                    f"Им оказался {suspect}. "
                    "Указанный гражданин был задержан с поличным при передаче наркотиков покупателю."
                )
            if self.cb_delivered.isChecked():
                block += f"\nДоставлен в {place}."
            story_parts.append(block)

        elif call == "10-55":
            block = f"{cs} - Производил 10-55, в ходе которого подозреваемый начал скрываться"
            if self.cb_delivered.isChecked():
                block += f", в следствии был задержан и доставлен в {place}"
            block += "."
            story_parts.append(block)

        elif call == "10-66":
            block = f"{cs} - Производил 10-66, в ходе которого подозреваемый начал скрываться"
            if self.cb_delivered.isChecked():
                block += f", в следствии был задержан и доставлен в {place}"
            block += "."
            story_parts.append(block)

        elif call == "Терри стоп":
            block = f"{cs} - Производил Терри стоп в ходе которого у подозреваемого были найдены запрещенные законом содержимое."
            if self.cb_delivered.isChecked():
                block += f" Подозреваемый был задержан и доставлен в {place}."
            story_parts.append(block)

        elif call == "10-55 с переходом на 10-66":
            block = (
                f"{cs} - Производил 10-55, после ознакомления с данными подозреваемого, "
                f"{cs} запросил 10-70 и начал производить 10-66."
            )
            if self.cb_delivered.isChecked():
                block += f" Подозреваемый был задержан и доставлен в {place}."
            story_parts.append(block)

        elif call == "10-66 с арестом":
            block = f"{cs} - Произвел 10-66, в ходе которого подозреваемый не оказывал сопротивление и сдался"
            if self.cb_delivered.isChecked():
                block += f", в следствии был задержан и доставлен в {place}"
            block += "."
            story_parts.append(block)

        else:
            story_parts.append(self._build_circumstance_narrative())

        # ── Досмотр ───────────────────────────────────────────────────────────
        if self.cb_weapon_search.isChecked():
            items = self.weapon_items.toPlainText().strip()
            if items:
                story_parts.append(f"При обыске было найдено:\n{items}")

        story_text = "\n".join(story_parts)
        details    = self.details.toPlainText().strip()
        victim     = self.victim.text().strip()

        header_lines = [
            f"#Рапорт по инциденту: {self.incident.text()}",
            f"- Подозреваемый: {suspect}",
        ]
        if victim:
            header_lines.append(f"- Пострадавший: {victim}")
        header_lines += [
            f"- Время: {self.time.text()}",
            f"- Сцена: {self.scene.text()}",
        ]
        header = "\n".join(header_lines)

        text = f"```cs\n{header}\n{story_text}"
        if details:
            text += f"\n{details}"
        text += "\n```"
        self.type_text(self.result, text)

    def generate_impound(self):
        text = f"""```cs
#Эвакуированный транспорт
{self.imp_date.text()} / {self.imp_plate.text()} / {self.imp_reg.text()} / {self.imp_model.text()} / {self.imp_color.text()} / {self.imp_reason.text()} / {self.imp_where.text()} / {self.imp_officer.text()}
```"""
        self.type_text(self.imp_result, text)

    def generate_offense(self):
        fine = self.off_fine.text()
        if fine and not fine.endswith("$"): fine += "$"
        article = f"Ст. {self.off_article.text()}"
        time_value = self.off_time.text()
        if time_value: time_value = f"{time_value} Сроков"
        block = f"""#Уголовное взыскание
{self.off_number.text()} / {self.off_date.text()} / {self.off_reg.text()} / {self.off_name.text()} / {article} / {time_value} / {fine} / {self.off_release.text()} / {self.off_items.text()} / {self.off_dept.currentText()} / {self.off_callsign.text()}

"""
        if self.offense_open_block:
            current = self.off_result.toPlainText()
            self.off_result.setText(current + block + "```")
            self.offense_open_block = False
        else:
            self.type_text(self.off_result, f"```cs\n{block}```")

    def offense_x2(self):
        fine = self.off_fine.text()
        if fine and not fine.endswith("$"): fine += "$"
        article = f"Ст. {self.off_article.text()}"
        time_value = self.off_time.text()
        if time_value: time_value = f"{time_value} Сроков"
        block = f"""#Уголовное взыскание
{self.off_number.text()} / {self.off_date.text()} / {self.off_reg.text()} / {self.off_name.text()} / {article} / {time_value} / {fine} / {self.off_release.text()} / {self.off_items.text()} / {self.off_dept.currentText()} / {self.off_callsign.text()}

"""
        current = self.off_result.toPlainText()
        if current.endswith("```"): current = current[:-3]
        if not current.startswith("```cs"): current = "```cs\n"
        self.off_result.setText(current + block + "```")
        for f in [self.off_reg, self.off_name]:
            f.clear()

    def generate_claim(self):
        text = f"""```cs
#{self.claim_number.text()} Заявление:
- Заявитель-Пострадавший: "{self.claim_victim.text()}"
- Подозреваемый: "{self.claim_suspect.text()}"
- Время и дата происшествия: {self.claim_datetime.text()}
- Дополнительная информация: {self.claim_details.toPlainText()}
```"""
        self.type_text(self.claim_result, text)

    def generate_evidence(self):
        action = self.evidence_action.currentText()
        text = f"""```cs
EVIDENCE ROOM | {self.evidence_callsign.text()} | {self.evidence_name.text()}
#{action}:

{self.evidence_items.toPlainText()}
```"""
        self.type_text(self.evidence_result, text)

    def generate_restraining(self):
        status = self.res_status.currentText()
        notified = "#УВЕДОМЛЕН" if self.res_notified.isChecked() else "#НЕ УВЕДОМЛЕН"
        text = f"""```cs
#{self.res_date.text()} - {self.res_number.text()} - {self.res_name.text()} / {self.res_reg.text()} - {self.res_type.currentText()}
- Субъект приказа: "{self.res_reg.text()} {self.res_name.text()}"
- Вид приказа: "{self.res_type.currentText()}"
- Приказ: {self.res_text.toPlainText()}
- Срок действия: "до {self.res_until.text()}"
- {notified}
- Статус: "{status}".
- Примечание: {self.res_note.toPlainText()}
```"""
        self.type_text(self.res_result, text)

    def generate_wanted(self):
        text = f"""```cs
#WANTED-SUSPECT #{self.wanted_number.text()}
1. ИМЯ И ФАМИЛИЯ: {self.wanted_name.text()}
2. РЕГНОМЕР: {self.wanted_plate.text()}
3. ПРИЧИНА РОЗЫСКА: {self.wanted_reason.text()}
4. ПРИКРЕПЛЕННЫЙ ИНЦИДЕНТ-РЕПОРТ: {self.wanted_incident.text()}
Доп. инфо: {self.wanted_info.toPlainText()}
```"""
        self.type_text(self.wanted_result, text)

    def generate_bolo(self):
        text = f"""```cs
#WANTED-CAR #{self.bolo_number.text()}
1. МАРКА ТС: {self.bolo_model.text()}
2. РЕГНОМЕР: {self.bolo_plate.text()}
3. ВЛАДЕЛЕЦ: {self.bolo_owner.text()}
4. ПРИЧИНА РОЗЫСКА: {self.bolo_reason.text()}
5. ПРИКРЕПЛЕННЫЙ ИНЦИДЕНТ-РЕПОРТ: {self.bolo_incident.text()}
6. ДОП ИНФОРМАЦИЯ: {self.bolo_info.toPlainText()}
```"""
        self.type_text(self.bolo_result, text)

    def populate_laws_list(self):
        self.laws_list.clear()
        for category in self.laws_data:
            cat_item = QListWidgetItem(f"── {category} ──")
            cat_item.setForeground(QColor(C['accent_glow']))
            cat_item.setFlags(Qt.ItemFlag.NoItemFlags)
            font = cat_item.font()
            font.setBold(True)
            font.setPointSize(9)
            cat_item.setFont(font)
            self.laws_list.addItem(cat_item)
            for article in self.laws_data[category]:
                item = QListWidgetItem("  " + article)
                self.laws_list.addItem(item)

    def show_law_text(self, item):
        name = item.text().strip()
        for category in self.laws_data:
            if name in self.laws_data[category]:
                article_data = self.laws_data[category][name]
                # Extract numeric article number for the offense field link
                m = re.search(r'(\d+(?:\.\d+)?)', name)
                art_num = m.group(1) if m else name
                html = f"""<div style='font-family: Segoe UI; color: #e2e8f0; padding: 10px;'>
<h2 style='color: #3b82f6; margin-bottom: 8px;'>{name}</h2>
<p style='color: #94a3b8; line-height: 1.7; margin-bottom: 16px;'>{article_data.get('text','').replace(chr(10), '<br>')}</p>"""
                if "paragraphs" in article_data and article_data["paragraphs"]:
                    html += "<hr style='border: 1px solid #1e293b; margin: 12px 0;'>"
                    for para, pdata in article_data["paragraphs"].items():
                        para_num = para.lstrip('§')
                        full_art = f"{art_num}.{para_num}"
                        self._laws_punishment_map[full_art] = pdata.get('punishment', '')
                        html += f"""<a href='{full_art}' style='text-decoration: none; display: block; cursor: pointer;'><div style='margin-bottom: 12px; padding: 10px; background: #131922; border-radius: 6px; border-left: 3px solid #2563eb;'>
<span style='color: #60a5fa; font-weight: bold;'>{para}</span>
<span style='color: #cbd5e1; margin-left: 8px;'>{pdata.get('title','')}</span><br>
<span style='color: #f59e0b; font-size: 12px;'>⚖ {pdata.get('punishment','')}</span>
</div></a>"""
                html += "</div>"
                self.laws_text.setHtml(html)
                break

    def _law_paragraph_clicked(self, url):
        art_ref = url.toString()
        punishment = self._laws_punishment_map.get(art_ref, '')
        existing = [a['article'] for a in self._selected_articles]
        if art_ref not in existing:
            self._selected_articles.append({'article': art_ref, 'punishment': punishment})
        self.laws_selected_lbl.setText(", ".join(a['article'] for a in self._selected_articles))

    def _transfer_articles_to_offense(self):
        if self._selected_articles:
            articles_str = ", ".join(a['article'] for a in self._selected_articles)
            self.off_article.setText(articles_str)

            max_terms = 0
            total_fine = 0
            for item in self._selected_articles:
                punishment = item.get('punishment', '')
                terms_match = re.search(r'(\d+)\s*сроков', punishment)
                if terms_match:
                    t = int(terms_match.group(1))
                    if t > max_terms:
                        max_terms = t
                fine_match = re.search(r'(\d+)\s*\$', punishment)
                if fine_match:
                    try:
                        total_fine += int(fine_match.group(1))
                    except ValueError:
                        pass

            if max_terms > 0:
                self.off_time.setText(str(max_terms))
            if total_fine > 0:
                self.off_fine.setText(str(total_fine))

        self._nav_click(self.nav_buttons[2], self.page_offense)

    def _clear_selected_articles(self):
        self._selected_articles.clear()
        self.laws_selected_lbl.setText("—")

    def search_laws(self):
        query = self.laws_search.text().lower()
        self.laws_list.clear()
        for category in self.laws_data:
            matched = []
            for article in self.laws_data[category]:
                article_data = self.laws_data[category][article]
                found = query in article.lower()
                if not found: found = query in article_data.get("text", "").lower()
                if not found and "paragraphs" in article_data:
                    for para, pdata in article_data["paragraphs"].items():
                        if (query in para.lower() or query in pdata.get("title","").lower()
                                or query in pdata.get("punishment","").lower()):
                            found = True
                            break
                if found:
                    matched.append(article)
            if matched:
                cat_item = QListWidgetItem(f"── {category} ──")
                cat_item.setForeground(QColor(C['accent_glow']))
                cat_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.laws_list.addItem(cat_item)
                for a in matched:
                    self.laws_list.addItem(QListWidgetItem("  " + a))

    # ── ИСПРАВЛЕННЫЕ методы сохранения и смены офицера ────────────────────────

    def _save_settings_data(self):
        """Единый метод сохранения — читает файл, обновляет нужные ключи, записывает."""
        path = os.path.join(self.base_path, "settings.json")
        # Читаем существующий файл чтобы не затереть лишние ключи
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        # Обновляем все актуальные поля
        data["hotkey"]   = getattr(self, "hotkey",           "F10")
        data["theme"]    = getattr(self, "theme",            "blue")
        data["nickname"] = getattr(self, "officer_nickname", "")
        data["callsign"] = getattr(self, "officer_callsign", "")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка сохранения",
                                f"Не удалось сохранить настройки:\n{e}")

    def _change_officer(self):
        login = LoginDialog()
        screen = QApplication.primaryScreen().geometry()
        login.move(screen.center().x() - 230, screen.center().y() - 160)
        if hasattr(self, 'officer_nickname'):
            login.nick_input.setText(self.officer_nickname)
        if hasattr(self, 'officer_callsign'):
            login.cs_input.setText(self.officer_callsign)

        login.exec()

        if login._confirmed:
            nick, cs = login.get_data()
            self.officer_nickname = nick
            self.officer_callsign = cs
            CallsignLineEdit._current_callsign = cs
            if hasattr(self, 'officer_lbl'):
                self.officer_lbl.setText(f"🛡  {nick}  ·  {cs}")
            self._save_settings_data()

    def _rebuild_ui(self):
        """Destroy all child widgets and rebuild UI with the current C palette.
        Must be called via QTimer.singleShot so it runs outside any signal handler."""
        # Stop any running QTimers attached to this window (clock etc.)
        for obj in list(self.children()):
            if isinstance(obj, QTimer):
                obj.stop()
        # Detach all child QWidgets — they become parentless and get GC'd
        for obj in list(self.children()):
            if isinstance(obj, QWidget):
                obj.hide()
                obj.setParent(None)
        # Reset UI state that _build_ui re-initialises
        self._nav_buttons = []
        self._active_nav = None
        # Rebuild with updated C palette
        self.setStyleSheet(build_style_main(C))
        self._build_ui()
        # Qt does NOT auto-show new children added to an already-visible parent —
        # we must call show() explicitly on each top-level child widget.
        for child in list(self.children()):
            if isinstance(child, QWidget) and child is not self.copy_notify:
                child.show()
        # Restore officer label text that _build_ui leaves blank
        if hasattr(self, 'officer_lbl'):
            nick = getattr(self, 'officer_nickname', '')
            cs   = getattr(self, 'officer_callsign', '')
            if nick or cs:
                self.officer_lbl.setText(f"🛡  {nick}  ·  {cs}")
        # Force repaint
        self.update()
        self.repaint()

    def save_settings(self):
        # Снимаем старую горячую клавишу
        if KEYBOARD_AVAILABLE and self.hotkey_id:
            try:
                keyboard.remove_hotkey(self.hotkey_id)
            except Exception:
                pass
        # Обновляем значения из UI до того, как виджеты могут быть пересозданы
        self.hotkey   = self.hotkey_input.text()
        new_theme     = self.theme_box.currentText()
        theme_changed = new_theme != self.theme
        if theme_changed:
            self.theme = new_theme
            C.update(THEMES.get(new_theme, THEMES["blue"]))
        # Регистрируем новую горячую клавишу
        if KEYBOARD_AVAILABLE:
            try:
                self.hotkey_id = keyboard.add_hotkey(
                    self.hotkey, lambda: QTimer.singleShot(0, self.toggle_window))
            except Exception:
                pass
        # Сохраняем через единый метод
        self._save_settings_data()
        # Перестраиваем UI отложенно — ПОСЛЕ того, как сигнал кнопки завершится,
        # иначе уничтожение виджетов внутри обработчика сигнала вызывает чёрный экран
        if theme_changed:
            QTimer.singleShot(0, self._rebuild_ui)

    # ── Остальные методы ──────────────────────────────────────────────────────

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def exit_app(self):
        QApplication.quit()
        os._exit(0)

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def load_settings(self):
        try:
            path = os.path.join(self.base_path, "settings.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        self.hotkey           = data.get("hotkey",    "F10")
        self.theme            = data.get("theme",     "blue")
        self.officer_nickname = data.get("nickname",  "")
        self.officer_callsign = data.get("callsign",  "")
        # Применяем сохранённую тему сразу
        palette = THEMES.get(self.theme, THEMES["blue"])
        C.update(palette)
        if KEYBOARD_AVAILABLE:
            try:
                self.hotkey_id = keyboard.add_hotkey(
                    self.hotkey, lambda: QTimer.singleShot(0, self.toggle_window))
            except Exception:
                pass

    def check_updates(self):
        try:
            response = urllib.request.urlopen(VERSION_URL)
            latest = response.read().decode("utf-8").strip()
            if latest != CURRENT_VERSION:
                msg = QMessageBox()
                msg.setWindowTitle("Обновление MDT")
                msg.setText(f"Доступна новая версия: {latest}")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    webbrowser.open(DOWNLOAD_URL)
        except Exception:
            pass

    def load_laws(self):
        try:
            path = os.path.join(self.base_path, "laws.json")
            with open(path, "r", encoding="utf-8") as f:
                self.laws_data = json.load(f)
        except Exception:
            self.laws_data = {}


# ── Exception logger ──────────────────────────────────────────────────────────
def log_exception(exc_type, exc_value, exc_traceback):
    with open(os.path.join(get_base_path(), "error_log.txt"), "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

sys.excepthook = log_exception

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    base = get_base_path()
    saved_cs   = ""
    saved_nick = ""
    try:
        with open(os.path.join(base, "settings.json"), "r", encoding="utf-8") as f:
            _d = json.load(f)
            saved_cs   = _d.get("callsign", "")
            saved_nick = _d.get("nickname", "")
    except Exception:
        pass

    if not saved_cs or not saved_nick:
        login = LoginDialog()
        screen = app.primaryScreen().geometry()
        login.move(screen.center().x() - 230, screen.center().y() - 160)
        login.exec()
        if not login._confirmed:
            sys.exit(0)
        saved_nick, saved_cs = login.get_data()

    CallsignLineEdit._current_callsign = saved_cs

    window = MDT()
    window.officer_callsign = saved_cs
    window.officer_nickname = saved_nick
    if hasattr(window, 'officer_lbl'):
        window.officer_lbl.setText(f"🛡  {saved_nick}  ·  {saved_cs}")
    # Сохраняем данные офицера при первом запуске (когда settings.json ещё не было)
    window._save_settings_data()

    window.show()
    sys.exit(app.exec())
