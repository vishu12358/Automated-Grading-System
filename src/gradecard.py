"""
Professional Grade Card Generator
Lloyd Institute of Engineering & Technology
Generates secure, visually rich PDF grade cards with verification features.
"""

import io
import math
import re
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from src.grading import assign_grade

# ─── Paths ───────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "images.jpg"

# ─── Color Palette ───────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0B1D3A")
NAVY_MID = colors.HexColor("#162D54")
GOLD = colors.HexColor("#C8A84E")
GOLD_DARK = colors.HexColor("#9E7F2E")
GOLD_LIGHT = colors.HexColor("#FDF6E3")
GOLD_PALE = colors.HexColor("#F7EDD4")
RED_ACCENT = colors.HexColor("#B71C1C")
ROW_ALT = colors.HexColor("#EDF2F8")
ROW_ALT2 = colors.HexColor("#F5F8FC")
BORDER_GRAY = colors.HexColor("#B0BEC5")
BORDER_LIGHT = colors.HexColor("#D6DEE8")
TEXT_DARK = colors.HexColor("#1A1A1A")
TEXT_GRAY = colors.HexColor("#5F6368")
TEXT_LIGHT = colors.HexColor("#9AA0A6")
SHADOW = colors.HexColor("#D0D5DD")
WHITE = colors.white

# ─── Typography ──────────────────────────────────────────────────────────────
FONT_REGULAR = "Times-Roman"
FONT_BOLD = "Times-Bold"
FONT_ITALIC = "Times-Italic"
FONT_BOLD_ITALIC = "Times-BoldItalic"
FONT_MONO = "Courier"

# ─── Grade Configuration ────────────────────────────────────────────────────
GRADE_LABELS = {
    "A+": "OUTSTANDING",
    "A": "EXCELLENT",
    "B": "GOOD",
    "C": "SATISFACTORY",
    "D": "NEEDS IMPROVEMENT",
}

GRADE_COLORS = {
    "A+": colors.HexColor("#1B5E20"),
    "A": colors.HexColor("#2E7D32"),
    "B": colors.HexColor("#1565C0"),
    "C": colors.HexColor("#E65100"),
    "D": colors.HexColor("#B71C1C"),
}

GRADE_BG_COLORS = {
    "A+": colors.HexColor("#E8F5E9"),
    "A": colors.HexColor("#E8F5E9"),
    "B": colors.HexColor("#E3F2FD"),
    "C": colors.HexColor("#FFF3E0"),
    "D": colors.HexColor("#FFEBEE"),
}

CLASSIFICATION_MAP = {
    "A+": "DISTINCTION",
    "A": "FIRST CLASS",
    "B": "SECOND CLASS – UPPER",
    "C": "SECOND CLASS – LOWER",
    "D": "PASS",
}

PERFORMANCE_MESSAGES = {
    "A+": "Exceptional mastery demonstrated across all assessments. Your consistency and depth of understanding reflect outstanding academic dedication.",
    "A": "Strong conceptual grasp and reliable performance throughout. Well-equipped for advanced academic and professional challenges ahead.",
    "B": "Solid foundation with identifiable growth areas. Strategic focus on weaker topics will unlock your full academic potential.",
    "C": "Adequate understanding with clear improvement areas. Consistent practice and structured revision will yield significant progress.",
    "D": "Foundational gaps require immediate attention. Engage with faculty support, attend remedial sessions, and commit to a structured study plan.",
}

GRADING_SCALE = [
    ("A+", "90 – 100", colors.HexColor("#1B5E20")),
    ("A", "80 – 89", colors.HexColor("#2E7D32")),
    ("B", "70 – 79", colors.HexColor("#1565C0")),
    ("C", "60 – 69", colors.HexColor("#E65100")),
    ("D", "50 – 59", colors.HexColor("#B71C1C")),
    ("F", "< 50", colors.HexColor("#78909C")),
]

