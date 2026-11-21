"""
QR Studio  -  Modern QR Code Generator (PySide6)

Install:
    pip install PySide6 qrcode

Run:
    python qr_generator_v2.py

Features
    * Content types: Text/URL, Wi-Fi, Email, Phone
    * Size, quiet zone, module shape (square / rounded / dots / diamond),
      roundness, module spacing, corner radius, error correction
    * Solid or gradient foreground, custom eye color, transparent background, presets
    * Caption text above or below the QR (font, size, bold/italic, align, color, spacing)
    * Center logo (auto-uses high error correction)
    * Save PNG / JPG / SVG, copy to clipboard
    * Themes: Light, Midnight, Jellyfish (animated)
"""

import math
import os
import random
import sys
import tempfile
from dataclasses import dataclass, field, replace
from urllib.parse import quote

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
)
from PySide6.QtCore import QPointF, QRect, QRectF, QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QIcon,
    QFont,
    QFontMetricsF,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# =========================================================================== #
#  THEMES
# =========================================================================== #
THEMES = {
    "Light": dict(
        bg1="#f6f7ff", bg2="#e7ecff",
        card="rgba(255,255,255,0.80)", card_border="rgba(110,120,200,0.25)",
        text="#1d2140", muted="#6a7090",
        a1="#5b6bff", a2="#a15bff", on_accent="#ffffff",
        input="rgba(255,255,255,0.95)", popup="#ffffff", status_bg="#eef1ff",
        tab_hover="rgba(91,107,255,0.12)",
        glass=(255, 255, 255, 175), checker_a="#ffffff", checker_b="#e3e7f6",
        orbs=[(0.08, 0.10, 0.40, (120, 140, 255, 70)), (0.95, 0.92, 0.45, (190, 120, 255, 60))],
        anim=False,
    ),
    "Midnight": dict(
        bg1="#0b0a15", bg2="#181330",
        card="rgba(32,27,58,0.75)", card_border="rgba(150,130,255,0.25)",
        text="#eeebff", muted="#9d99c2",
        a1="#8f7bff", a2="#ff6fc8", on_accent="#12081f",
        input="rgba(13,11,28,0.75)", popup="#1d1838", status_bg="#110e22",
        tab_hover="rgba(143,123,255,0.20)",
        glass=(18, 15, 38, 200), checker_a="#2b2650", checker_b="#1c1836",
        orbs=[(0.10, 0.15, 0.42, (120, 90, 255, 70)), (0.92, 0.85, 0.46, (255, 90, 190, 55))],
        anim=False,
    ),
    "Jellyfish": dict(
        bg1="#020c24", bg2="#13063c",
        card="rgba(8,36,82,0.58)", card_border="rgba(80,240,230,0.30)",
        text="#e3fbff", muted="#8fc9de",
        a1="#35f0e4", a2="#ff6bd6", on_accent="#02121f",
        input="rgba(2,18,52,0.68)", popup="#06214d", status_bg="#071b40",
        tab_hover="rgba(53,240,228,0.16)",
        glass=(4, 22, 62, 150), checker_a="#0f2d5f", checker_b="#08214b",
        orbs=[(0.18, 0.85, 0.50, (30, 110, 255, 55)), (0.88, 0.18, 0.42, (190, 70, 255, 55))],
        anim=True,
    ),
}

QSS_TEMPLATE = """
QWidget { color:@text; font-family:'Segoe UI','Inter','SF Pro Text','Helvetica Neue',Arial; font-size:13px; }
QMainWindow { background:@bg2; }
QLabel { background:transparent; }
QLabel#title { font-size:24px; font-weight:800; }
QLabel#subtitle, QLabel#muted { color:@muted; }
QLabel#value { color:@a1; font-weight:700; }
QLabel#section { font-size:11px; font-weight:800; color:@a1; letter-spacing:1.5px; }

QFrame#card { background:@card; border:1px solid @card_border; border-radius:16px; }

QTabWidget::pane { border:none; background:transparent; top:8px; }
QTabBar { background:transparent; }
QTabBar::tab { background:transparent; color:@muted; padding:8px 11px; margin-right:3px;
               border-radius:11px; font-weight:700; }
QTabBar::tab:hover:!selected { background:@tab_hover; color:@text; }
QTabBar::tab:selected { color:@on_accent;
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @a1,stop:1 @a2); }

QPlainTextEdit, QLineEdit, QComboBox, QFontComboBox {
    background:@input; border:1px solid @card_border; border-radius:10px; padding:7px 10px;
    selection-background-color:@a1; selection-color:@on_accent; }
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus, QFontComboBox:focus { border:1px solid @a1; }
QComboBox::drop-down, QFontComboBox::drop-down { border:none; width:26px; }
QComboBox::down-arrow, QFontComboBox::down-arrow { image:url(@arrow); width:12px; height:12px; margin-right:8px; }
QComboBox QAbstractItemView, QFontComboBox QAbstractItemView {
    background:@popup; border:1px solid @card_border; padding:4px; outline:none;
    selection-background-color:@a1; selection-color:@on_accent; }

QPushButton { background:@input; border:1px solid @card_border; border-radius:10px;
              padding:9px 14px; font-weight:600; }
QPushButton:hover { border:1px solid @a1; }
QPushButton#primary { color:@on_accent; border:none; font-weight:800;
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @a1,stop:1 @a2); }
QPushButton#primary:hover { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @a2,stop:1 @a1); }

QSlider::groove:horizontal { height:6px; background:@card_border; border-radius:3px; }
QSlider::sub-page:horizontal { border-radius:3px;
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @a1,stop:1 @a2); }
QSlider::handle:horizontal { image:url(@handle); background:transparent; border:none;
    width:24px; height:24px; margin:-9px 0; }

QCheckBox { spacing:8px; background:transparent; }
QCheckBox::indicator { width:18px; height:18px; border-radius:6px;
    border:1px solid @card_border; background:@input; }
QCheckBox::indicator:checked {
    border:1px solid @a1;
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @a1,stop:1 @a2); }

QStatusBar { background:@status_bg; border-top:1px solid @card_border; color:@muted; }
QStatusBar QLabel { color:@muted; padding:0 8px; }
QStatusBar::item { border:none; }

QScrollArea { border:none; background:transparent; }
QWidget#pageViewport, QWidget#pageInner, QStackedWidget { background:transparent; }
QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:@card_border; border-radius:4px; min-height:30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QToolTip { background:@popup; color:@text; border:1px solid @a1; padding:4px; }
"""


