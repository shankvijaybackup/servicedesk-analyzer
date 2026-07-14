#!/usr/bin/env python3
"""Flask web app: upload CSV/XLSX -> view report -> download formats -> forget.

Privacy model:
- Uploaded file is read into memory and never written to disk.
- The generated report (aggregates only, no raw rows) is kept in an
  in-memory store for RESULT_TTL_SECONDS so the user can download formats,
  then purged. A "Forget now" button purges immediately.
- No LLM, no external calls, no persistence, no logs of ticket content.
"""

import os
import secrets
import threading
import time

from flask import Flask, request, render_template_string, abort, Response, redirect, url_for

from sdanalyzer import report as report_mod
from sdanalyzer import render_md, render_html, render_pptx

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

RESULT_TTL_SECONDS = 1800  # 30 minutes
_store: dict[str, dict] = {}
_lock = threading.Lock()


def _purge_expired():
    now = time.time()
    with _lock:
        for k in [k for k, v in _store.items() if now - v["ts"] > RESULT_TTL_SECONDS]:
            del _store[k]


def _put(rep: dict) -> str:
    _purge_expired()
    token = secrets.token_urlsafe(16)
    with _lock:
        _store[token] = {"report": rep, "ts": time.time()}
    return token


def _get(token: str) -> dict | None:
    _purge_expired()
    with _lock:
        entry = _store.get(token)
    return entry["report"] if entry else None


UPLOAD_PAGE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Service Desk Intelligence Analyzer</title>
<style>
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; background:#f7f9fc;
       color:#1a2332; display:flex; justify-content:center; padding-top:8vh; margin:0; }
.card { background:#fff; border:1px solid #e3e8ef; border-radius:10px; padding:36px 40px;
        max-width:560px; box-shadow:0 2px 10px rgba(20,40,80,.06); }
h1 { font-size:1.4rem; color:#2456d6; margin-top:0; }
p { color:#5a6a7e; font-size:.93rem; }
ul { color:#5a6a7e; font-size:.88rem; padding-left:20px; }
input[type=file] { margin:18px 0; display:block; }
button { background:#2456d6; color:#fff; border:none; border-radius:6px;
         padding:10px 22px; font-size:.95rem; cursor:pointer; }
button:hover { background:#1c45ad; }
.err { color:#c53030; font-size:.9rem; }
</style></head><body><div class="card">
<h1>Service Desk Intelligence Analyzer</h1>
<p>Upload a service desk CSV or Excel export (ServiceNow, Jira SM, Freshservice, Zendesk,
ManageEngine, Atomicwork). Get an executive-ready operational analysis.</p>
<ul>
<li>No AI training. No LLM. Deterministic rule-based analytics.</li>
<li>Your file is processed in memory and never written to disk.</li>
<li>Results auto-purge after 30 minutes, or immediately via "Forget now".</li>
</ul>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<form method="post" action="/analyze" enctype="multipart/form-data">
<input type="file" name="csv" accept=".csv,.xlsx,.xlsm,.xls" required>
<button type="submit">Analyze</button>
</form></div></body></html>
"""

RESULT_BAR = """
<div style="position:sticky;top:0;background:#1a2332;color:#fff;padding:10px 24px;
     font-family:-apple-system,'Segoe UI',Roboto,sans-serif;font-size:.9rem;display:flex;
     gap:16px;align-items:center;flex-wrap:wrap;z-index:10">
<span>Report ready. Data auto-purges in 30 min.</span>
<a style="color:#9db8f0" href="/download/{{t}}/md">Markdown</a>
<a style="color:#9db8f0" href="/download/{{t}}/html">HTML</a>
<a style="color:#9db8f0" href="/download/{{t}}/pptx">PPTX</a>
<a style="color:#9db8f0" href="/download/{{t}}/ppt-outline">Slide outline</a>
<a style="color:#f0a3a3" href="/forget/{{t}}">Forget now</a>
<a style="color:#9db8f0" href="/">New analysis</a>
</div>
"""


@app.get("/")
def index():
    return render_template_string(UPLOAD_PAGE, error=None)


@app.get("/health")
def health():
    return {"status": "ok", "reports_in_memory": len(_store)}


@app.post("/analyze")
def analyze():
    f = request.files.get("csv")
    if f is None or f.filename == "":
        return render_template_string(UPLOAD_PAGE, error="Please choose a CSV or Excel file."), 400
    data = f.read()  # in-memory only
    try:
        rep = report_mod.analyze(data, source_name=f.filename)
    except Exception as e:
        return render_template_string(
            UPLOAD_PAGE, error=f"Could not analyze this file: {e}"), 400
    finally:
        del data  # forget raw upload
    token = _put(rep)
    return redirect(url_for("view_report", token=token))


@app.get("/report/<token>")
def view_report(token):
    rep = _get(token)
    if rep is None:
        return render_template_string(
            UPLOAD_PAGE, error="Report expired or forgotten. Upload again."), 404
    page = render_html.render(rep)
    bar = render_template_string(RESULT_BAR, t=token)
    return page.replace("<body>", "<body>" + bar, 1)


@app.get("/download/<token>/<fmt>")
def download(token, fmt):
    rep = _get(token)
    if rep is None:
        abort(404)
    base = rep["meta"]["source_name"].rsplit(".", 1)[0] + "_report"
    if fmt == "md":
        return Response(render_md.render(rep), mimetype="text/markdown",
                        headers={"Content-Disposition": f"attachment; filename={base}.md"})
    if fmt == "html":
        return Response(render_html.render(rep), mimetype="text/html",
                        headers={"Content-Disposition": f"attachment; filename={base}.html"})
    if fmt == "pptx":
        return Response(render_pptx.render(rep),
                        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        headers={"Content-Disposition": f"attachment; filename={base}.pptx"})
    if fmt == "ppt-outline":
        lines = []
        for i, s in enumerate(rep["slides"], 1):
            lines.append(f"Slide {i}: {s['title']}")
            lines += [f"  - {b}" for b in s["bullets"]]
            lines.append("")
        return Response("\n".join(lines), mimetype="text/plain",
                        headers={"Content-Disposition": f"attachment; filename={base}_slides.txt"})
    abort(404)


@app.get("/forget/<token>")
def forget(token):
    with _lock:
        _store.pop(token, None)
    return render_template_string(UPLOAD_PAGE, error=None)


if __name__ == "__main__":
    # HOST=0.0.0.0 to expose beyond localhost (e.g. in a container). Default stays local.
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5080")),
            debug=False)