QUIZ_MAX_MARKS = 100
PAGE_W, PAGE_H = letter
MARGIN = 24
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN
INNER_PAD = 12


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_value(value, default=""):
    """Return string representation, handling NaN/None gracefully."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value)


def _get_quiz_rows(row):
    """Extract and sort quiz column names from a DataFrame row."""
    return sorted(
        [col for col in row.index if re.match(r"^Quiz\d+$", col)],
        key=lambda col: int(re.search(r"(\d+)", col).group(1)),
    )


def _grade_label(grade):
    return GRADE_LABELS.get(str(grade).strip().upper(), "COMMENDABLE")


def _performance_message(grade):
    return PERFORMANCE_MESSAGES.get(str(grade).strip().upper(), PERFORMANCE_MESSAGES["C"])


def _classification(grade):
    return CLASSIFICATION_MAP.get(str(grade).strip().upper(), "PASS")


def _grade_color(grade):
    return GRADE_COLORS.get(str(grade).strip().upper(), TEXT_GRAY)


def _grade_bg(grade):
    return GRADE_BG_COLORS.get(str(grade).strip().upper(), WHITE)


def _generate_hash(enrollment_no, total_marks, grade):
    """Generate a short verification hash for the grade card."""
    payload = f"{enrollment_no}:{total_marks}:{grade}:{datetime.now().strftime('%Y-%m-%d')}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16].upper()


def _generate_doc_number(index):
    """Generate a formal document reference number."""
    return f"LIET/GC/2024-25/{str(index + 1).zfill(4)}"


def _truncate_text(c, text, font, size, max_width, ellipsis="..."):
    """Truncate text to fit within max_width, appending ellipsis if needed."""
    if c.stringWidth(text, font, size) <= max_width:
        return text
    while len(text) > 0 and c.stringWidth(text + ellipsis, font, size) > max_width:
        text = text[:-1]
    return text + ellipsis


def _wrap_text(c, text, font, size, max_width):
    """Word-wrap text into lines that fit within max_width."""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if c.stringWidth(test, font, size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
#  DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_outer_border(c):
    """Triple-line border with gold accent and corner diamonds."""
    x, y, w, h = MARGIN, MARGIN, CONTENT_W, CONTENT_H

    c.setStrokeColor(NAVY)
    c.setLineWidth(2.0)
    c.rect(x, y, w, h)

    c.setLineWidth(0.6)
    c.rect(x + 5, y + 5, w - 10, h - 10)

    c.setStrokeColor(GOLD)
    c.setLineWidth(0.35)
    c.rect(x + 8, y + 8, w - 16, h - 16)

    d = 4.5
    for cx, cy in [
        (x + 2, y + h - 2), (x + w - 2, y + h - 2),
        (x + 2, y + 2), (x + w - 2, y + 2),
    ]:
        c.setFillColor(GOLD)
        p = c.beginPath()
        p.moveTo(cx, cy + d)
        p.lineTo(cx + d, cy)
        p.lineTo(cx, cy - d)
        p.lineTo(cx - d, cy)
        p.close()
        c.drawPath(p, fill=1, stroke=0)


def _draw_watermark(c):
    """Semi-transparent centred logo watermark."""
    if not LOGO_PATH.exists():
        return
    size = 260
    x = (PAGE_W - size) / 2
    y = (PAGE_H - size) / 2 - 15
    c.saveState()
    c.setFillAlpha(0.04)
    c.drawImage(str(LOGO_PATH), x, y, width=size, height=size,
                preserveAspectRatio=True, mask="auto")
    c.restoreState()


def _draw_header(c, top_y):
    """Logo, institution name, accreditation line, decorative divider."""
    y = top_y

    # --- Logo ---
    if LOGO_PATH.exists():
        logo_h = 58
        c.drawImage(str(LOGO_PATH), (PAGE_W - logo_h) / 2, y - logo_h,
                    width=logo_h, height=logo_h,
                    preserveAspectRatio=True, mask="auto")
        y -= logo_h + 6
    else:
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 15)
        c.drawCentredString(PAGE_W / 2, y - 20, "LLOYD")
        y -= 28

    # --- Institution name ---
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 16)
    c.drawCentredString(PAGE_W / 2, y - 14, "LLOYD INSTITUTE OF ENGINEERING & TECHNOLOGY")
    y -= 16

    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(PAGE_W / 2, y - 12,
                        "Approved by AICTE, New Delhi  |  Affiliated to Dr. A.P.J. Abdul Kalam Technical University, Lucknow")
    y -= 18

    # --- Decorative divider ---
    half = (CONTENT_W - 100) / 2
    cx = PAGE_W / 2
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.7)
    c.line(cx - half, y, cx - 14, y)
    c.line(cx + 14, y, cx + half, y)
    c.setFillColor(NAVY)
    c.circle(cx, y, 2.8, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.circle(cx, y, 1.3, fill=1, stroke=0)

    return y - 10


def _draw_title_badge(c, y, doc_number):
    """Centred title pill + document reference number."""
    badge_w, badge_h = 230, 26
    bx = (PAGE_W - badge_w) / 2

    c.setFillColor(NAVY)
    c.roundRect(bx, y - badge_h, badge_w, badge_h, 5, fill=1, stroke=0)

    # Gold accent line above badge
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    c.line(bx + 20, y, bx + badge_w - 20, y)

    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 13)
    c.drawCentredString(PAGE_W / 2, y - 18, "STUDENT GRADE CARD")

    # Document number
    c.setFont(FONT_MONO, 7.5)
    c.setFillColor(TEXT_LIGHT)
    c.drawRightString(PAGE_W - MARGIN - INNER_PAD - 2, y - 12, doc_number)

    return y - badge_h - 6


def _draw_shadow_rect(c, x, y, w, h, r=6, offset=1.5):
    """Draw a card-style rectangle with a subtle drop shadow."""
    c.setFillColor(SHADOW)
    c.roundRect(x + offset, y - offset, w, h, r, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def _draw_info_box(c, box_top, fields):
    """Student information card with left accent bar and two-column layout."""
    box_x = MARGIN + INNER_PAD
    box_w = CONTENT_W - 2 * INNER_PAD
    box_h = 84

    _draw_shadow_rect(c, box_x, box_top - box_h, box_w, box_h)

    # Gold accent bar on left edge
    c.setFillColor(GOLD)
    c.rect(box_x, box_top - box_h, 3.5, box_h, fill=1, stroke=0)

    lx = box_x + 14
    lv = lx + 90
    rx = box_x + box_w / 2 + 8
    rv = rx + 90
    line_h = 18
    sy = box_top - 20

    # Draw the student name as a full-width field so long names don't overlap the right column.
    if fields and fields[0][0].strip().lower() == "name":
        label, value = fields[0]
        c.setFont(FONT_BOLD, 9)
        c.setFillColor(NAVY)
        c.drawString(lx, sy, label)
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(TEXT_DARK)
        c.drawString(lv, sy, ": " + _truncate_text(c, value, FONT_REGULAR, 9, box_w - 120))
        remaining = fields[1:]
        sy -= line_h
    else:
        remaining = fields

    left = remaining[:3]
    right = remaining[3:]

    for i, (label, value) in enumerate(left):
        yy = sy - i * line_h
        c.setFont(FONT_BOLD, 9)
        c.setFillColor(NAVY)
        c.drawString(lx, yy, label)
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(TEXT_DARK)
        c.drawString(lv, yy, ": " + _truncate_text(c, value, FONT_REGULAR, 9, box_w / 2 - 100))

    for i, (label, value) in enumerate(right):
        yy = sy - i * line_h
        c.setFont(FONT_BOLD, 9)
        c.setFillColor(NAVY)
        c.drawString(rx, yy, label)
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(TEXT_DARK)
        c.drawString(rv, yy, ": " + _truncate_text(c, value, FONT_REGULAR, 9, box_w / 2 - 100))

    return box_top - box_h


def _draw_grades_table(c, table_top, quiz_rows, default_grade):
    """Professional assessment table with alternating rows and grade badges."""
    tx = MARGIN + INNER_PAD
    tw = CONTENT_W - 2 * INNER_PAD
    hdr_h = 22
    row_h = min(20, max(16, 160 / max(len(quiz_rows), 1)))

    # Header
    c.setFillColor(NAVY)
    c.roundRect(tx, table_top - hdr_h, tw, hdr_h, 4, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 9)
    c.drawString(tx + 10, table_top - 15, "S.No.")
    c.drawString(tx + 48, table_top - 15, "Assessment")
    c.drawRightString(tx + tw - 155, table_top - 15, "Maximum Marks")
    c.drawRightString(tx + tw - 72, table_top - 15, "Obtained")
    c.drawRightString(tx + tw - 14, table_top - 15, "Grade")

    ry = table_top - hdr_h
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.4)

    for idx, (label, score) in enumerate(quiz_rows, start=1):
        ry -= row_h

        if idx % 2 == 0:
            c.setFillColor(ROW_ALT)
            c.rect(tx, ry, tw, row_h, fill=1, stroke=0)

        c.line(tx, ry, tx + tw, ry)

        q_grade = assign_grade(float(score)) if score else default_grade
        gc = _grade_color(q_grade)

        c.setFillColor(TEXT_DARK)
        c.setFont(FONT_REGULAR, 8.5)
        c.drawString(tx + 10, ry - 13, str(idx))
        c.drawString(tx + 48, ry - 13, label)
        c.drawRightString(tx + tw - 155, ry - 13, str(QUIZ_MAX_MARKS))
        c.drawRightString(tx + tw - 72, ry - 13, f"{score:.0f}" if score else "-")

        # Grade pill
        pill_w = 28
        pill_h = 13
        pill_x = tx + tw - 14 - pill_w
        pill_y = ry + (row_h - pill_h) / 2
        c.setFillColor(gc)
        c.roundRect(pill_x, pill_y, pill_w, pill_h, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 7.5)
        c.drawCentredString(pill_x + pill_w / 2, pill_y + 3, str(q_grade))

    ry -= 0
    c.line(tx, ry, tx + tw, ry)

    # Outer border
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.rect(tx, ry, tw, table_top - hdr_h - ry, fill=0, stroke=1)

    return ry


def _draw_gauge(c, cx, cy, radius, percentage):
    """Semicircular gauge showing overall percentage with color zones."""
    pct = max(0.0, min(100.0, float(percentage)))
    r = radius
    thick = 7

    zones = [
        (0, 50, "#EF9A9A", "#C62828"),
        (50, 60, "#FFCC80", "#E65100"),
        (60, 70, "#FFF59D", "#F9A825"),
        (70, 80, "#90CAF9", "#1565C0"),
        (80, 100, "#A5D6A7", "#2E7D32"),
    ]

    # Background arcs (light)
    c.setLineCap(1)
    c.setLineWidth(thick + 2)
    for lo, hi, bg, _ in zones:
        sa = 180 - lo * 1.8
        ea = 180 - hi * 1.8
        c.setStrokeColor(colors.HexColor(bg))
        c.arc(cx - r, cy - r, cx + r, cy + r, sa, ea - sa)

    # Active arcs (vivid)
    c.setLineWidth(thick)
    for lo, hi, _, fg in zones:
        if pct <= lo:
            break
        actual = min(pct, hi)
        sa = 180 - lo * 1.8
        ea = 180 - actual * 1.8
        c.setStrokeColor(colors.HexColor(fg))
        c.arc(cx - r, cy - r, cx + r, cy + r, sa, ea - sa)

    # Tick marks
    c.setLineCap(0)
    for tp in range(0, 101, 25):
        ta = math.radians(180 - tp * 1.8)
        ri = r - thick / 2 - 3
        ro = r + thick / 2 + 3
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.2 if tp % 50 == 0 else 0.5)
        c.line(cx + ri * math.cos(ta), cy + ri * math.sin(ta),
               cx + ro * math.cos(ta), cy + ro * math.sin(ta))

    # Needle
    needle_a = math.radians(180 - pct * 1.8)
    nl = r - thick / 2 - 6
    nx = cx + nl * math.cos(needle_a)
    ny = cy + nl * math.sin(needle_a)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.8)
    c.setLineCap(1)
    c.line(cx, cy, nx, ny)
    c.setFillColor(NAVY)
    c.circle(cx, cy, 3, fill=1, stroke=0)

    # Center text
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 16)
    c.drawCentredString(cx, cy + 8, f"{pct:.1f}%")
    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(cx, cy - 4, "OVERALL")


def _draw_mini_bars(c, x, y, width, quiz_rows, bar_h=11, gap=3):
    """Horizontal progress bars for each quiz, coloured by grade."""
    for i, (label, score) in enumerate(quiz_rows):
        by = y - i * (bar_h + gap)
        pct = score / QUIZ_MAX_MARKS if QUIZ_MAX_MARKS else 0
        bw = width * pct

        qg = assign_grade(float(score)) if score else "D"
        gc = _grade_color(qg)

        # Background track
        c.setFillColor(colors.HexColor("#E8EAF6"))
        c.roundRect(x, by, width, bar_h, 2, fill=1, stroke=0)

        # Filled bar
        c.setFillColor(gc)
        if bw > 4:
            c.roundRect(x, by, bw, bar_h, 2, fill=1, stroke=0)
        else:
            c.rect(x, by, max(bw, 2), bar_h, fill=1, stroke=0)

        # Labels
        c.setFont(FONT_BOLD, 6.5)
        c.setFillColor(WHITE if bw > 28 else TEXT_DARK)
        c.drawString(x + 3, by + 2.5, label)

        c.setFont(FONT_BOLD, 6.5)
        c.setFillColor(WHITE if bw > width - 24 else TEXT_DARK)
        c.drawRightString(x + width - 3, by + 2.5, f"{score:.0f}")


def _draw_grade_badge(c, cx, cy, grade):
    """Central grade circle with wreath, label, and classification."""
    label = _grade_label(grade)
    classif = _classification(grade)
    gc = _grade_color(grade)
    gbc = _grade_bg(grade)

    # Wreath dots
    for angle in range(0, 360, 24):
        rad = math.radians(angle)
        dx = cx + 38 * math.cos(rad)
        dy = cy + 6 + 38 * math.sin(rad)
        c.setFillColor(GOLD)
        c.circle(dx, dy, 3.2, fill=1, stroke=0)

    # White circle
    c.setFillColor(WHITE)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.circle(cx, cy + 6, 30, fill=1, stroke=1)

    # Grade letter
    c.setFillColor(gc)
    c.setFont(FONT_BOLD, 32)
    c.drawCentredString(cx, cy - 4, str(grade))

    # Label ribbon
    rw, rh = 100, 15
    rx = cx - rw / 2
    ry = cy - 24
    c.setFillColor(gc)
    c.roundRect(rx, ry, rw, rh, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 7.5)
    c.drawCentredString(cx, ry + 4, label)

    # Classification
    c.setFillColor(GOLD_DARK)
    c.setFont(FONT_BOLD, 7)
    c.drawCentredString(cx, ry - 10, classif)


def _draw_performance_section(c, sec_top, quiz_rows, total_marks, max_total,
                               percentage, percentile, rank, total_students, grade):
    """Three-column performance dashboard: grade badge | gauge+stats | bar chart."""
    sx = MARGIN + INNER_PAD
    sw = CONTENT_W - 2 * INNER_PAD
    sh = 148
    sy = sec_top - sh

    _draw_shadow_rect(c, sx, sy, sw, sh, r=6)

    # Column widths
    col1_w = sw * 0.27
    col2_w = sw * 0.30
    col3_w = sw - col1_w - col2_w

    c1x = sx + col1_w / 2
    c2x = sx + col1_w + col2_w / 2
    c3x = sx + col1_w + col2_w

    # Vertical dividers
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.5)
    c.line(sx + col1_w, sy + 10, sx + col1_w, sy + sh - 10)
    c.line(sx + col1_w + col2_w, sy + 10, sx + col1_w + col2_w, sy + sh - 10)

    # --- Column 1: Grade Badge ---
    badge_cy = sy + sh / 2 + 4
    _draw_grade_badge(c, c1x, badge_cy, grade)

    # --- Column 2: Gauge + Stats ---
    gauge_cy = sy + sh - 52
    _draw_gauge(c, c2x, gauge_cy, 36, percentage)

    # Stats below gauge
    stats = [
        ("Total Marks", f"{total_marks} / {max_total}"),
        ("Percentile", f"{float(percentile):.2f}"),
        ("Rank", f"{rank} / {total_students}"),
    ]
    stat_y = gauge_cy - 32
    for label, value in stats:
        c.setFont(FONT_BOLD, 7.5)
        c.setFillColor(NAVY)
        c.drawString(c2x - 38, stat_y, label)
        c.setFont(FONT_REGULAR, 7.5)
        c.setFillColor(TEXT_DARK)
        c.drawRightString(c2x + 42, stat_y, value)
        stat_y -= 12

    # --- Column 3: Bar chart + message ---
    bars_x = c3x + 10
    bars_w = col3_w - 20
    bars_top = sy + sh - 18
    _draw_mini_bars(c, bars_x, bars_top, bars_w, quiz_rows, bar_h=10, gap=3)

    # Performance message below bars
    msg_y = sy + sh - 18 - len(quiz_rows) * 13 - 8
    c.setFont(FONT_ITALIC, 7)
    c.setFillColor(TEXT_GRAY)
    lines = _wrap_text(c, _performance_message(grade), FONT_ITALIC, 7, bars_w)
    for line in lines[:3]:
        c.drawString(bars_x, msg_y, line)
        msg_y -= 10

    return sy


def _draw_grading_scale(c, y):
    """Compact horizontal grading scale reference strip."""
    sx = MARGIN + INNER_PAD
    sw = CONTENT_W - 2 * INNER_PAD
    sh = 18

    c.setFillColor(GOLD_PALE)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.roundRect(sx, y - sh, sw, sh, 3, fill=1, stroke=1)

    c.setFont(FONT_BOLD, 7)
    c.setFillColor(NAVY)
    label_x = sx + 8
    c.drawString(label_x, y - 12, "Scale:")

    item_x = label_x + 30
    for grade_letter, range_str, gc in GRADING_SCALE:
        # Color swatch
        c.setFillColor(gc)
        c.rect(item_x, y - 11, 7, 7, fill=1, stroke=0)

        c.setFillColor(TEXT_DARK)
        c.setFont(FONT_BOLD, 7)
        c.drawString(item_x + 10, y - 12, grade_letter)
        c.setFont(FONT_REGULAR, 6.5)
        c.setFillColor(TEXT_GRAY)
        c.drawString(item_x + 24, y - 12, range_str)

        item_x += 68

    return y - sh


def _draw_footer(c, footer_top, enrollment_no, student_name, doc_hash):
    """QR code, verification info, and dual signature blocks."""
    fy = footer_top
    qr_size = 64
    qr_x = MARGIN + INNER_PAD + 6
    qr_y = fy - qr_size - 8

    # QR Code
    qr_data = (
        f"LIET-GRADECARD|Enrollment:{enrollment_no}|"
        f"Name:{student_name}|Hash:{doc_hash}"
    )
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B1D3A", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), qr_x, qr_y, width=qr_size, height=qr_size)

    # Verification text
    c.setFont(FONT_BOLD, 8)
    c.setFillColor(NAVY)
    c.drawString(qr_x, qr_y - 16, "Document Verification")
    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColor(TEXT_GRAY)
    c.drawString(qr_x, qr_y - 26, "Scan QR to verify authenticity")
    c.setFont(FONT_MONO, 6)
    c.setFillColor(TEXT_LIGHT)
    c.drawString(qr_x, qr_y - 36, f"Hash: {doc_hash}")

    # Signature blocks
    sign_block_w = 160
    sign_gap = 30
    sign_area_x = PAGE_W - MARGIN - INNER_PAD - 2 * sign_block_w - sign_gap
    sign_y_base = qr_y + 12

    signatories = [
        ("Head of Department", "(HOD)"),
        ("Controller of Examinations", "(CoE)"),
    ]

    for i, (title, abbrev) in enumerate(signatories):
        sx = sign_area_x + i * (sign_block_w + sign_gap)

        # Signature line
        c.setStrokeColor(TEXT_DARK)
        c.setLineWidth(0.7)
        c.line(sx, sign_y_base, sx + sign_block_w, sign_y_base)

        # Blank signature placeholder
        c.setFont(FONT_ITALIC, 10)
        c.setFillColor(TEXT_LIGHT)
        c.drawString(sx + 8, sign_y_base + 6, " ")

        # Title
        c.setFont(FONT_BOLD, 8)
        c.setFillColor(TEXT_DARK)
        c.drawString(sx, sign_y_base - 12, title)

        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(TEXT_GRAY)
        c.drawString(sx, sign_y_base - 22, abbrev)
        c.drawString(sx, sign_y_base - 31, "Lloyd Institute of Engineering")
        c.drawString(sx, sign_y_base - 40, "& Technology, Greater Noida")

    return fy - qr_size - 38


def _draw_bottom_bar(c):
    """Institutional footer bar with contact information."""
    bh = 20
    by = MARGIN + 3
    bx = MARGIN + INNER_PAD
    bw = CONTENT_W - 2 * INNER_PAD

    c.setFillColor(NAVY)
    c.roundRect(bx, by, bw, bh, 3, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont(FONT_REGULAR, 7)
    c.drawCentredString(PAGE_W / 2, by + 6,
                        "This is a computer-generated document and does not require a physical signature.  "
                        "|  Greater Noida, U.P.  |  www.liet.ac.in  |  Ph: 0120-XXXXXXX")

    return by


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_gradecards(df, output_dir="gradecards"):
    """Generate individual professional PDF grade cards for each student."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    created_files = []
    total_students = len(df)

    for idx, row in df.iterrows():
        # ── Extract student data ──────────────────────────────────────────
        student_name = _safe_value(row.get("Name", ""), "Student")
        student_email = _safe_value(row.get("Email", ""), "unknown")
        enrollment_no = _safe_value(
            row.get("Enrollment No.", ""),
            student_email.split("@")[0].upper(),
        )
        department = _safe_value(row.get("Department", ""), "Data Science")
        semester = _safe_value(row.get("Semester", ""), "6th Semester")
        roll_no = _safe_value(row.get("Roll No.", ""), enrollment_no or "2201234567")
        percentile = row.get("Percentile", 0)
        percentage = row.get("Percentage", 0)
        rank = row.get("Rank", "")
        grade = _safe_value(row.get("Grade", ""), "-")
        total_marks = row.get("Total_Marks", row.get("Total Marks", 0))
        if pd.isna(total_marks):
            total_marks = 0

        quiz_columns = _get_quiz_rows(row)
        quiz_rows = []
        for col in quiz_columns:
            score = row.get(col, 0)
            if pd.isna(score):
                score = 0
            quiz_rows.append((col.replace("Quiz", "Quiz "), float(score)))

        max_total = len(quiz_rows) * QUIZ_MAX_MARKS if quiz_rows else QUIZ_MAX_MARKS
        doc_number = _generate_doc_number(idx)
        doc_hash = _generate_hash(enrollment_no, total_marks, grade)

        # ── Build PDF ─────────────────────────────────────────────────────
        safe_name = re.sub(r"[^A-Za-z0-9]+", "_", student_name).strip("_") or "student"
        file_name = f"{safe_name}_{student_email.replace('@', '_').replace('.', '_')}.pdf"
        pdf_path = output_path / file_name

        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Border & watermark
        _draw_outer_border(c)
        _draw_watermark(c)

        # Header
        top_y = PAGE_H - MARGIN - 14
        y = _draw_header(c, top_y)

        # Title badge
        y = _draw_title_badge(c, y, doc_number)

        # Student info
        info_fields = [
            ("Name", student_name),
            ("Enrollment No.", enrollment_no),
            ("Department", department),
            ("Semester", semester),
            ("Roll No.", roll_no),
            ("Date of Issue", datetime.now().strftime("%d %B %Y")),
            ("Academic Year", "2024–25"),
        ]
        y = _draw_info_box(c, y, info_fields) - 10

        # Grades table
        y = _draw_grades_table(c, y, quiz_rows, grade) - 10

        # Performance section
        y = _draw_performance_section(
            c, y, quiz_rows, total_marks, max_total,
            percentage, percentile, rank, total_students, grade,
        ) - 6

        # Grading scale
        y = _draw_grading_scale(c, y) - 6

        # Footer
        y = _draw_footer(c, y, enrollment_no, student_name, doc_hash) - 4

        # Bottom bar
        _draw_bottom_bar(c)

        c.save()
        created_files.append(str(pdf_path))

    return created_files