def make_arrow_icon(color: str) -> str:
    """Draw a small chevron PNG for combo boxes and return its path (forward slashes for QSS)."""
    path = os.path.join(tempfile.gettempdir(), f"qrstudio_arrow_{color.lstrip('#')}.png")
    pm = QPixmap(24, 24)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 3)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.drawPolyline(QPolygonF([QPointF(6, 9), QPointF(12, 15), QPointF(18, 9)]))
    p.end()
    pm.save(path)
    return path.replace("\\", "/")


def make_handle_icon(theme: dict) -> str:
    """Slider handle: glowing gradient ring with a solid center. Writes name.png and name@2x.png."""
    tag = (theme["a1"] + theme["a2"] + theme["popup"]).replace("#", "")
    base = os.path.join(tempfile.gettempdir(), f"qrstudio_handle_{tag}")
    for scale, suffix in ((1, ""), (2, "@2x")):
        px = 24 * scale
        pm = QPixmap(px, px)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        c = px / 2
        p.setPen(Qt.NoPen)

        glow = QRadialGradient(QPointF(c, c), c)          # soft halo
        a = QColor(theme["a1"])
        a.setAlpha(110)
        glow.setColorAt(0.55, a)
        a.setAlpha(0)
        glow.setColorAt(1.0, a)
        p.setBrush(glow)
        p.drawEllipse(QPointF(c, c), c, c)

        ring = QLinearGradient(0, 0, px, px)              # gradient ring
        ring.setColorAt(0, QColor(theme["a1"]))
        ring.setColorAt(1, QColor(theme["a2"]))
        p.setBrush(ring)
        p.drawEllipse(QPointF(c, c), 9 * scale, 9 * scale)

        p.setBrush(QColor(theme["popup"]))                # center
        p.drawEllipse(QPointF(c, c), 5 * scale, 5 * scale)
        p.end()
        pm.save(f"{base}{suffix}.png")
    return (base + ".png").replace("\\", "/")


def build_qss(theme: dict) -> str:
    qss = QSS_TEMPLATE.replace("@arrow", make_arrow_icon(theme["muted"]))
    qss = qss.replace("@handle", make_handle_icon(theme))
    # longest keys first so "@card" never clobbers "@card_border"
    for key in sorted((k for k, v in theme.items() if isinstance(v, str)), key=len, reverse=True):
        qss = qss.replace("@" + key, theme[key])
    return qss


# =========================================================================== #
#  QR OPTIONS + RENDERING
# =========================================================================== #
@dataclass
class QROpts:
    size: int = 512
    border: int = 4
    style: str = "Square"
    roundness: int = 30          # % of module (rounded style)
    module_scale: int = 100      # % of module actually filled
    corner: int = 0              # outer corner radius, % of size

    fg: QColor = field(default_factory=lambda: QColor("#111827"))
    fg2: QColor = field(default_factory=lambda: QColor("#6d28d9"))
    gradient: bool = False
    grad_dir: str = "Diagonal"
    eye_custom: bool = False
    eye: QColor = field(default_factory=lambda: QColor("#111827"))
    bg: QColor = field(default_factory=lambda: QColor("#FFFFFF"))
    transparent: bool = False

    caption: str = ""
    cap_pos: str = "Below"       # None / Below / Above
    font_family: str = "Arial"
    font_pct: int = 7            # % of QR size
    bold: bool = True
    italic: bool = False
    align: str = "Center"
    cap_color: QColor = field(default_factory=lambda: QColor("#111827"))
    cap_gap: int = 4             # caption <-> image edge, % of size
    cap_dist: int = 4            # QR modules <-> caption, % of size

    logo: QImage | None = None
    logo_pct: int = 20
    logo_pad: int = 12
    logo_round: bool = True


def make_matrix(text: str, ec_level: int):
    qr = qrcode.QRCode(error_correction=ec_level, box_size=1, border=0)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.get_matrix(), qr.version


def is_eye(r: int, c: int, n: int) -> bool:
    return (r < 7 and c < 7) or (r < 7 and c >= n - 7) or (r >= n - 7 and c < 7)


def compute_layout(o: QROpts, n: int):
    """Canvas layout. The caption gap is measured from the visible QR modules (not from the
    white quiet-zone edge), and the padding on the far side of the caption mirrors it, so the
    caption sits evenly between the code and the edge of the image."""
    size = o.size
    q = o.border * size / (n + 2 * o.border)          # quiet-zone width in px
    text = o.caption.strip() if o.cap_pos != "None" else ""
    if not text:
        return size, size, QRectF(0, 0, size, size), QRectF(), None, ""

    fpx = max(6.0, size * o.font_pct / 100)
    font = QFont(o.font_family)
    font.setPixelSize(max(6, int(fpx)))
    font.setBold(o.bold)
    font.setItalic(o.italic)
    align = {"Left": Qt.AlignLeft, "Center": Qt.AlignHCenter, "Right": Qt.AlignRight}[o.align]
    flags = align.value | Qt.TextWordWrap.value
    pad_h = size * 0.05
    gap = size * o.cap_dist / 100                      # code  <->  caption
    pad = size * o.cap_gap / 100                       # caption  <->  image edge
    th = QFontMetricsF(font).boundingRect(QRectF(0, 0, size - 2 * pad_h, 100000), flags, text).height()

    H = size - q + gap + th + pad
    if o.cap_pos == "Above":
        text_rect = QRectF(0, pad, size, th)
        qr_rect = QRectF(0, pad + th + gap - q, size, size)
    else:
        qr_rect = QRectF(0, 0, size, size)
        text_rect = QRectF(0, size - q + gap, size, th)
    return size, H, qr_rect, text_rect, (font, flags, pad_h), text


