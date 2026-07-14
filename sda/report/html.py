"""Self-contained HTML report (inline CSS and inline SVG, no external calls)."""

from __future__ import annotations

import html as _h
from pathlib import Path

from . import charts

_CONF_COLOR = {"High": "#059669", "Medium": "#b45309", "Low": "#dc2626"}


def _badge(text, color):
    return (f"<span style='background:{color}1a;color:{color};border:1px solid {color}55;"
            f"border-radius:999px;padding:2px 9px;font-size:11px;font-weight:600'>{_h.escape(str(text))}</span>")


def _conf(c):
    return _badge(c, _CONF_COLOR.get(c, "#64748b"))


def write(a: dict, path) -> str:
    meta, dq, ex, opp = a["meta"], a["data_quality"], a["executive"], a["opportunities"]
    P: list[str] = []
    w = P.append

    w("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    w("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    w(f"<title>Service Desk Analysis: {_h.escape(meta['source_name'])}</title>")
    w("</head><body style='margin:0;background:#f1f5f9;padding:24px;"
      "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a'>")
    w("<div style='max-width:1000px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;"
      "border-radius:16px;padding:28px 32px'>")

    # Header
    w(f"<h1 style='margin:0 0 4px;font-size:24px'>Service Desk Analysis</h1>")
    w(f"<div style='color:#64748b;font-size:13px'>{_h.escape(meta['source_name'])} &middot; "
      f"generated {meta['generated_at']} &middot; {meta['tool']} v{meta['version']}</div>")
    w(f"<div style='background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;"
      f"padding:8px 12px;font-size:12px;color:#3730a3;margin-top:10px'>{_h.escape(meta['stateless_note'])}</div>")

    # A. Executive summary
    _section(w, "A. Executive summary")
    w("<ul style='font-size:14px;line-height:1.6'>")
    for line in ex["current_state_summary"]:
        w(f"<li>{_h.escape(line)}</li>")
    w("</ul>")
    w("<h3 style='font-size:13px;text-transform:uppercase;color:#475569'>Top findings</h3>")
    for f in ex["top_findings"]:
        w(f"<div style='margin:6px 0;font-size:14px'>{_conf(f['confidence'])} {_h.escape(f['finding'])}</div>")

    # Headline tiles
    roi = opp["roi_summary"]
    tiles = [("Tickets", dq["total_records"], "#4f46e5"),
             ("Data quality", f"{dq['quality_score']}/100 {dq['quality_grade']}", "#0891b2")]
    if a["mttr"].get("available"):
        tiles.append(("Median MTTR", f"{a['mttr']['overall']['median_hours']}h", "#b45309"))
    tiles.append(("Est. deflectable",
                  f"{roi['est_total_deflectable_pct_range'][0]}-{roi['est_total_deflectable_pct_range'][1]}%",
                  "#059669"))
    w("<div style='display:flex;gap:12px;flex-wrap:wrap;margin:14px 0'>")
    for label, val, color in tiles:
        w(f"<div style='flex:1;min-width:160px;border:1px solid #e2e8f0;border-top:4px solid {color};"
          f"border-radius:12px;padding:12px'><div style='font-size:12px;color:#64748b;"
          f"text-transform:uppercase'>{_h.escape(label)}</div>"
          f"<div style='font-size:24px;font-weight:800;color:{color}'>{_h.escape(str(val))}</div></div>")
    w("</div>")

    # B. Data quality
    _section(w, "B. Data quality assessment")
    w("<div style='font-size:13px;line-height:1.7'>")
    w(f"Detected fields: {_h.escape(', '.join(dq['fields_detected']) or 'none')}.<br>")
    w(f"<b>Missing fields:</b> {_h.escape(', '.join(dq['fields_missing']) or 'none')}.<br>")
    w(f"Duplicates: {dq['duplicate_records']} (by {_h.escape(dq['duplicate_basis'])}). ")
    if dq.get("date_range"):
        d = dq["date_range"]
        w(f"Date range: {d['start']} to {d['end']} ({d['days']} days). ")
    w(f"MTTR: {'available, ' + _h.escape(str(dq['mttr_source'])) if dq['mttr_available'] else 'not available'}.")
    if dq["quality_reasons"]:
        w("<br><span style='color:#64748b'>Deductions: " + _h.escape("; ".join(dq["quality_reasons"])) + "</span>")
    w("</div>")

    # C. Volume
    vol = a["volume"]
    _section(w, "C. Ticket volume analysis")
    if vol.get("by_month"):
        w("<div style='font-size:12px;color:#475569;margin-bottom:4px'>Tickets created by month</div>")
        w(charts.vbar([(r["month"], r["count"]) for r in vol["by_month"]]))
    cols = []
    for key, title in [("by_type", "By type"), ("by_priority", "By priority"), ("by_status", "By status")]:
        if key in vol:
            cells = "".join(f"<li>{_h.escape(r['value'])}: {r['count']} ({r['pct']}%)</li>"
                            for r in vol[key][:8])
            cols.append(f"<div style='flex:1;min-width:200px'><b style='font-size:12px'>{title}</b>"
                        f"<ul style='font-size:13px;margin:6px 0;padding-left:18px'>{cells}</ul></div>")
    if cols:
        w("<div style='display:flex;gap:16px;flex-wrap:wrap'>" + "".join(cols) + "</div>")

    # D. MTTR
    m = a["mttr"]
    _section(w, "D. MTTR analysis")
    if m.get("available"):
        o = m["overall"]
        w(f"<div style='font-size:13px'>Overall median {o['median_hours']}h, mean {o['mean_hours']}h, "
          f"p90 {o['p90_hours']}h (n={o['n']}).</div>")
        if m.get("by_theme"):
            w("<div style='font-size:12px;color:#475569;margin:8px 0 4px'>Median MTTR by theme (hours)</div>")
            w(charts.hbar([(r["value"], r["median_hours"]) for r in m["by_theme"]
                           if r["median_hours"] is not None][:12], unit="h"))
    else:
        w(f"<div style='font-size:13px;color:#64748b'>{_h.escape(m.get('note', 'Not available.'))}</div>")

    # E. Themes
    _section(w, "E. Theme and category breakdown")
    w(charts.hbar([(t["theme"], t["count"]) for t in a["themes"][:12]]))
    w(_table(["Theme", "Count", "%", "MTTR med (h)", "Confidence"],
             [[t["theme"], t["count"], t["pct"],
               t["mttr_median_hours"] if t["mttr_median_hours"] is not None else "-",
               t["confidence"]] for t in a["themes"]]))

    # F. Applications
    al = a["application_landscape"]
    _section(w, "F. Application landscape")
    if al and al.get("available"):
        w(f"<div style='font-size:13px;margin-bottom:6px'>{al['distinct_applications']} distinct applications.</div>")
        w(charts.hbar([(r["application"], r["count"]) for r in al["top"][:12]]))
    else:
        w("<div style='font-size:13px;color:#64748b'>No application/CI field detected.</div>")

    # G. Friction
    _section(w, "G. Top operational friction points")
    w(_table(["Area", "Tickets", "MTTR med (h)", "Est. effort (h)"],
             [[fp["area"], fp["count"], fp["mttr_median_hours"], fp["est_effort_hours"]]
              for fp in ex["friction_points"]]))

    # H. Automation backlog
    _section(w, "H. AI automation opportunity backlog")
    rows = []
    for b in opp["backlog"]:
        rng = b["est_deflectable_tickets_range"]
        rows.append([b["theme"], b["primary_type"], b["tickets_addressable"],
                     f"{rng[0]}-{rng[1]} ({b['deflection_range_pct'][0]}-{b['deflection_range_pct'][1]}%)",
                     b["mttr_reduction_potential"], b["implementation_complexity"],
                     b["risk_level"], b["confidence"]])
    w(_table(["Theme", "Type", "Addressable", "Est. deflectable", "MTTR", "Complexity", "Risk", "Conf."], rows))
    w(f"<div style='background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:10px 14px;"
      f"font-size:13px;margin-top:8px'><b>ROI (planning estimate):</b> "
      f"{roi['est_total_deflectable_range'][0]}-{roi['est_total_deflectable_range'][1]} tickets "
      f"({roi['est_total_deflectable_pct_range'][0]}-{roi['est_total_deflectable_pct_range'][1]}% of total). "
      f"Ranges, not commitments.</div>")

    # I. Agentic
    _section(w, "I. Agentic AI use case backlog")
    if opp["agentic_backlog"]:
        for g in opp["agentic_backlog"]:
            w(f"<div style='border:1px solid #e2e8f0;border-left:4px solid #7c3aed;border-radius:10px;"
              f"padding:12px 14px;margin:8px 0'><b>{_h.escape(g['theme'])}</b> "
              f"({g['tickets_addressable']} tickets) {_conf(g['confidence'])}"
              f"<div style='font-size:13px;margin-top:6px;line-height:1.6'>"
              f"<b>Trigger:</b> {_h.escape(str(g['trigger']))}<br>"
              f"<b>System of action:</b> {_h.escape(str(g['system_of_action']))}<br>"
              f"<b>Permissions:</b> {_h.escape(str(g['required_permissions']))}<br>"
              f"<b>Steps:</b> {_h.escape(', '.join(g['workflow_steps']))}<br>"
              f"<b>Feasibility:</b> {_h.escape(str(g['automation_feasibility']))} &middot; "
              f"<b>Risk:</b> {_h.escape(str(g['risk_level']))}<br>"
              f"<b>Human approval:</b> {_h.escape(str(g['human_approval_required']))} &middot; "
              f"<b>Fallback:</b> {_h.escape(str(g['fallback_path']))}<br>"
              f"<b>Expected impact:</b> {_h.escape(str(g['expected_impact']))}</div></div>")
    else:
        w("<div style='font-size:13px;color:#64748b'>No agentic use cases met the volume threshold.</div>")

    # J. Solution mapping
    _section(w, "J. Atomicwork solution mapping")
    w(_table(["Theme", "Tickets", "Primary type", "Capabilities"],
             [[s["theme"], s["tickets"], s["primary_type"], ", ".join(s["capabilities"])]
              for s in opp["solution_map"] if s["capabilities"]]))

    # K. Roadmap
    _section(w, "K. 30-60-90 day roadmap")
    w("<div style='display:flex;gap:12px;flex-wrap:wrap'>")
    for key, title in [("days_0_30", "Days 0-30"), ("days_30_60", "Days 30-60"), ("days_60_90", "Days 60-90")]:
        r = ex["roadmap_30_60_90"][key]
        acts = "".join(f"<li>{_h.escape(x)}</li>" for x in r["actions"])
        themes = _h.escape(", ".join(r["themes"])) if r["themes"] else "-"
        w(f"<div style='flex:1;min-width:220px;border:1px solid #e2e8f0;border-radius:12px;padding:12px'>"
          f"<b>{title}</b><div style='font-size:12px;color:#4f46e5;margin:4px 0'>{_h.escape(r['focus'])}</div>"
          f"<div style='font-size:12px;color:#64748b'>Themes: {themes}</div>"
          f"<ul style='font-size:13px;margin:6px 0;padding-left:18px'>{acts}</ul></div>")
    w("</div>")

    # L. Workshop questions
    _section(w, "L. Workshop questions for customer")
    w("<ul style='font-size:14px;line-height:1.6'>")
    for q in ex["workshop_questions"]:
        w(f"<li>{_h.escape(q)}</li>")
    w("</ul>")

    # N. Recommendations
    _section(w, "N. Final recommendations")
    w("<ul style='font-size:14px;line-height:1.6'>")
    for rec in ex["final_recommendations"]:
        w(f"<li>{_h.escape(rec)}</li>")
    w("</ul>")
    w("<div style='font-size:12px;color:#475569;margin-top:10px'><b>Assumptions:</b><ul>")
    for asm in roi["assumptions"]:
        w(f"<li>{_h.escape(asm)}</li>")
    for risk in ex["risks_and_assumptions"]:
        w(f"<li>{_h.escape(risk)}</li>")
    w("</ul></div>")

    # O-S. Implementation and UAT package
    impl = a.get("implementation")
    if impl:
        tp = impl["test_plan"]
        _section(w, "O. UAT test plan")
        w(f"<div style='font-size:13px;color:#475569;margin-bottom:6px'>{_h.escape(tp['coverage_note'])}</div>")
        w(f"<div style='font-size:13px;margin-bottom:8px'><b>{tp['total_cases']} cases:</b> "
          f"{_badge('Must ' + str(tp['must_count']), '#dc2626')} "
          f"{_badge('Should ' + str(tp['should_count']), '#b45309')} "
          f"{_badge('Could ' + str(tp['could_count']), '#059669')}</div>")
        for c in tp["cases"]:
            gate_color = {"Must": "#dc2626", "Should": "#b45309", "Could": "#059669"}.get(c["priority"], "#64748b")
            steps = "".join(f"<li>{_h.escape(s)}</li>" for s in c["steps"])
            w(f"<div style='border:1px solid #e2e8f0;border-left:4px solid {gate_color};border-radius:10px;"
              f"padding:10px 14px;margin:8px 0'><b>{_h.escape(c['id'])}: {_h.escape(c['title'])}</b> "
              f"{_badge(c['priority'], gate_color)}"
              f"<div style='font-size:12px;color:#64748b;margin:2px 0'>Area: {_h.escape(c['area'])} &middot; "
              f"Role: {_h.escape(c['role'])} &middot; Derived from: {_h.escape(c['source'])}</div>"
              f"<ol style='font-size:13px;margin:6px 0;padding-left:20px'>{steps}</ol>"
              f"<div style='font-size:13px'><b>Expected:</b> {_h.escape(c['expected'])}</div></div>")

        _section(w, "P. Role and permission test matrix")
        w(_table(["Role", "Can", "Cannot", "Derived from"],
                 [[r["role"], "; ".join(r["can"]), "; ".join(r["cannot"]), r["derived_from"]]
                  for r in impl["role_matrix"]]))

        _section(w, "Q. Implementation RACI")
        w(_table(["Activity", "Responsible", "Accountable", "Consulted", "Informed"],
                 [[r["activity"], r["responsible"], r["accountable"], r["consulted"], r["informed"]]
                  for r in impl["raci"]]))

        _section(w, "R. Go-live readiness checklist")
        w(_table(["Gate", "Category", "Item", "Derived from"],
                 [[r["gate"], r["category"], r["item"], r["source"]]
                  for r in impl["readiness_checklist"]]))

        _section(w, "S. 15-day testing phase plan")
        w("<div style='display:flex;gap:12px;flex-wrap:wrap'>")
        for ph in impl["phase_plan_15_day"]:
            acts = "".join(f"<li>{_h.escape(x)}</li>" for x in ph["activities"])
            w(f"<div style='flex:1;min-width:280px;border:1px solid #e2e8f0;border-radius:12px;padding:12px'>"
              f"<b>Days {_h.escape(ph['days'])}</b>"
              f"<div style='font-size:12px;color:#4f46e5;margin:4px 0'>{_h.escape(ph['phase'])}</div>"
              f"<ul style='font-size:13px;margin:6px 0;padding-left:18px'>{acts}</ul>"
              f"<div style='font-size:12px;color:#059669'><b>Exit:</b> {_h.escape(ph['exit_criteria'])}</div></div>")
        w("</div>")
        w("<div style='background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:10px 14px;"
          "font-size:13px;margin-top:10px'><b>Testing assumptions:</b><ul style='margin:6px 0;padding-left:18px'>")
        for asm in impl["assumptions"]:
            w(f"<li>{_h.escape(asm)}</li>")
        w("</ul></div>")

    w(f"<div style='color:#94a3b8;font-size:11px;margin-top:16px;border-top:1px solid #e2e8f0;"
      f"padding-top:10px'>Deterministic analysis. No model, no training, no data retained. "
      f"All figures traceable to the input; deflection figures are planning ranges to validate with SMEs.</div>")
    w("</div></body></html>")

    Path(path).write_text("".join(P), encoding="utf-8")
    return str(path)


def _section(w, title):
    w(f"<h2 style='font-size:16px;margin:26px 0 8px;padding-top:14px;border-top:1px solid #e2e8f0'>"
      f"{_h.escape(title)}</h2>")


def _table(headers, rows):
    if not rows:
        return "<div style='font-size:13px;color:#64748b'>No data.</div>"
    th = "".join(f"<th style='text-align:left;padding:7px 8px'>{_h.escape(str(x))}</th>" for x in headers)
    body = []
    for r in rows:
        tds = "".join(f"<td style='padding:7px 8px;border-top:1px solid #eef2f7'>"
                      f"{_conf(str(c)) if str(c) in _CONF_COLOR else _h.escape(str(c))}</td>" for c in r)
        body.append(f"<tr>{tds}</tr>")
    return (f"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
            f"<tr style='background:#f1f5f9'>{th}</tr>{''.join(body)}</table>")
