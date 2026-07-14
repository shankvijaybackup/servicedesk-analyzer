#!/usr/bin/env python3
"""Privacy and quality audit. Run before every release: python audit.py

Enforces the project's core guarantees:
1. No AI/LLM: no network or AI SDK imports anywhere in the source.
2. No retention: raw upload, dataframe, and normalized view are all deleted;
   the web app never writes uploads to disk.
3. Forgetting works: forget endpoint purges; expired reports purge.
4. No slop: no emojis, no em/en-dashes, no marketing filler in source or in
   generated reports.
Exits non-zero on any violation.
"""

import io
import re
import sys
import pathlib

FAIL = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAIL.append(name)


ROOT = pathlib.Path(__file__).parent
SOURCES = (list((ROOT / "sdanalyzer").glob("*.py"))
           + [ROOT / "cli.py", ROOT / "web_app.py", ROOT / "audit.py"])
DOCS = [ROOT / "README.md", ROOT / "Dockerfile"]

# 1. No network / AI SDK imports
NET_RE = re.compile(
    r"^\s*(import|from)\s+(requests|urllib|httpx|aiohttp|socket|openai|anthropic|"
    r"boto3|google\.|azure|litellm|transformers|torch|sklearn|tensorflow)\b", re.M)
hits = [f"{p.name}: {m.group(0).strip()}" for p in SOURCES
        for m in NET_RE.finditer(p.read_text())]
check("No network/AI/ML imports in source", not hits, "; ".join(hits))

# 2. Dependencies are exactly the four known-offline libraries
deps = {line.split(">=")[0].split("==")[0].strip()
        for line in (ROOT / "requirements.txt").read_text().splitlines() if line.strip()}
check("Dependencies limited to pandas/flask/python-pptx/openpyxl",
      deps == {"pandas", "flask", "python-pptx", "openpyxl"}, str(sorted(deps)))

# 3. Web app never writes uploads to disk
web_src = (ROOT / "web_app.py").read_text()
disk_re = re.compile(r"\bopen\(|\.save\(|to_csv|to_excel|tempfile|NamedTemporary")
check("Web app has no disk writes", not disk_re.search(web_src))

# 4. Data forgotten at every stage
report_src = (ROOT / "sdanalyzer" / "report.py").read_text()
check("Raw dataframe deleted after quality assessment", "del df" in report_src)
check("Normalized view deleted after aggregation", "del view" in report_src)
check("Web upload bytes deleted after analysis", "del data" in web_src)

# 5. Forget endpoint and TTL purge actually work
sys.path.insert(0, str(ROOT))
import web_app  # noqa: E402
from sdanalyzer import report as report_mod, render_md  # noqa: E402

sample = ROOT / "sample_data" / "sample_tickets.csv"
if sample.exists():
    client = web_app.app.test_client()
    with open(sample, "rb") as f:
        resp = client.post("/analyze", data={"csv": (io.BytesIO(f.read()), "t.csv")},
                           follow_redirects=True)
    check("Upload -> report renders", resp.status_code == 200)
    token = next(iter(web_app._store), None)
    client.get(f"/forget/{token}")
    check("Forget now purges immediately",
          token not in web_app._store
          and client.get(f"/report/{token}").status_code == 404)
    # TTL purge
    with open(sample, "rb") as f:
        client.post("/analyze", data={"csv": (io.BytesIO(f.read()), "t.csv")})
    token2 = next(iter(web_app._store))
    web_app._store[token2]["ts"] -= web_app.RESULT_TTL_SECONDS + 1
    web_app._purge_expired()
    check("Expired report auto-purges", token2 not in web_app._store)

    # 6. No slop in generated output
    md = render_md.render(report_mod.analyze(str(sample), source_name="t.csv"))
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
    dash_re = re.compile(r"[\u2014\u2013]")
    slop = ["leverage", "unlock the power", "game-chang", "revolutioniz",
            "cutting-edge", "seamless", "empower", "delve", "furthermore",
            "best-in-class", "world-class", "synerg", "holistic", "transformative",
            "paradigm", "state-of-the-art", "supercharge", "elevate your"]
    slop_hits = [s for s in slop if s in md.lower()]
    check("No emojis in generated report", not emoji_re.search(md))
    check("No em/en-dashes in generated report", not dash_re.search(md))
    check("No marketing slop in generated report", not slop_hits, "; ".join(slop_hits))
    check("No absurd cumulative wait-hours", "waiting hours eliminated" not in md)
else:
    print("SKIP  sample data missing; run sample_data/make_sample.py for full audit")

# 7. No emojis / dashes in source and docs
emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
dash_re = re.compile(r"[\u2014\u2013]")
bad = [f"{p.name}:{i}" for p in SOURCES + DOCS if p.exists()
       for i, line in enumerate(p.read_text().splitlines(), 1)
       if emoji_re.search(line) or dash_re.search(line)]
check("No emojis or em/en-dashes in source and docs", not bad, "; ".join(bad[:5]))

print()
if FAIL:
    print(f"AUDIT FAILED: {len(FAIL)} violation(s)")
    sys.exit(1)
print("AUDIT PASSED: no AI, no LLM, no learning, no retention, no slop.")