def draw_all(p: QPainter, matrix, o: QROpts):
    W, H, qr_rect, text_rect, info, text = compute_layout(o, len(matrix))
    p.setRenderHint(QPainter.TextAntialiasing, True)

    # ---- background
    if not o.transparent:
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(o.bg)
        r = o.size * o.corner / 100
        if r > 0:
            p.drawRoundedRect(QRectF(0, 0, W, H), r, r)
        else:
            p.drawRect(QRectF(0, 0, W, H))

    # ---- brushes
    if o.gradient:
        a, b = qr_rect.topLeft(), qr_rect.bottomRight()
        if o.grad_dir == "Horizontal":
            a, b = qr_rect.topLeft(), qr_rect.topRight()
        elif o.grad_dir == "Vertical":
            a, b = qr_rect.topLeft(), qr_rect.bottomLeft()
        g = QLinearGradient(a, b)
        g.setColorAt(0, o.fg)
        g.setColorAt(1, o.fg2)
        main = g
    else:
        main = o.fg
    eye_brush = o.eye if o.eye_custom else main

    # ---- logo area (modules underneath are skipped)
    logo_rect, keep = None, None
    if o.logo is not None and not o.logo.isNull():
        side = o.size * o.logo_pct / 100
        pad = side * o.logo_pad / 100
        c = qr_rect.center()
        logo_rect = QRectF(c.x() - side / 2, c.y() - side / 2, side, side)
        keep = logo_rect.adjusted(-pad, -pad, pad, pad)

    # ---- modules
    n = len(matrix)
    border = o.border
    m = o.size / (n + 2 * border)
    scale = o.module_scale / 100
    inset = m * (1 - scale) / 2
    p.setRenderHint(QPainter.Antialiasing, o.style != "Square" or scale < 1)
    p.setPen(Qt.NoPen)

    last_eye = None
    for r, row in enumerate(matrix):
        for c, filled in enumerate(row):
            if not filled:
                continue
            x0 = qr_rect.x() + (c + border) * m
            y0 = qr_rect.y() + (r + border) * m
            if keep is not None and keep.intersects(QRectF(x0, y0, m, m)):
                continue
            eye = is_eye(r, c, n)
            if eye != last_eye:
                p.setBrush(eye_brush if eye else main)
                last_eye = eye

            if o.style == "Square":
                if scale >= 1:
                    xa, ya = round(x0), round(y0)
                    p.drawRect(QRectF(xa, ya, round(x0 + m) - xa, round(y0 + m) - ya))
                else:
                    p.drawRect(QRectF(x0 + inset, y0 + inset, m - 2 * inset, m - 2 * inset))
            elif o.style == "Rounded":
                rad = m * o.roundness / 100
                p.drawRoundedRect(QRectF(x0 + inset, y0 + inset, m - 2 * inset, m - 2 * inset), rad, rad)
            elif o.style == "Dots":
                d = inset + m * 0.06
                p.drawEllipse(QRectF(x0 + d, y0 + d, m - 2 * d, m - 2 * d))
            else:  # Diamond
                cx, cy, h = x0 + m / 2, y0 + m / 2, m / 2 * scale * 1.05
                p.drawPolygon(QPolygonF([QPointF(cx, cy - h), QPointF(cx + h, cy),
                                         QPointF(cx, cy + h), QPointF(cx - h, cy)]))

    # ---- logo
    if logo_rect is not None:
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        iw, ih = o.logo.width(), o.logo.height()
        k = min(logo_rect.width() / iw, logo_rect.height() / ih)
        w, h = iw * k, ih * k
        target = QRectF(logo_rect.center().x() - w / 2, logo_rect.center().y() - h / 2, w, h)
        p.save()
        if o.logo_round:
            path = QPainterPath()
            path.addRoundedRect(target, min(w, h) * 0.22, min(w, h) * 0.22)
            p.setClipPath(path)
        p.drawImage(target, o.logo)
        p.restore()

    # ---- caption
    if info is not None:
        font, flags, pad_h = info
        p.setFont(font)
        p.setPen(o.cap_color)
        p.setBrush(Qt.NoBrush)
        p.drawText(text_rect.adjusted(pad_h, 0, -pad_h, 0), flags | Qt.AlignVCenter.value, text)


def render_image(matrix, o: QROpts) -> QImage:
    W, H, *_ = compute_layout(o, len(matrix))
    img = QImage(int(W), int(math.ceil(H)), QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    draw_all(p, matrix, o)
    p.end()
    return img


def luminance(c: QColor) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def contrast_ratio(a: QColor, b: QColor) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# =========================================================================== #
#  CUSTOM WIDGETS
# =========================================================================== #
class Backdrop(QWidget):
    """Window background: gradient + glow orbs, plus animated jellyfish for that theme."""

    JELLY_COLORS = [QColor(53, 240, 228), QColor(255, 107, 214), QColor(150, 120, 255), QColor(90, 170, 255)]

    def __init__(self):
        super().__init__()
        self.theme = THEMES["Light"]
        self.t = 0.0
        rnd = random.Random(11)
        self.jellies = [(rnd.random(), rnd.random() * 1.4, rnd.uniform(0.7, 1.5),
                         rnd.uniform(0.010, 0.026), self.JELLY_COLORS[i % 4], rnd.random() * 6.28)
                        for i in range(5)]
        self.bubbles = [(rnd.random(), rnd.random(), rnd.uniform(2, 6), rnd.uniform(0.02, 0.06))
                        for _ in range(26)]
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)

    def set_theme(self, theme):
        self.theme = theme
        self.timer.start() if theme["anim"] else self.timer.stop()
        self.update()

    def _tick(self):
        self.t += 0.04
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        th = self.theme

        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor(th["bg1"]))
        g.setColorAt(1, QColor(th["bg2"]))
        p.fillRect(self.rect(), g)

        p.setPen(Qt.NoPen)
        for fx, fy, fr, (r, gg, b, a) in th["orbs"]:
            rad = fr * max(W, H)
            rg = QRadialGradient(fx * W, fy * H, rad)
            rg.setColorAt(0, QColor(r, gg, b, a))
            rg.setColorAt(1, QColor(r, gg, b, 0))
            p.setBrush(rg)
            p.drawEllipse(QPointF(fx * W, fy * H), rad, rad)

        if th["anim"]:
            self._draw_ocean(p, W, H)

    def _draw_ocean(self, p: QPainter, W, H):
        t = self.t
        # bubbles
        p.setBrush(Qt.NoBrush)
        for xf, yf, r, sp in self.bubbles:
            y = H * (1.05 - ((yf + t * sp) % 1.1))
            x = xf * W + math.sin(t * 0.8 + xf * 20) * 10
            p.setPen(QPen(QColor(170, 240, 255, 90), 1))
            p.drawEllipse(QPointF(x, y), r, r)
        # jellyfish
        for xf, yf, sc, sp, col, ph in self.jellies:
            x = xf * W + math.sin(t * 0.4 + ph) * 35
            y = H * (1.25 - ((yf + t * sp) % 1.45))
            self._jelly(p, x, y, sc, t + ph, col)

    @staticmethod
    def _jelly(p: QPainter, x, y, s, t, col: QColor):
        pulse = 1 + 0.07 * math.sin(t * 2.2)
        w = 58 * s * pulse
        h = 46 * s * (2 - pulse)

        # tentacles
        p.setBrush(Qt.NoBrush)
        for i in range(8):
            tx = x - w * 0.8 + i * (w * 1.6 / 7)
            length = 150 * s * (0.65 + 0.35 * (((i * 37) % 5) / 4))
            path = QPainterPath(QPointF(tx, y))
            steps = 14
            for k in range(1, steps + 1):
                f = k / steps
                px = tx + math.sin(t * 1.7 + i * 0.9 + f * 4) * 9 * s * f
                path.lineTo(px, y + length * f)
            pen = QPen(QColor(col.red(), col.green(), col.blue(), 105), max(1.0, 1.8 * s))
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawPath(path)

        # bell
        bell = QPainterPath()
        bell.moveTo(x - w, y)
        bell.cubicTo(x - w, y - h * 1.55, x + w, y - h * 1.55, x + w, y)
        bell.quadTo(x, y + h * 0.28, x - w, y)
        rg = QRadialGradient(QPointF(x, y - h * 0.55), w * 1.25)
        rg.setColorAt(0, QColor(col.red(), col.green(), col.blue(), 150))
        rg.setColorAt(1, QColor(col.red(), col.green(), col.blue(), 22))
        p.setBrush(rg)
        p.setPen(QPen(QColor(col.red(), col.green(), col.blue(), 120), 1.3))
        p.drawPath(bell)


