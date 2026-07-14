"""Tiny self-contained SVG chart helpers (no external chart library).

Deterministic: identical input renders identical SVG. Used to keep the HTML
report fully self-contained with no CDN or JS dependency.
"""

from __future__ import annotations

import html

_PALETTE = ["#4f46e5", "#0891b2", "#059669", "#b45309", "#dc2626", "#7c3aed",
            "#0d9488", "#ca8a04", "#be123c", "#2563eb", "#65a30d", "#9333ea",
            "#c2410c", "#0f766e"]


def hbar(items: list[tuple[str, float]], *, width: int = 640, unit: str = "") -> str:
    """Horizontal bar chart from (label, value) pairs."""
    if not items:
        return "<p style='color:#64748b'>No data.</p>"
    row_h, gap, label_w, pad = 26, 8, 180, 8
    maxv = max(v for _, v in items) or 1
    bar_w = width - label_w - 80
    height = pad * 2 + len(items) * (row_h + gap)
    parts = [f"<svg viewBox='0 0 {width} {height}' width='100%' role='img' "
             f"style='max-width:{width}px;font-family:inherit'>"]
    y = pad
    for i, (label, value) in enumerate(items):
        color = _PALETTE[i % len(_PALETTE)]
        w = int(bar_w * (value / maxv)) if maxv else 0
        lbl = html.escape(str(label)[:34])
        val = f"{value:g}{unit}"
        parts.append(f"<text x='{label_w-6}' y='{y+row_h*0.7}' text-anchor='end' "
                     f"font-size='12' fill='#334155'>{lbl}</text>")
        parts.append(f"<rect x='{label_w}' y='{y}' width='{w}' height='{row_h}' "
                     f"rx='4' fill='{color}'></rect>")
        parts.append(f"<text x='{label_w+w+6}' y='{y+row_h*0.7}' font-size='12' "
                     f"fill='#64748b'>{val}</text>")
        y += row_h + gap
    parts.append("</svg>")
    return "".join(parts)


def vbar(items: list[tuple[str, float]], *, width: int = 640, height: int = 220,
         unit: str = "") -> str:
    """Vertical bar chart, good for a time series."""
    if not items:
        return "<p style='color:#64748b'>No data.</p>"
    pad_b, pad_t, pad_l = 40, 10, 10
    n = len(items)
    maxv = max(v for _, v in items) or 1
    slot = (width - pad_l) / n
    bw = max(4, slot * 0.7)
    parts = [f"<svg viewBox='0 0 {width} {height}' width='100%' role='img' "
             f"style='max-width:{width}px;font-family:inherit'>"]
    plot_h = height - pad_b - pad_t
    for i, (label, value) in enumerate(items):
        h = int(plot_h * (value / maxv)) if maxv else 0
        x = pad_l + i * slot + (slot - bw) / 2
        yv = pad_t + (plot_h - h)
        parts.append(f"<rect x='{x:.1f}' y='{yv}' width='{bw:.1f}' height='{h}' "
                     f"rx='3' fill='#4f46e5'></rect>")
        show = html.escape(str(label)[-7:])
        parts.append(f"<text x='{x+bw/2:.1f}' y='{height-pad_b+14}' text-anchor='middle' "
                     f"font-size='10' fill='#64748b' transform='rotate(0 {x+bw/2:.1f} "
                     f"{height-pad_b+14})'>{show}</text>")
    parts.append(f"<text x='{pad_l}' y='{pad_t+8}' font-size='10' fill='#94a3b8'>peak "
                 f"{maxv:g}{unit}</text>")
    parts.append("</svg>")
    return "".join(parts)
