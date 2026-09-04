#!/usr/bin/env python3
"""runway_sim — Monte Carlo cash runway: not one number, a distribution.
Stdlib only. Simulates thousands of burn/revenue paths with volatility and growth,
reports P10/P50/P90 runway and death-by-month probabilities, and writes a real
.xlsx whose Assumptions cells are live (naive runway recalculates on edit).

  python3 runway_sim.py run out.xlsx --cash 2400000 --burn 210000 --burn-vol 0.12 \
      --revenue 60000 --rev-growth 0.05 --rev-vol 0.25
  python3 runway_sim.py run out.xlsx --config assumptions.json

Model (stated plainly): burn_t ~ Normal(burn, burn*burn_vol), clamped >= 0;
revenue_t = revenue * (1+g_t)^t with g_t ~ Normal(rev_growth, rev_growth_vol
approximated per-path); net burn floors at 0 when revenue exceeds burn.
Honest limits: normal noise (no fat tails), no seasonality, no fundraise events —
model the round separately. Deterministic with --seed.
"""
import argparse, json, random, sys
# ── xlsx writer (stdlib zip+XML — same approach as the excel-model skill) ─────
import zipfile
from xml.sax.saxutils import escape

def _col(i):
    s = ""
    while True:
        s = chr(65 + i % 26) + s
        i = i // 26 - 1
        if i < 0: return s

def write_xlsx(out, data):
    """data: {sheetName: [[cells...], ...]}. Numbers stay numbers; '=...' becomes a live formula."""
    sheets = list(data.items())
    strings, sidx = [], {}
    def sref(v):
        if v not in sidx: sidx[v] = len(strings); strings.append(v)
        return sidx[v]
    sheet_xmls = []
    for name, rows in sheets:
        cells = []
        for r, row in enumerate(rows, 1):
            cs = []
            for c, v in enumerate(row):
                ref = f"{_col(c)}{r}"
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    cs.append(f'<c r="{ref}"><v>{v}</v></c>')
                elif isinstance(v, str) and v.startswith("="):
                    cs.append(f'<c r="{ref}"><f>{escape(v[1:])}</f></c>')
                elif v is None or v == "":
                    continue
                else:
                    cs.append(f'<c r="{ref}" t="s"><v>{sref(str(v))}</v></c>')
            cells.append(f'<row r="{r}">{"".join(cs)}</row>')
        sheet_xmls.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(cells)}</sheetData></worksheet>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + "".join(f'<sheet name="{escape(n)}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i, (n, _) in enumerate(sheets))
        + '</sheets></workbook>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(sheets)))
        + f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>')
    shared = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        + "".join(f'<si><t xml:space="preserve">{escape(s)}</t></si>' for s in strings) + '</sst>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + "".join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
        + '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/sharedStrings.xml", shared)
        for i, x in enumerate(sheet_xmls):
            z.writestr(f"xl/worksheets/sheet{i+1}.xml", x)

def simulate(cash, burn, burn_vol, revenue, rev_growth, rev_vol, horizon, sims, seed):
    rng = random.Random(seed)
    deaths = []                      # month index the path ran out (horizon+1 = survived)
    for _ in range(sims):
        c = cash
        g = rng.gauss(rev_growth, rev_growth * rev_vol if rev_growth else rev_vol * 0.05)
        dead = horizon + 1
        for t in range(1, horizon + 1):
            b = max(0.0, rng.gauss(burn, burn * burn_vol))
            r = max(0.0, revenue * ((1 + g) ** t)) if revenue else 0.0
            c -= max(0.0, b - r)
            if c <= 0:
                dead = t
                break
        deaths.append(dead)
    return sorted(deaths)

def pct(sorted_vals, p):
    i = min(len(sorted_vals) - 1, max(0, int(p * len(sorted_vals))))
    return sorted_vals[i]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("out")
    r.add_argument("--config", help="JSON file with the flags below as keys (cash, burn, ...)")
    r.add_argument("--cash", type=float); r.add_argument("--burn", type=float)
    r.add_argument("--burn-vol", type=float, default=0.10)
    r.add_argument("--revenue", type=float, default=0.0)
    r.add_argument("--rev-growth", type=float, default=0.0)
    r.add_argument("--rev-vol", type=float, default=0.25)
    r.add_argument("--horizon", type=int, default=36)
    r.add_argument("--sims", type=int, default=5000)
    r.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    if a.config:
        cfg = json.load(open(a.config))
        for k, v in cfg.items(): setattr(a, k.replace("-", "_"), v)
    if not a.cash or not a.burn: sys.exit("need --cash and --burn (or a --config with them)")

    deaths = simulate(a.cash, a.burn, a.burn_vol, a.revenue, a.rev_growth, a.rev_vol, a.horizon, a.sims, a.seed)
    p10, p50, p90 = pct(deaths, 0.10), pct(deaths, 0.50), pct(deaths, 0.90)
    survived = sum(1 for d in deaths if d > a.horizon) / len(deaths)
    naive = a.cash / max(1e-9, a.burn - a.revenue) if a.burn > a.revenue else float("inf")

    # Death curve: % of paths out of cash by month t.
    curve = [["Month", "% of simulations out of cash by this month"]]
    for t in range(1, a.horizon + 1):
        curve.append([t, round(sum(1 for d in deaths if d <= t) / len(deaths), 4)])

    assumptions = [
        ["Runway Monte Carlo", ""],
        ["Cash today (EDIT ME)", a.cash],
        ["Monthly gross burn (EDIT ME)", a.burn],
        ["Monthly revenue (EDIT ME)", a.revenue],
        ["Burn volatility (σ/μ)", a.burn_vol],
        ["Revenue growth (monthly)", a.rev_growth],
        ["Naive runway, months (live formula)", "=B2/MAX(0.000001,B3-B4)"],
        ["", ""],
        ["Simulated (%d paths, seed %d)" % (a.sims, a.seed), ""],
        ["P10 (unlucky) runway", ("> %d" % a.horizon) if p10 > a.horizon else p10],
        ["P50 (median) runway", ("> %d" % a.horizon) if p50 > a.horizon else p50],
        ["P90 (lucky) runway", ("> %d" % a.horizon) if p90 > a.horizon else p90],
        ["Survive full horizon", round(survived, 3)],
        ["", ""],
        ["Read: raise while P10 > fundraise time (6-9 months), not P50.", ""],
    ]
    write_xlsx(a.out, {"Assumptions": assumptions, "Death curve": curve})
    naive_s = "inf" if naive == float("inf") else f"{naive:.1f}"
    fmt = lambda v: f">{a.horizon}" if v > a.horizon else str(v)
    print(f"wrote {a.out}: naive={naive_s}mo P10={fmt(p10)} P50={fmt(p50)} P90={fmt(p90)} survive({a.horizon}mo)={survived:.1%}")

if __name__ == "__main__":
    main()