class LogoBadge(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(46, 46)
        self.theme = THEMES["Light"]

    def set_theme(self, th):
        self.theme = th
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 46, 46)
        g.setColorAt(0, QColor(self.theme["a1"]))
        g.setColorAt(1, QColor(self.theme["a2"]))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(0, 0, 46, 46), 13, 13)
        p.setBrush(QColor(self.theme["on_accent"]))
        for (x, y) in [(9, 9), (27, 9), (9, 27)]:
            p.drawRoundedRect(QRectF(x, y, 10, 10), 3, 3)
        p.drawRoundedRect(QRectF(27, 27, 4.5, 4.5), 1.5, 1.5)
        p.drawRoundedRect(QRectF(33.5, 33.5, 4.5, 4.5), 1.5, 1.5)


class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.image: QImage | None = None
        self.theme = THEMES["Light"]
        self.setMinimumSize(340, 340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_theme(self, th):
        self.theme = th
        self.update()

    def set_image(self, img):
        self.image = img
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        th = self.theme

        p.setPen(QPen(QColor(th["a1"]).darker(100), 1))
        glass = QColor(*th["glass"])
        p.setBrush(glass)
        border = QColor(th["a1"])
        border.setAlpha(70)
        p.setPen(QPen(border, 1.2))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 20, 20)

        if self.image is None:
            p.setPen(QColor(th["muted"]))
            p.setFont(QFont(self.font().family(), 12))
            p.drawText(self.rect(), Qt.AlignCenter, "Enter some content to generate a QR code")
            return

        iw, ih = self.image.width(), self.image.height()
        avail_w, avail_h = self.width() - 70, self.height() - 70
        k = max(0.05, min(avail_w / iw, avail_h / ih))
        w, h = iw * k, ih * k
        target = QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

        # soft glow
        for i in range(7, 0, -1):
            gc = QColor(th["a1"])
            gc.setAlpha(9)
            p.setPen(Qt.NoPen)
            p.setBrush(gc)
            p.drawRoundedRect(target.adjusted(-i * 4, -i * 4, i * 4, i * 4), 16 + i * 2, 16 + i * 2)

        # checkerboard (shows through transparent areas)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(target, 4, 4)
        p.setClipPath(clip)
        tile = 12
        ca, cb = QColor(th["checker_a"]), QColor(th["checker_b"])
        y = target.top()
        row = 0
        while y < target.bottom():
            x, col = target.left(), row
            while x < target.right():
                p.fillRect(QRectF(x, y, tile, tile), ca if col % 2 == 0 else cb)
                x += tile
                col += 1
            y += tile
            row += 1
        p.restore()

        p.drawImage(target, self.image)


class ColorButton(QPushButton):
    def __init__(self, color: QColor, on_change):
        super().__init__()
        self._color = QColor(color)
        self._on_change = on_change
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.pick)
        self._refresh()

    @property
    def color(self) -> QColor:
        return QColor(self._color)

    def set_color(self, c):
        self._color = QColor(c)
        self._refresh()

    def _refresh(self):
        c = self._color
        txt = "#000000" if luminance(c) > 0.4 else "#ffffff"
        self.setText(c.name().upper())
        self.setStyleSheet(
            f"QPushButton {{ background:{c.name()}; color:{txt}; border:1px solid rgba(128,128,128,0.45);"
            f" border-radius:10px; padding:9px 12px; font-weight:800; }}"
            f"QPushButton:hover {{ border:2px solid rgba(128,128,128,0.9); }}")

    def pick(self):
        c = QColorDialog.getColor(self._color, self.window(), "Choose color")
        if c.isValid():
            self.set_color(c)
            self._on_change()


class LabeledSlider(QWidget):
    changed = Signal()

    def __init__(self, label, lo, hi, val, suffix=""):
        super().__init__()
        self.suffix = suffix
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        top = QHBoxLayout()
        name = QLabel(label)
        name.setObjectName("muted")
        self.val = QLabel()
        self.val.setObjectName("value")
        top.addWidget(name)
        top.addStretch()
        top.addWidget(self.val)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimumHeight(28)
        self.slider.setRange(lo, hi)
        self.slider.setValue(val)
        self.slider.valueChanged.connect(self._on)
        lay.addLayout(top)
        lay.addWidget(self.slider)
        self._on(val)

    def _on(self, v):
        self.val.setText(f"{v}{self.suffix}")
        self.changed.emit()

    def value(self):
        return self.slider.value()

    def setValue(self, v):
        self.slider.setValue(v)


def muted(text):
    l = QLabel(text)
    l.setObjectName("muted")
    return l


def make_card(title=None):
    frame = QFrame()
    frame.setObjectName("card")
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 16)
    lay.setSpacing(10)
    if title:
        lbl = QLabel(title.upper())
        lbl.setObjectName("section")
        lay.addWidget(lbl)
    return frame, lay


def make_page():
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.viewport().setObjectName("pageViewport")
    scroll.viewport().setAutoFillBackground(False)
    inner = QWidget()
    inner.setObjectName("pageInner")
    inner.setAutoFillBackground(False)
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(0, 0, 8, 0)
    lay.setSpacing(12)
    scroll.setWidget(inner)
    return scroll, lay


# =========================================================================== #
#  MAIN WINDOW
# =========================================================================== #
def wifi_escape(s: str) -> str:
    for ch in '\\;,":':
        s = s.replace(ch, "\\" + ch)
    return s


