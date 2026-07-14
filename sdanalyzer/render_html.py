"""HTML renderer: converts the Markdown deliverables into a styled,
self-contained executive report page (no external assets, no JS calls out).
"""

import html
import re

from . import render_md

CSS = """
:root { --ink:#1a2332; --sub:#5a6a7e; --line:#e3e8ef; --accent:#2456d6;
        --bg:#f7f9fc; --card:#ffffff; --good:#1a7f4e; --warn:#b7791f; --bad:#c53030; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       color: var(--ink); background: var(--bg); margin: 0; line-height: 1.55; }
.wrap { max-width: 960px; margin: 0 auto; padding: 32px 24px 64px; }
h1 { font-size: 1.7rem; border-bottom: 3px solid var(--accent); padding-bottom: 10px; }
h2 { font-size: 1.25rem; margin-top: 2.2em; color: var(--accent);
     border-bottom: 1px solid var(--line); padding-bottom: 6px; }
h3 { font-size: 1.02rem; margin-top: 1.4em; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 18px; background: var(--card);
        font-size: 0.9rem; }
th, td { border: 1px solid var(--line); padding: 7px 10px; text-align: left; }
th { background: #eef2f8; }
tr:nth-child(even) td { background: #fbfcfe; }
li { margin: 3px 0; }
code { background: #eef2f8; padding: 1px 5px; border-radius: 3px; font-size: 0.88em; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 0.78rem;
         font-weight: 600; }
.b-high { background: #e6f4ec; color: var(--good); }
.b-medium { background: #fdf3e0; color: var(--warn); }
.b-low { background: #fde8e8; color: var(--bad); }
.footer { margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--line);
          color: var(--sub); font-size: 0.85rem; font-style: italic; }
hr { border: none; border-top: 1px solid var(--line); margin: 28px 0; }
"""


def _md_to_html(md: str) -> str:
    """Small deterministic Markdown-to-HTML converter for our own output."""
    lines = md.split("\n")
    out, in_table, in_list, in_olist = [], False, False, False

    def close_lists():
        nonlocal in_list, in_olist
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_olist:
            out.append("</ol>")
            in_olist = False

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"_\[(High confidence)\]_", r'<span class="badge b-high">\1</span>', s)
        s = re.sub(r"_\[(Medium confidence)\]_", r'<span class="badge b-medium">\1</span>', s)
        s = re.sub(r"_\[(Low confidence)\]_", r'<span class="badge b-low">\1</span>', s)
        s = re.sub(r"_(.+?)_", r"<em>\1</em>", s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r"-{3,}", c) for c in cells):
                i += 1
                continue
            if not in_table:
                close_lists()
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            i += 1
            continue
        if in_table:
            out.append("</table>")
            in_table = False

        if stripped.startswith("### "):
            close_lists()
            out.append(f"<h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            close_lists()
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            close_lists()
            out.append(f"<h1>{inline(stripped[2:])}</h1>")
        elif stripped == "---":
            close_lists()
            out.append("<hr>")
        elif stripped.startswith("- "):
            if in_olist:
                out.append("</ol>")
                in_olist = False
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if in_list:
                out.append("</ul>")
                in_list = False
            if not in_olist:
                out.append("<ol>")
                in_olist = True
            item_text = re.sub(r"^\d+\.\s", "", stripped)
            out.append(f"<li>{inline(item_text)}</li>")
        elif stripped == "":
            close_lists()
        else:
            close_lists()
            out.append(f"<p>{inline(stripped)}</p>")
        i += 1
    if in_table:
        out.append("</table>")
    close_lists()
    return "\n".join(out)


def render(report: dict) -> str:
    md = render_md.render(report)
    body = _md_to_html(md)
    title = html.escape(f"Service Desk Intelligence - {report['meta']['source_name']}")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>{CSS}</style></head>"
        f"<body><div class='wrap'>{body}"
        "<div class='footer'>Generated by Service Desk Intelligence Analyzer. "
        "No LLM, no training, no data retention: the CSV was analyzed in memory and discarded."
        "</div></div></body></html>"
    )