class MainWindow(QMainWindow):
    EC_LEVELS = {"Low (7%)": ERROR_CORRECT_L, "Medium (15%)": ERROR_CORRECT_M,
                 "Quartile (25%)": ERROR_CORRECT_Q, "High (30%)": ERROR_CORRECT_H}
    PRESETS = [("#111827", None, "#FFFFFF"), ("#5B6BFF", "#C04BFF", "#F3F1FF"),
               ("#0EA5A4", "#3B82F6", "#ECFEFF"), ("#F43F5E", "#F59E0B", "#FFF7ED"),
               ("#16A34A", "#065F46", "#F0FDF4"), ("#35F0E4", "#FF6BD6", "#0A1230"),
               ("#FFFFFF", None, "#111827")]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Studio")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 680)

        self.settings = QSettings("QRStudio", "QRStudio")
        self.theme_name = self.settings.value("theme", "Jellyfish")
        if self.theme_name not in THEMES:
            self.theme_name = "Jellyfish"
        self.matrix = None
        self.logo_img: QImage | None = None
        self.logo_path = ""
        self._loading = False

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(140)
        self._debounce.timeout.connect(self.update_qr)

        self._build_ui()
        self.defaults = self.snapshot()          # factory defaults, taken before loading saved values
        self.theme_combo.setCurrentText(self.theme_name)
        self.apply_theme()
        self.load_settings()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.backdrop = Backdrop()
        self.setCentralWidget(self.backdrop)
        outer = QVBoxLayout(self.backdrop)
        outer.setContentsMargins(22, 18, 22, 14)
        outer.setSpacing(14)

        # header
        header = QHBoxLayout()
        header.setSpacing(12)
        self.badge = LogoBadge()
        header.addWidget(self.badge)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        t = QLabel("QR Studio")
        t.setObjectName("title")
        s = QLabel("Design, style and export beautiful QR codes")
        s.setObjectName("subtitle")
        titles.addWidget(t)
        titles.addWidget(s)
        header.addLayout(titles)
        header.addStretch()
        header.addWidget(muted("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setFixedWidth(140)
        self.theme_combo.currentTextChanged.connect(self.set_theme)
        header.addWidget(self.theme_combo)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        outer.addLayout(body, 1)

        # ---------------- left: tabs
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(450)
        self.tabs.tabBar().setDrawBase(False)
        body.addWidget(self.tabs)
        self._tab_content()
        self._tab_design()
        self._tab_colors()
        self._tab_caption()
        self._tab_logo()

        # ---------------- right: preview + actions
        right = QVBoxLayout()
        right.setSpacing(12)
        self.preview = PreviewWidget()
        right.addWidget(self.preview, 1)
        actions = QHBoxLayout()
        self.save_btn = QPushButton("Save as...")
        self.save_btn.setObjectName("primary")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_file)
        self.copy_btn = QPushButton("Copy to clipboard")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_clipboard)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setToolTip("Restore all design options to their defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        actions.addWidget(self.save_btn, 2)
        actions.addWidget(self.copy_btn, 1)
        actions.addWidget(self.reset_btn)
        right.addLayout(actions)
        body.addLayout(right, 1)

        # ---------------- status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.setSizeGripEnabled(False)
        self.info_label = QLabel("")
        sb.addPermanentWidget(self.info_label)

    def _add_tab(self, name):
        page, lay = make_page()
        self.tabs.addTab(page, name)
        return lay

    # ---- Content tab
    def _tab_content(self):
        lay = self._add_tab("Content")
        c, l = make_card("Content type")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Text / URL", "Wi-Fi", "Email", "Phone"])
        self.type_combo.currentIndexChanged.connect(self._type_changed)
        l.addWidget(self.type_combo)

        # text
        self.w_text = QWidget()
        tl = QVBoxLayout(self.w_text)
        tl.setContentsMargins(0, 0, 0, 0)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Enter text, a URL, anything...")
        self.text_edit.setPlainText("https://example.com")
        self.text_edit.setFixedHeight(110)
        self.text_edit.textChanged.connect(self.schedule_update)
        tl.addWidget(self.text_edit)
        l.addWidget(self.w_text)

        # wifi
        self.w_wifi = QWidget()
        wl = QVBoxLayout(self.w_wifi)
        wl.setContentsMargins(0, 0, 0, 0)
        self.wifi_ssid = QLineEdit()
        self.wifi_ssid.setPlaceholderText("Network name (SSID)")
        self.wifi_pass = QLineEdit()
        self.wifi_pass.setPlaceholderText("Password")
        self.wifi_sec = QComboBox()
        self.wifi_sec.addItems(["WPA", "WEP", "None"])
        for w in (self.wifi_ssid, self.wifi_pass):
            w.textChanged.connect(self.schedule_update)
            wl.addWidget(w)
        self.wifi_sec.currentIndexChanged.connect(self.schedule_update)
        wl.addWidget(self.wifi_sec)
        l.addWidget(self.w_wifi)

        # email
        self.w_mail = QWidget()
        ml = QVBoxLayout(self.w_mail)
        ml.setContentsMargins(0, 0, 0, 0)
        self.mail_to = QLineEdit()
        self.mail_to.setPlaceholderText("name@example.com")
        self.mail_subject = QLineEdit()
        self.mail_subject.setPlaceholderText("Subject (optional)")
        self.mail_body = QLineEdit()
        self.mail_body.setPlaceholderText("Message (optional)")
        for w in (self.mail_to, self.mail_subject, self.mail_body):
            w.textChanged.connect(self.schedule_update)
            ml.addWidget(w)
        l.addWidget(self.w_mail)

        # phone
        self.w_phone = QWidget()
        pl = QVBoxLayout(self.w_phone)
        pl.setContentsMargins(0, 0, 0, 0)
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+1 555 123 4567")
        self.phone.textChanged.connect(self.schedule_update)
        pl.addWidget(self.phone)
        l.addWidget(self.w_phone)

        lay.addWidget(c)
        lay.addStretch()
        self._type_changed()

    def _type_changed(self):
        i = self.type_combo.currentIndex()
        for idx, w in enumerate((self.w_text, self.w_wifi, self.w_mail, self.w_phone)):
            w.setVisible(idx == i)
        self.schedule_update()

    def get_data(self) -> str:
        i = self.type_combo.currentIndex()
        if i == 0:
            return self.text_edit.toPlainText()
        if i == 1:
            ssid = self.wifi_ssid.text()
            if not ssid:
                return ""
            sec = {"WPA": "WPA", "WEP": "WEP", "None": "nopass"}[self.wifi_sec.currentText()]
            pw = "" if sec == "nopass" else f"P:{wifi_escape(self.wifi_pass.text())};"
            return f"WIFI:T:{sec};S:{wifi_escape(ssid)};{pw};"
        if i == 2:
            to = self.mail_to.text().strip()
            if not to:
                return ""
            params = []
            if self.mail_subject.text():
                params.append("subject=" + quote(self.mail_subject.text()))
            if self.mail_body.text():
                params.append("body=" + quote(self.mail_body.text()))
            return f"mailto:{to}" + ("?" + "&".join(params) if params else "")
        ph = self.phone.text().strip()
        return f"tel:{ph}" if ph else ""

    # ---- Design tab
    def _tab_design(self):
        lay = self._add_tab("Design")
        c, l = make_card("Size")
        self.size_s = LabeledSlider("Export size", 100, 2000, 512, " px")
        self.border_s = LabeledSlider("Quiet zone", 0, 12, 4, " modules")
        self.corner_s = LabeledSlider("Background corner radius", 0, 25, 0, " %")
        for w in (self.size_s, self.border_s, self.corner_s):
            w.changed.connect(self.schedule_update)
            l.addWidget(w)
        lay.addWidget(c)

        c, l = make_card("Modules")
        l.addWidget(muted("Shape"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Square", "Rounded", "Dots", "Diamond"])
        self.style_combo.currentIndexChanged.connect(self.schedule_update)
        l.addWidget(self.style_combo)
        self.round_s = LabeledSlider("Roundness (Rounded shape)", 0, 50, 30, " %")
        self.scale_s = LabeledSlider("Module size (spacing)", 40, 100, 100, " %")
        for w in (self.round_s, self.scale_s):
            w.changed.connect(self.schedule_update)
            l.addWidget(w)
        lay.addWidget(c)

        c, l = make_card("Error correction")
        self.ec_combo = QComboBox()
        self.ec_combo.addItems(list(self.EC_LEVELS.keys()))
        self.ec_combo.setCurrentIndex(1)
        self.ec_combo.currentIndexChanged.connect(self.schedule_update)
        l.addWidget(self.ec_combo)
        lay.addWidget(c)
        lay.addStretch()

    # ---- Colors tab
    def _tab_colors(self):
        lay = self._add_tab("Colors")
        c, l = make_card("Foreground")
        self.grad_cb = QCheckBox("Use gradient")
        self.grad_cb.toggled.connect(self.schedule_update)
        l.addWidget(self.grad_cb)

        row = QHBoxLayout()
        for label, attr, color in (("Color 1", "fg_btn", "#111827"), ("Color 2 (gradient)", "fg2_btn", "#6D28D9")):
            col = QVBoxLayout()
            col.addWidget(muted(label))
            btn = ColorButton(QColor(color), self.schedule_update)
            setattr(self, attr, btn)
            col.addWidget(btn)
            row.addLayout(col)
        l.addLayout(row)

        l.addWidget(muted("Gradient direction"))
        self.grad_dir = QComboBox()
        self.grad_dir.addItems(["Diagonal", "Horizontal", "Vertical"])
        self.grad_dir.currentIndexChanged.connect(self.schedule_update)
        l.addWidget(self.grad_dir)

        self.eye_cb = QCheckBox("Custom color for the 3 corner eyes")
        self.eye_cb.toggled.connect(self.schedule_update)
        l.addWidget(self.eye_cb)
        self.eye_btn = ColorButton(QColor("#111827"), self.schedule_update)
        l.addWidget(self.eye_btn)
        lay.addWidget(c)

        c, l = make_card("Background")
        self.bg_btn = ColorButton(QColor("#FFFFFF"), self.schedule_update)
        l.addWidget(self.bg_btn)
        self.transparent_cb = QCheckBox("Transparent background")
        self.transparent_cb.toggled.connect(self.schedule_update)
        l.addWidget(self.transparent_cb)
        swap = QPushButton("Swap foreground / background")
        swap.setCursor(Qt.PointingHandCursor)
        swap.clicked.connect(self.swap_colors)
        l.addWidget(swap)
        lay.addWidget(c)

        c, l = make_card("Presets")
        row = QHBoxLayout()
        for fg, fg2, bg in self.PRESETS:
            b = QPushButton()
            b.setFixedSize(38, 38)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {fg},stop:1 {fg2 or fg});"
                f" border:4px solid {bg}; border-radius:19px; padding:0; }}"
                f"QPushButton:hover {{ border:4px solid rgba(128,128,128,0.8); }}")
            b.clicked.connect(lambda _=False, a=fg, b2=fg2, c2=bg: self.apply_preset(a, b2, c2))
            row.addWidget(b)
        row.addStretch()
        l.addLayout(row)
        lay.addWidget(c)
        lay.addStretch()

    # ---- Caption tab
    def _tab_caption(self):
        lay = self._add_tab("Caption")
        c, l = make_card("Caption text")
        self.cap_edit = QPlainTextEdit()
        self.cap_edit.setPlaceholderText("Text shown next to the QR code (multi-line OK)")
        self.cap_edit.setPlainText("SCAN ME")
        self.cap_edit.setFixedHeight(70)
        self.cap_edit.textChanged.connect(self.schedule_update)
        l.addWidget(self.cap_edit)
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.addWidget(muted("Position"))
        self.cap_pos = QComboBox()
        self.cap_pos.addItems(["Below", "Above", "None"])
        self.cap_pos.currentIndexChanged.connect(self.schedule_update)
        col.addWidget(self.cap_pos)
        row.addLayout(col)
        col = QVBoxLayout()
        col.addWidget(muted("Alignment"))
        self.cap_align = QComboBox()
        self.cap_align.addItems(["Center", "Left", "Right"])
        self.cap_align.currentIndexChanged.connect(self.schedule_update)
        col.addWidget(self.cap_align)
        row.addLayout(col)
        l.addLayout(row)
        lay.addWidget(c)

        c, l = make_card("Font")
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.schedule_update)
        l.addWidget(self.font_combo)
        row = QHBoxLayout()
        self.bold_cb = QCheckBox("Bold")
        self.bold_cb.setChecked(True)
        self.italic_cb = QCheckBox("Italic")
        for cb in (self.bold_cb, self.italic_cb):
            cb.toggled.connect(self.schedule_update)
            row.addWidget(cb)
        row.addStretch()
        l.addLayout(row)
        self.fsize_s = LabeledSlider("Text size (relative to QR)", 3, 20, 7, " %")
        self.dist_s = LabeledSlider("Space between QR code and caption", 0, 30, 4, " %")
        self.gap_s = LabeledSlider("Space between caption and image edge", 0, 30, 4, " %")
        for w in (self.fsize_s, self.dist_s, self.gap_s):
            w.changed.connect(self.schedule_update)
            l.addWidget(w)
        l.addWidget(muted("Text color"))
        self.cap_color = ColorButton(QColor("#111827"), self.schedule_update)
        l.addWidget(self.cap_color)
        lay.addWidget(c)
        lay.addStretch()

    # ---- Logo tab
    def _tab_logo(self):
        lay = self._add_tab("Logo")
        c, l = make_card("Center logo")
        self.logo_label = muted("No logo selected")
        l.addWidget(self.logo_label)
        row = QHBoxLayout()
        pick = QPushButton("Choose image...")
        pick.setCursor(Qt.PointingHandCursor)
        pick.clicked.connect(self.choose_logo)
        clear = QPushButton("Remove")
        clear.setCursor(Qt.PointingHandCursor)
        clear.clicked.connect(self.clear_logo)
        row.addWidget(pick, 1)
        row.addWidget(clear)
        l.addLayout(row)
        self.logo_size_s = LabeledSlider("Logo size", 8, 30, 20, " %")
        self.logo_pad_s = LabeledSlider("Clear space around logo", 0, 40, 12, " %")
        for w in (self.logo_size_s, self.logo_pad_s):
            w.changed.connect(self.schedule_update)
            l.addWidget(w)
        self.logo_round_cb = QCheckBox("Round the logo corners")
        self.logo_round_cb.setChecked(True)
        self.logo_round_cb.toggled.connect(self.schedule_update)
        l.addWidget(self.logo_round_cb)
        note = muted("Adding a logo switches error correction to High so the code stays scannable.")
        note.setWordWrap(True)
        l.addWidget(note)
        lay.addWidget(c)
        lay.addStretch()


    # ------------------------------------------------- Persistence / reset
    CONTENT_KEYS = {"content_type", "text", "wifi_ssid", "wifi_sec", "mail_to",
                    "mail_subject", "mail_body", "phone"}

    def _specs(self):
        """(key, widget, kind) for every option that is saved and restored.
        The Wi-Fi password is intentionally NOT stored on disk."""
        return [
            ("content_type", self.type_combo, "index"), ("text", self.text_edit, "plain"),
            ("wifi_ssid", self.wifi_ssid, "line"), ("wifi_sec", self.wifi_sec, "combo"),
            ("mail_to", self.mail_to, "line"), ("mail_subject", self.mail_subject, "line"),
            ("mail_body", self.mail_body, "line"), ("phone", self.phone, "line"),
            ("size", self.size_s, "slider"), ("border", self.border_s, "slider"),
            ("corner", self.corner_s, "slider"), ("style", self.style_combo, "combo"),
            ("roundness", self.round_s, "slider"), ("module_scale", self.scale_s, "slider"),
            ("ec", self.ec_combo, "combo"),
            ("gradient", self.grad_cb, "check"), ("fg", self.fg_btn, "color"),
            ("fg2", self.fg2_btn, "color"), ("grad_dir", self.grad_dir, "combo"),
            ("eye_custom", self.eye_cb, "check"), ("eye", self.eye_btn, "color"),
            ("bg", self.bg_btn, "color"), ("transparent", self.transparent_cb, "check"),
            ("caption", self.cap_edit, "plain"), ("cap_pos", self.cap_pos, "combo"),
            ("cap_align", self.cap_align, "combo"), ("font", self.font_combo, "font"),
            ("bold", self.bold_cb, "check"), ("italic", self.italic_cb, "check"),
            ("font_pct", self.fsize_s, "slider"), ("cap_dist", self.dist_s, "slider"),
            ("cap_gap", self.gap_s, "slider"), ("cap_color", self.cap_color, "color"),
            ("logo_pct", self.logo_size_s, "slider"), ("logo_pad", self.logo_pad_s, "slider"),
            ("logo_round", self.logo_round_cb, "check"),
        ]

    @staticmethod
    def _get(w, kind):
        return {"index": lambda: w.currentIndex(), "plain": lambda: w.toPlainText(),
                "line": lambda: w.text(), "combo": lambda: w.currentText(),
                "slider": lambda: w.value(), "check": lambda: w.isChecked(),
                "color": lambda: w.color.name(), "font": lambda: w.currentFont().family()}[kind]()

    @staticmethod
    def _set(w, kind, v):
        if kind == "index":
            w.setCurrentIndex(int(v))
        elif kind == "slider":
            w.setValue(int(v))
        elif kind == "check":
            w.setChecked(v if isinstance(v, bool) else str(v).lower() == "true")
        elif kind == "plain":
            w.setPlainText(str(v))
        elif kind == "line":
            w.setText(str(v))
        elif kind == "combo":
            w.setCurrentText(str(v))
        elif kind == "color":
            w.set_color(QColor(str(v)))
        elif kind == "font":
            w.setCurrentFont(QFont(str(v)))

    def snapshot(self) -> dict:
        return {k: self._get(w, kind) for k, w, kind in self._specs()}

    def _apply(self, values: dict):
        self._loading = True
        try:
            for key, w, kind in self._specs():
                if key in values:
                    try:
                        self._set(w, kind, values[key])
                    except Exception:
                        pass
        finally:
            self._loading = False

    def save_settings(self):
        if self._loading:
            return
        for k, v in self.snapshot().items():
            self.settings.setValue("ui/" + k, v)
        self.settings.setValue("ui/logo_path", self.logo_path)
        self.settings.setValue("geometry", self.saveGeometry())

    def load_settings(self):
        vals = {k: self.settings.value("ui/" + k) for k, _, _ in self._specs()
                if self.settings.contains("ui/" + k)}
        self._apply(vals)

        path = self.settings.value("ui/logo_path", "")
        if path and os.path.exists(path):
            img = QImage(path)
            if not img.isNull():
                self.logo_img = img.convertToFormat(QImage.Format_ARGB32)
                self.logo_path = path
                self.logo_label.setText(os.path.basename(path))

        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        self.update_qr()
        self.status("Settings restored", 3000)

    def reset_defaults(self):
        """Reset every design option. Your typed content and the theme are kept."""
        self._apply({k: v for k, v in self.defaults.items() if k not in self.CONTENT_KEYS})
        self.logo_img = None
        self.logo_path = ""
        self.logo_label.setText("No logo selected")
        self.update_qr()
        self.status("✔ Design options reset to defaults")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    # ------------------------------------------------------------- Theme
    def set_theme(self, name):
        if name not in THEMES:
            return
        self.theme_name = name
        self.settings.setValue("theme", name)
        self.apply_theme()
        self.status(f"Theme: {name}")

    def apply_theme(self):
        th = THEMES[self.theme_name]
        self.setStyleSheet(build_qss(th))
        self.backdrop.set_theme(th)
        self.preview.set_theme(th)
        self.badge.set_theme(th)

    # ------------------------------------------------------------ Helpers
    def status(self, msg, ms=4500):
        self.statusBar().showMessage(msg, ms)

    def schedule_update(self, *_):
        if not self._loading:
            self._debounce.start()

    def swap_colors(self):
        a, b = self.fg_btn.color, self.bg_btn.color
        self.fg_btn.set_color(b)
        self.bg_btn.set_color(a)
        self.schedule_update()

    def apply_preset(self, fg, fg2, bg):
        self.fg_btn.set_color(QColor(fg))
        self.eye_btn.set_color(QColor(fg))
        self.cap_color.set_color(QColor(fg))
        self.bg_btn.set_color(QColor(bg))
        if fg2:
            self.fg2_btn.set_color(QColor(fg2))
        self.grad_cb.setChecked(bool(fg2))
        self.transparent_cb.setChecked(False)
        self.schedule_update()

    def choose_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose logo", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg)")
        if not path:
            return
        img = QImage(path)
        if img.isNull():
            self.status("Could not load that image")
            return
        self.logo_img = img.convertToFormat(QImage.Format_ARGB32)
        self.logo_path = path
        self.logo_label.setText(os.path.basename(path))
        self.schedule_update()

    def clear_logo(self):
        self.logo_img = None
        self.logo_path = ""
        self.logo_label.setText("No logo selected")
        self.schedule_update()

    def collect_opts(self) -> QROpts:
        return QROpts(
            size=self.size_s.value(), border=self.border_s.value(),
            style=self.style_combo.currentText(), roundness=self.round_s.value(),
            module_scale=self.scale_s.value(), corner=self.corner_s.value(),
            fg=self.fg_btn.color, fg2=self.fg2_btn.color, gradient=self.grad_cb.isChecked(),
            grad_dir=self.grad_dir.currentText(),
            eye_custom=self.eye_cb.isChecked(), eye=self.eye_btn.color,
            bg=self.bg_btn.color, transparent=self.transparent_cb.isChecked(),
            caption=self.cap_edit.toPlainText(), cap_pos=self.cap_pos.currentText(),
            font_family=self.font_combo.currentFont().family(), font_pct=self.fsize_s.value(),
            bold=self.bold_cb.isChecked(), italic=self.italic_cb.isChecked(),
            align=self.cap_align.currentText(), cap_color=self.cap_color.color,
            cap_gap=self.gap_s.value(), cap_dist=self.dist_s.value(),
            logo=self.logo_img, logo_pct=self.logo_size_s.value(),
            logo_pad=self.logo_pad_s.value(), logo_round=self.logo_round_cb.isChecked(),
        )

    # ------------------------------------------------------- QR generation
    def update_qr(self):
        self.save_settings()
        data = self.get_data()
        if not data.strip():
            self.matrix = None
            self.preview.set_image(None)
            self.info_label.setText("")
            self.status("Waiting for input...", 0)
            return

        o = self.collect_opts()
        ec = ERROR_CORRECT_H if o.logo is not None else self.EC_LEVELS[self.ec_combo.currentText()]
        try:
            self.matrix, version = make_matrix(data, ec)
        except Exception as e:
            self.matrix = None
            self.preview.set_image(None)
            self.status(f"Could not generate QR code: {e}", 0)
            return

        # preview is capped for speed; export renders at the real size
        self.preview.set_image(render_image(self.matrix, replace(o, size=min(o.size, 900))))

        n = len(self.matrix)
        W, H, *_ = compute_layout(o, n)
        self.info_label.setText(f"Version {version}  •  {n}×{n} modules  •  {int(W)}×{int(math.ceil(H))} px")

        ratios = [contrast_ratio(o.fg, o.bg)]
        if o.gradient:
            ratios.append(contrast_ratio(o.fg2, o.bg))
        if not o.transparent and min(ratios) < 3:
            self.status("⚠ Low contrast between colors – the code may be hard to scan", 0)
        elif not o.transparent and luminance(o.fg) > luminance(o.bg):
            self.status("Note: light-on-dark (inverted) codes aren't read by every scanner", 0)
        elif o.logo is not None:
            self.status("Logo added – error correction set to High", 3000)
        else:
            self.status("QR code updated", 2000)

    # -------------------------------------------------------------- Export
    def save_file(self):
        if not self.matrix:
            self.status("Nothing to save yet – enter some content first")
            return
        path, selected = QFileDialog.getSaveFileName(
            self, "Save QR code", "qrcode.png",
            "PNG image (*.png);;JPEG image (*.jpg);;SVG vector (*.svg)")
        if not path:
            self.status("Save cancelled")
            return

        low = path.lower()
        if "SVG" in selected and not low.endswith(".svg"):
            path += ".svg"
        elif "JPEG" in selected and not low.endswith((".jpg", ".jpeg")):
            path += ".jpg"
        elif "PNG" in selected and not low.endswith(".png"):
            path += ".png"
        low = path.lower()

        try:
            o = self.collect_opts()
            if low.endswith(".svg"):
                W, H, *_ = compute_layout(o, len(self.matrix))
                gen = QSvgGenerator()
                gen.setFileName(path)
                gen.setSize(QSize(int(W), int(math.ceil(H))))
                gen.setViewBox(QRect(0, 0, int(W), int(math.ceil(H))))
                gen.setTitle("QR Code")
                p = QPainter(gen)
                draw_all(p, self.matrix, o)
                p.end()
            else:
                jpg = low.endswith((".jpg", ".jpeg"))
                if jpg:
                    o = replace(o, transparent=False)
                img = render_image(self.matrix, o)
                if jpg:
                    img = img.convertToFormat(QImage.Format_RGB32)
                if not img.save(path):
                    raise IOError("Qt could not write the file")
            self.status(f"✔ Saved to {path}", 7000)
        except Exception as e:
            self.status(f"Save failed: {e}", 8000)

    def copy_clipboard(self):
        if not self.matrix:
            self.status("Nothing to copy yet – enter some content first")
            return
        QApplication.clipboard().setPixmap(QPixmap.fromImage(render_image(self.matrix, self.collect_opts())))
        self.status("✔ QR code copied to clipboard")


def resource_path(name: str) -> str:
    """Works both when running the script and inside a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    # Windows: group the taskbar button under our own identity so our icon is shown
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("QRStudio.App.1")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(resource_path("app_icon.png")))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()