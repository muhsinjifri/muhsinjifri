"""Generate every profile README card (light + dark) in one visual system.

usage: python3 cards.py <icons_dir> <img_dir> <out_dir>

GitHub shows README images as plain <img>, so nothing here can react to the mouse.
All motion is CSS / SMIL that plays on its own. Rules followed throughout:
  * the un-animated state is the finished state, so a card never gets stuck half-drawn
  * one gentle motion per card, staggered so the page never moves all at once
  * prefers-reduced-motion switches CSS motion off
"""
import base64, math, os, re, sys
from xml.sax.saxutils import escape as esc

ICONS, IMG, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(name="dark", bg="#0d1117", bar="#161b22", tile="#161b22", border="#30363d", text="#e6edf3",
                 muted="#7d8590", prompt="#3fb950", accent="#58a6ff", accent_soft="#388bfd26",
                 ok="#3fb950", warn="#d29922", chip="#21262d", glint="#ffffff",
                 sea1="#1f6feb2e", sea2="#388bfd4d", hull="#6e7681", cabin="#8b949e", cloud="#21262d",
                 boxes=["#58a6ff", "#3fb950", "#f0883e", "#a371f7", "#db61a2", "#d29922"]),
    "light": dict(name="light", bg="#ffffff", bar="#f6f8fa", tile="#f6f8fa", border="#d0d7de", text="#1f2328",
                  muted="#656d76", prompt="#1a7f37", accent="#0969da", accent_soft="#0969da1a",
                  ok="#1a7f37", warn="#9a6700", chip="#eaeef2", glint="#ffffff",
                  sea1="#0969da1f", sea2="#0969da38", hull="#424a53", cabin="#6e7781", cloud="#eaeef2",
                  boxes=["#0969da", "#1a7f37", "#bc4c00", "#8250df", "#bf3989", "#9a6700"]),
}


# ---------------------------------------------------------------- helpers
def icon_d(name):
    return re.search(r'd="([^"]+)"', open(f"{ICONS}/{name}.svg").read()).group(1)


def icon(name, x, y, size, fill):
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path fill="{fill}" d="{icon_d(name)}"/></svg>')


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def style(extra=""):
    return f"""<style>
  .m {{ font-family: {MONO}; }}
  .s {{ font-family: {SANS}; }}
  {extra}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>"""


def svg_open(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}">')


def pane(w, h, c, cmd, body, css="", label=None, dashed=False, aria=""):
    """A card whose terminal-style title bar shows the command that 'printed' it."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lab = (f'<text x="{w-20}" y="25" text-anchor="end" class="m" font-size="12" fill="{c["muted"]}">{label}</text>'
           if label else "")
    head = (f'<path d="M0.5 40 V12.5 a12 12 0 0 1 12 -12 H{w-12.5} a12 12 0 0 1 12 12 V40 Z" fill="{c["bar"]}"/>'
            f'<line x1="0.5" y1="40" x2="{w-0.5}" y2="40" stroke="{c["border"]}"/>'
            f'<text x="20" y="25" class="m" font-size="13"><tspan fill="{c["prompt"]}">$</tspan>'
            f'<tspan fill="{c["text"]}"> {esc(cmd)}</tspan></text>{lab}') if cmd else ""
    return (f'{svg_open(w, h, aria or cmd)}{style(css)}'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{c["bg"]}" stroke="{c["border"]}"{dash}/>'
            f'{head}{body}</svg>\n')


def chips(items, x, y, c, size=11):
    out, cx = [], x
    for it in items:
        wdt = len(it) * size * 0.62 + 18
        out.append(f'<rect x="{cx}" y="{y}" width="{wdt:.0f}" height="24" rx="12" fill="{c["chip"]}"/>'
                   f'<text x="{cx + wdt/2:.0f}" y="{y+16}" text-anchor="middle" class="m" font-size="{size}" fill="{c["muted"]}">{esc(it)}</text>')
        cx += wdt + 8
    return "".join(out)


def lines(txt_lines, x, y, lh, c, size=15, color="text", cls="s", weight=None, anchor=None):
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return "".join(f'<text x="{x}" y="{y + i*lh}" class="{cls}" font-size="{size}" fill="{c[color]}"{w}{a}>{esc(t)}</text>'
                   for i, t in enumerate(txt_lines))


# ---------------------------------------------------------------- header: the command types itself, output prints
def header(c):
    W, H = 880, 352
    kx, vx, y_cmd = 40, 190, 84
    cmd = "kubectl describe engineer muhsin"
    cw, t0, per = 9.63, 0.6, 0.045            # char advance, typing start, seconds per char
    n = len(cmd)
    t_done = t0 + n * per
    total = t_done + 0.2
    times = [0, t0] + [t0 + (k + 1) * per for k in range(n)] + [total]
    widths = [0, 0] + [(k + 1) * cw for k in range(n)] + [W]
    kt = ";".join(f"{t/total:.4f}" for t in times)
    vals = ";".join(f"{w:.1f}" for w in widths)
    xs = ";".join(f"{kx + 18 + min(w, n*cw):.1f}" for w in widths)
    rows = [
        ("Name", [("Sayed Muhsin Jifri", "text", True)]),
        ("Role", [("DevOps Engineer", "text", False), (" @ ", "muted", False), ("IQVIA", "text", False)]),
        ("Location", [("Bengaluru, India", "text", False)]),
        ("Focus", [("Kubernetes · GitOps · CI/CD · AWS · Terraform", "accent", False)]),
        ("Certified", [("AWS Solutions Architect Associate · Terraform Associate", "text", False)]),
        ("Next", [("CKA (in progress)", "text", False)]),
    ]
    out_start = t_done + 0.35
    css = (".ln { animation: show .35s ease-out backwards; }"
           "@keyframes show { from { opacity: 0; } }"
           f".cur {{ animation: blink 1.1s steps(1) infinite; }}"
           "@keyframes blink { 50% { opacity: 0; } }"
           ".ring { transform-box: fill-box; transform-origin: center; animation: ring 2.4s ease-out infinite; }"
           "@keyframes ring { from { transform: scale(1); opacity: .55; } to { transform: scale(3.2); opacity: 0; } }")
    b = [f'<path d="M0.5 44 V12.5 a12 12 0 0 1 12 -12 H{W-12.5} a12 12 0 0 1 12 12 V44 Z" fill="{c["bar"]}"/>',
         f'<line x1="0.5" y1="44" x2="{W-0.5}" y2="44" stroke="{c["border"]}"/>',
         '<circle cx="24" cy="22" r="6" fill="#ff5f57"/><circle cx="44" cy="22" r="6" fill="#febc2e"/><circle cx="64" cy="22" r="6" fill="#28c840"/>',
         f'<text x="{W/2}" y="27" text-anchor="middle" class="m" font-size="13" fill="{c["muted"]}">muhsin@bengaluru: ~</text>',
         f'<clipPath id="typed"><rect x="{kx+18}" y="{y_cmd-18}" width="{W}" height="26">'
         f'<animate attributeName="width" dur="{total:.2f}s" fill="freeze" calcMode="discrete" keyTimes="{kt}" values="{vals}"/></rect></clipPath>',
         f'<text x="{kx}" y="{y_cmd}" class="m" font-size="16" fill="{c["prompt"]}">$</text>',
         f'<text x="{kx+18}" y="{y_cmd}" class="m" font-size="16" fill="{c["text"]}" clip-path="url(#typed)">{cmd}</text>',
         # the cursor rides along while typing, then hides
         f'<rect x="{kx+18}" y="{y_cmd-14}" width="9" height="18" fill="{c["text"]}" opacity="0">'
         f'<animate attributeName="x" dur="{total:.2f}s" fill="freeze" calcMode="discrete" keyTimes="{kt}" values="{xs}"/>'
         f'<animate attributeName="opacity" dur="{out_start:.2f}s" fill="freeze" calcMode="discrete" keyTimes="0;0.999" values="1;0"/></rect>']
    y = y_cmd + 34
    for i, (k, vals_) in enumerate(rows):
        d = out_start + i * 0.11
        tsp = "".join(f'<tspan fill="{c[col]}"{" font-weight=" + chr(34) + "700" + chr(34) if bold else ""}>{esc(v)}</tspan>'
                      for v, col, bold in vals_)
        b.append(f'<g class="ln" style="animation-delay:{d:.2f}s"><text x="{kx}" y="{y}" class="m" font-size="16" fill="{c["muted"]}">{k}:</text>'
                 f'<text x="{vx}" y="{y}" class="m" font-size="16" xml:space="preserve">{tsp}</text></g>')
        y += 30
    d = out_start + len(rows) * 0.11
    b.append(f'<g class="ln" style="animation-delay:{d:.2f}s"><text x="{kx}" y="{y}" class="m" font-size="16" fill="{c["muted"]}">Status:</text>'
             f'<circle class="ring" style="animation-delay:{d+0.4:.2f}s" cx="{vx+5}" cy="{y-5}" r="5" fill="{c["ok"]}" opacity="0"/>'
             f'<circle cx="{vx+5}" cy="{y-5}" r="5" fill="{c["ok"]}"/>'
             f'<text x="{vx+18}" y="{y}" class="m" font-size="16" fill="{c["ok"]}">Running</text>'
             f'<text x="{vx+92}" y="{y}" class="m" font-size="16" fill="{c["muted"]}">· open to new opportunities</text></g>')
    y += 36
    d += 0.25
    b.append(f'<g class="ln" style="animation-delay:{d:.2f}s"><text x="{kx}" y="{y}" class="m" font-size="16" fill="{c["prompt"]}">$</text>'
             f'<rect class="cur" x="{kx+18}" y="{y-14}" width="9" height="18" fill="{c["text"]}"/></g>')
    return (f'{svg_open(W, H, "kubectl describe engineer muhsin")}{style(css)}'
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{c["bg"]}" stroke="{c["border"]}"/>'
            + "".join(b) + "</svg>\n")


# ---------------------------------------------------------------- about: tiles light up in turn
def about(c):
    W, H = 880, 300
    cols = [
        ("01", "Ship", ["CI/CD and GitOps pipelines", "that take code from merge", "request to production."]),
        ("02", "Run", ["Containerized services on", "Kubernetes, with autoscaling", "and health probes."]),
        ("03", "Build", ["AWS infrastructure as", "Terraform: reproducible,", "reviewed and versioned."]),
        ("04", "Secure", ["Least-privilege IAM and", "no long-lived secrets", "inside workloads."]),
    ]
    period = 10
    css = (f".t {{ animation: glow {period}s ease-in-out infinite; }}"
           f"@keyframes glow {{ 0%, 26%, 100% {{ stroke: {c['border']}; }} 6%, 18% {{ stroke: {c['accent']}; }} }}"
           f".n {{ animation: num {period}s ease-in-out infinite; }}"
           f"@keyframes num {{ 0%, 26%, 100% {{ opacity: 1; }} 6%, 18% {{ opacity: .35; }} }}")
    b = [lines(["I'm a DevOps engineer. I get software from a merge request into production",
                "safely and repeatably, and keep it easy to see what's running."], 32, 82, 26, c, size=17)]
    cw, gap, x0, y0 = 196, 14, 32, 140
    for i, (n, title, body) in enumerate(cols):
        x = x0 + i * (cw + gap)
        d = 2 + i * period * 0.25
        b.append(f'<rect class="t" style="animation-delay:{d}s" x="{x}" y="{y0}" width="{cw}" height="132" rx="10" fill="{c["tile"]}" stroke="{c["border"]}"/>')
        b.append(f'<text x="{x+16}" y="{y0+30}" class="m" font-size="12" fill="{c["accent"]}">{n}</text>')
        b.append(f'<text x="{x+42}" y="{y0+30}" class="s" font-size="16" font-weight="600" fill="{c["text"]}">{title}</text>')
        b.append(lines(body, x + 16, y0 + 60, 21, c, size=13, color="muted"))
    return pane(W, H, c, "cat about.md", "".join(b), css)


# ---------------------------------------------------------------- pipeline: a commit travels to production
def pipeline(c):
    W, H = 880, 250
    stages = [("Commit", "Git", "git"), ("Build", "GitLab CI", "gitlab"), ("Package", "Docker", "docker"),
              ("Store", "Amazon ECR", "amazonwebservices"), ("Template", "Helm", "helm"),
              ("Sync", "Argo CD", "argo"), ("Run", "Kubernetes", "kubernetes"), ("Observe", "Datadog", "datadog")]
    n, x0, x1, cy = len(stages), 70, W - 70, 112
    step = (x1 - x0) / (n - 1)
    dur, travel = 7.0, 5.6
    css = (f".node {{ animation: lit {dur}s linear infinite; }}"
           f"@keyframes lit {{ 0% {{ stroke: {c['accent']}; stroke-width: 2; }} 10%, 100% {{ stroke: {c['border']}; stroke-width: 1; }} }}"
           f".done {{ animation: done {dur}s linear infinite; }}"
           f"@keyframes done {{ 0%, 80% {{ opacity: 0; }} 84%, 96% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}")
    b = [f'<line x1="{x0}" y1="{cy}" x2="{x1}" y2="{cy}" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="4 6"/>',
         # the travelled part of the line fills in behind the commit
         f'<line x1="{x0}" y1="{cy}" x2="{x0}" y2="{cy}" stroke="{c["accent"]}" stroke-width="2" opacity=".55">'
         f'<animate attributeName="x2" dur="{dur}s" repeatCount="indefinite" keyTimes="0;{travel/dur:.3f};0.97;1" values="{x0};{x1};{x1};{x0}"/></line>']
    for i, (stage, tool, ic) in enumerate(stages):
        x = x0 + i * step
        delay = travel * i / (n - 1)
        b.append(f'<rect class="node" style="animation-delay:{delay:.2f}s" x="{x-28:.1f}" y="{cy-28}" width="56" height="56" rx="14" fill="{c["tile"]}" stroke="{c["border"]}"/>')
        b.append(icon(ic, f"{x-14:.1f}", cy - 14, 28, c["text"]))
        b.append(f'<text x="{x:.1f}" y="{cy+56}" text-anchor="middle" class="s" font-size="14" font-weight="600" fill="{c["text"]}">{stage}</text>')
        b.append(f'<text x="{x:.1f}" y="{cy+76}" text-anchor="middle" class="m" font-size="11.5" fill="{c["muted"]}">{tool}</text>')
    b.append(f'<circle r="5" fill="{c["accent"]}"><animateMotion dur="{dur}s" repeatCount="indefinite" '
             f'keyPoints="0;1;1" keyTimes="0;{travel/dur:.3f};1" calcMode="linear" path="M{x0},{cy} H{x1}"/></circle>')
    b.append(f'<g class="done"><rect x="{x1-38}" y="{cy-62}" width="76" height="22" rx="11" fill="{c["accent_soft"]}"/>'
             f'<text x="{x1}" y="{cy-47}" text-anchor="middle" class="m" font-size="11" fill="{c["ok"]}">✓ deployed</text></g>')
    b.append(f'<text x="{W/2}" y="{H-20}" text-anchor="middle" class="m" font-size="12" fill="{c["muted"]}">'
             f'merge → build → image → registry → chart → GitOps sync → cluster → dashboards</text>')
    return pane(W, H, c, "git push origin main", "".join(b), css, label="how I ship")


# ---------------------------------------------------------------- toolbox: a soft scan line sweeps across
def toolbox(c):
    W, H = 880, 240
    cols = [("Cloud & IaC", [("AWS", "amazonwebservices"), ("Terraform", "terraform"), ("Cloudflare", "cloudflare")]),
            ("Containers", [("Kubernetes", "kubernetes"), ("Docker", "docker"), ("Helm", "helm")]),
            ("Delivery", [("GitLab CI/CD", "gitlab"), ("Argo CD", "argo"), ("Git", "git")]),
            ("Observability", [("Datadog", "datadog"), ("CloudWatch", "amazoncloudwatch"), ("Splunk", "splunk")]),
            ("Scripting", [("Python", "python"), ("Bash", "gnubash"), ("Linux", "linux")])]
    cw, gap, x0, y0 = 156, 13, 32, 62
    css = (".scan { animation: scan 11s cubic-bezier(.45,0,.25,1) 3s infinite backwards; }"
           "@keyframes scan { 0% { transform: translateX(-260px); } 38%, 100% { transform: translateX(1000px); } }")
    b = [f'<defs><linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{c["accent"]}" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="{c["accent"]}" stop-opacity="{.10 if c["name"] == "light" else .14}"/>'
         f'<stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="tiles"><rect x="{x0}" y="{y0}" width="{W - 2*x0}" height="152" rx="10"/></clipPath></defs>']
    for i, (cat, items) in enumerate(cols):
        x = x0 + i * (cw + gap)
        b.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="152" rx="10" fill="{c["tile"]}" stroke="{c["border"]}"/>')
        b.append(f'<text x="{x+16}" y="{y0+28}" class="m" font-size="11.5" letter-spacing="0.5" fill="{c["accent"]}">{esc(cat.upper())}</text>')
        for j, (name, ic) in enumerate(items):
            yy = y0 + 50 + j * 32
            if ic == "splunk":  # simple-icons' Splunk is a wordmark; draw its ">" mark instead
                b.append(f'<path d="M{x+19},{yy+3} l11,6 l-11,6" fill="none" stroke="{c["text"]}" '
                         f'stroke-width="2.6" stroke-linejoin="round"/>')
            else:
                b.append(icon(ic, x + 16, yy, 18, c["text"]))
            b.append(f'<text x="{x+44}" y="{yy+14}" class="s" font-size="14" fill="{c["text"]}">{esc(name)}</text>')
    b.append(f'<g clip-path="url(#tiles)"><rect class="scan" x="0" y="{y0}" width="220" height="152" fill="url(#beam)"/></g>')
    return pane(W, H, c, "ls ~/toolbox", "".join(b), css)


# ---------------------------------------------------------------- certs: light glints across the badges
def cert(c, kind):
    W, H = 280, 330
    if kind == "cka":
        css = (".draw { animation: draw 7s ease-in-out infinite; }"
               "@keyframes draw { 0% { stroke-dashoffset: 100; opacity: 1; } 55%, 85% { stroke-dashoffset: 38; opacity: 1; } 100% { stroke-dashoffset: 38; opacity: 0; } }"
               ".spin { transform-origin: 140px 128px; animation: spin 14s linear infinite; }"
               "@keyframes spin { to { transform: rotate(360deg); } }"
               ".pulse { animation: p 1.6s ease-in-out infinite; } @keyframes p { 50% { opacity: .25; } }")
        hexa = "140,62 197,95 197,161 140,194 83,161 83,95"
        b = [f'<polygon points="{hexa}" fill="none" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="6 5"/>',
             f'<polygon class="draw" points="{hexa}" pathLength="100" fill="none" stroke="{c["warn"]}" stroke-width="2.5" '
             f'stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="38"/>',
             f'<g class="spin">{icon("kubernetes", 112, 100, 56, c["muted"])}</g>',
             lines(["Certified Kubernetes", "Administrator"], 140, 232, 22, c, size=16, weight=600, anchor="middle"),
             f'<circle cx="104" cy="291" r="4.5" fill="{c["warn"]}" class="pulse"/>'
             f'<text x="116" y="296" class="m" font-size="12.5" fill="{c["warn"]}">in progress</text>']
        return pane(W, H, c, "", "".join(b), css, dashed=True, aria="Certified Kubernetes Administrator, in progress")
    name, issuer, date, img, delay = {
        "aws": (["AWS Certified Solutions", "Architect – Associate"], "Amazon Web Services", "Sep 2025", "aws-s.png", 1.5),
        "tf": (["HashiCorp Certified:", "Terraform Associate"], "HashiCorp", "Jan 2026", "tf-s.png", 6.0),
    }[kind]
    css = (f".glint {{ animation: glint 9s ease-in-out {delay}s infinite backwards; }}"
           "@keyframes glint { 0% { transform: translateX(-120px); } 16%, 100% { transform: translateX(260px); } }")
    b = [f'<defs><image id="badge" href="{data_uri(os.path.join(IMG, img), "image/png")}" x="70" y="40" width="140" height="140"/>'
         f'<mask id="shape" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><use href="#badge"/></mask>'
         f'<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="{c["glint"]}" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="{c["glint"]}" stop-opacity=".55"/><stop offset="1" stop-color="{c["glint"]}" stop-opacity="0"/></linearGradient></defs>',
         '<use href="#badge"/>',
         f'<g mask="url(#shape)"><g transform="rotate(22 140 110)"><rect class="glint" x="0" y="0" width="56" height="240" fill="url(#shine)"/></g></g>',
         lines(name, 140, 216, 22, c, size=16, weight=600, anchor="middle"),
         f'<text x="140" y="266" text-anchor="middle" class="s" font-size="13" fill="{c["muted"]}">{issuer} · {date}</text>',
         f'<text x="140" y="298" text-anchor="middle" class="m" font-size="12" fill="{c["accent"]}">verify on credly ↗</text>']
    return pane(W, H, c, "", "".join(b), css, aria=" ".join(name))


# ---------------------------------------------------------------- projects
def project_loft(c):
    W, H = 430, 420
    shot = data_uri(os.path.join(IMG, "loft.jpg"), "image/jpeg")
    css = (".kb { transform-origin: 215px 150px; animation: kb 22s ease-in-out infinite alternate; }"
           "@keyframes kb { from { transform: scale(1) translate(0, 0); } to { transform: scale(1.12) translate(-14px, 6px); } }")
    b = [f'<defs><clipPath id="clip"><rect x="20" y="58" width="{W-40}" height="190" rx="8"/></clipPath></defs>',
         f'<g clip-path="url(#clip)"><image class="kb" href="{shot}" x="20" y="58" width="{W-40}" height="{(W-40)*1034/2000:.0f}"/></g>',
         f'<rect x="20" y="58" width="{W-40}" height="190" rx="8" fill="none" stroke="{c["border"]}"/>',
         f'<text x="22" y="284" class="s" font-size="19" font-weight="600" fill="{c["text"]}">Loft</text>',
         f'<text x="70" y="284" class="m" font-size="12" fill="{c["muted"]}">personal project</text>',
         lines(["A private photo and video gallery on Cloudflare's",
                "free tier, about $0–3 a month. One Worker serves",
                "the React PWA and API; R2 and D1 store the media."], 22, 312, 21, c, size=13.5, color="muted"),
         chips(["Workers", "R2", "D1", "Zero Trust", "TypeScript"], 22, 372, c)]
    return pane(W, H, c, "open loft-photo-gallery", "".join(b), css, label="↗ repo")


def project_rag(c):
    W, H = 430, 420
    nodes = [("Audit", "findings"), ("Embed", "vectors"), ("ChromaDB", "index"), ("FastAPI", "search")]
    nx0, nw, ng, ny = 34, 78, 16, 136
    centers = [nx0 + i * (nw + ng) + nw / 2 for i in range(len(nodes))]
    cy, ry = ny + 29, ny + 78
    dur = 7.0
    css = (".star { transform-origin: 0 0; animation: tw 3s ease-in-out infinite; }"
           "@keyframes tw { 50% { opacity: .3; } }")
    b = [f'<rect x="20" y="58" width="{W-40}" height="190" rx="8" fill="{c["tile"]}" stroke="{c["border"]}"/>',
         f'<rect x="{W/2-118}" y="76" width="236" height="26" rx="13" fill="{c["accent_soft"]}"/>',
         f'<text x="{W/2-96}" y="94" class="m star" font-size="12" fill="{c["accent"]}">★</text>',
         f'<text x="{W/2+8}" y="94" text-anchor="middle" class="m" font-size="11.5" fill="{c["accent"]}">HACKATHON FINALIST · TOP 10</text>']
    for i, (t, sub) in enumerate(nodes):
        x = nx0 + i * (nw + ng)
        b.append(f'<rect x="{x}" y="{ny}" width="{nw}" height="58" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>')
        b.append(f'<text x="{x+nw/2}" y="{ny+26}" text-anchor="middle" class="s" font-size="13" font-weight="600" fill="{c["text"]}">{t}</text>')
        b.append(f'<text x="{x+nw/2}" y="{ny+44}" text-anchor="middle" class="m" font-size="10.5" fill="{c["muted"]}">{sub}</text>')
        if i < len(nodes) - 1:
            ax = x + nw
            b.append(f'<path d="M{ax+3},{cy} h{ng-8} m-4,-4 l4,4 l-4,4" fill="none" stroke="{c["muted"]}" stroke-width="1.5"/>')
    # a query hops node to node, then the answer slides back underneath
    hop = 0.11
    kp, kt, t = ["0"], ["0"], 0.04
    for i in range(1, len(centers)):
        kp += [f"{(i-1)/3:.4f}", f"{i/3:.4f}"]
        kt += [f"{t:.4f}", f"{t+hop:.4f}"]
        t += hop + 0.04
    kp += ["1", "1"]; kt += [f"{t:.4f}", "1"]
    b.append(f'<circle r="4.5" fill="{c["accent"]}"><animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" '
             f'keyPoints="{";".join(kp)}" keyTimes="{";".join(kt)}" path="M{centers[0]},{ny} H{centers[-1]}"/>'
             f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" keyTimes="0;{t:.3f};{t+0.02:.3f};1" values="1;1;0;0"/></circle>')
    back0, back1 = t + 0.03, t + 0.25
    b.append(f'<path d="M{centers[-1]},{ny+58} V{ry} H{centers[0]} V{ny+58}" fill="none" stroke="{c["border"]}" stroke-dasharray="3 4"/>')
    b.append(f'<circle r="4.5" fill="{c["ok"]}" opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" '
             f'keyPoints="0;0;1;1" keyTimes="0;{back0:.3f};{back1:.3f};1" path="M{centers[-1]},{ny+58} V{ry} H{centers[0]} V{ny+58}"/>'
             f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" keyTimes="0;{back0:.3f};{back1:.3f};{back1+0.02:.3f};1" values="0;1;1;0;0"/></circle>')
    b.append(f'<text x="{W/2}" y="{ry+18}" text-anchor="middle" class="m" font-size="10.5" fill="{c["muted"]}">answer + cited findings</text>')
    b += [f'<text x="22" y="284" class="s" font-size="19" font-weight="600" fill="{c["text"]}">Regulatory Audit RAG</text>',
          f'<text x="222" y="284" class="m" font-size="12" fill="{c["muted"]}">IQVIA hackathon</text>',
          lines(["A retrieval service that indexes historical audit",
                 "findings and remediation playbooks, with semantic",
                 "search endpoints on top."], 22, 312, 21, c, size=13.5, color="muted"),
          chips(["Python", "FastAPI", "ChromaDB", "LLM APIs"], 22, 372, c)]
    return pane(W, H, c, "cat hackathon/README.md", "".join(b), css)


# ---------------------------------------------------------------- logs drawer: career log streams in when opened
def logs(c):
    W = 880
    entries = [("2024-02", "INFO", "ok", "joined IQVIA as a DevOps Engineer"),
               ("2025-09", "INFO", "ok", "passed AWS Certified Solutions Architect – Associate"),
               ("2026-01", "INFO", "ok", "passed HashiCorp Certified: Terraform Associate (004)"),
               ("now", "INFO", "ok", "DevOps Engineer 2 · IQVIA Impact Award · hackathon Top 10"),
               ("next", "WARN", "warn", "CKA exam: preparing")]
    H = 70 + len(entries) * 30 + 20
    css = (".ln { animation: show .3s ease-out backwards; } @keyframes show { from { opacity: 0; } }"
           ".cur { animation: blink 1.1s steps(1) infinite; } @keyframes blink { 50% { opacity: 0; } }")
    b, y = [], 74
    for i, (ts, lvl, col, msg) in enumerate(entries):
        b.append(f'<g class="ln" style="animation-delay:{0.25 + i*0.32:.2f}s">'
                 f'<text x="32" y="{y}" class="m" font-size="14" fill="{c["muted"]}">{ts}</text>'
                 f'<text x="120" y="{y}" class="m" font-size="14" fill="{c[col]}">{lvl}</text>'
                 f'<text x="180" y="{y}" class="m" font-size="14" fill="{c["text"]}">{esc(msg)}</text>')
        if i == len(entries) - 1:
            cx = 180 + len(msg) * 8.43 + 6
            b.append(f'<rect class="cur" x="{cx:.0f}" y="{y-12}" width="8" height="16" fill="{c["text"]}"/>')
        b.append("</g>")
        y += 30
    return pane(W, H, c, "kubectl logs muhsin --previous", "".join(b), css)


# ---------------------------------------------------------------- the cute one: a container ship at sea
SPRITE = [  # tiny pixel me (from the avatar): spiky hair, shades, green tee
    "..H.H..H.H..",
    ".HHHHHHHHHH.",
    "HHHHHHHHHHHH",
    "HHSSSSSSSSHH",
    "HGGGGGGGGGGH",
    ".SGGWSSGGWS.",
    ".SSSSSSSSSS.",
    ".SSSSMMSSSS.",
    "..SSSSSSSS..",
    "..JJTTTTJJ..",
    ".JJJTTTTJJJ.",
    ".JJJTTTTJJJ.",
]


def sprite(c, x, y, px):
    pal = {"H": "#1b1f24" if c["name"] == "light" else "#3d444d", "G": "#1b1f24" if c["name"] == "light" else "#010409", "W": "#ffffff",
           "S": "#f2c4a0", "M": "#9a5b4b", "J": "#8c959f", "T": "#2da44e"}
    rects = []
    for r, row in enumerate(SPRITE):
        for col, ch in enumerate(row):
            if ch != ".":
                rects.append(f'<rect x="{x + col*px}" y="{y + r*px}" width="{px}" height="{px}" fill="{pal[ch]}"/>')
    # waving arm: two frames toggled with steps()
    ax, ay = x + 12 * px, y + 9 * px
    arm_up = (f'<g class="wave-a"><rect x="{ax}" y="{ay - px}" width="{px}" height="{px}" fill="{pal["J"]}"/>'
              f'<rect x="{ax + px}" y="{ay - 2*px}" width="{px}" height="{px}" fill="{pal["J"]}"/>'
              f'<rect x="{ax + px}" y="{ay - 3*px}" width="{px}" height="{px}" fill="{pal["S"]}"/></g>')
    arm_dn = (f'<g class="wave-b"><rect x="{ax}" y="{ay - px}" width="{px}" height="{px}" fill="{pal["J"]}"/>'
              f'<rect x="{ax + px}" y="{ay - 2*px}" width="{px}" height="{px}" fill="{pal["J"]}"/>'
              f'<rect x="{ax + 2*px}" y="{ay - 3*px}" width="{px}" height="{px}" fill="{pal["S"]}"/></g>')
    return "".join(rects) + arm_up + arm_dn


def wave_path(y, amp, period, x0, x1, bottom):
    pts = [f"M{x0},{bottom} L{x0},{y}"]
    x = x0
    while x < x1:
        pts.append(f"q{period/4},{-amp} {period/2},0 t{period/2},0")
        x += period
    pts.append(f"L{x},{bottom} Z")
    return " ".join(pts)


def harbor(c):
    W, H = 880, 240
    sea_y = 182
    dark = c["name"] == "dark"
    css = (
        ".w1 { animation: w 7s linear infinite; } .w2 { animation: w 4.5s linear infinite reverse; }"
        "@keyframes w { to { transform: translateX(-90px); } }"
        ".sail { animation: sail 46s linear -14s infinite; }"
        "@keyframes sail { from { transform: translateX(-280px); } to { transform: translateX(1000px); } }"
        ".bob { transform-origin: 100px 30px; animation: bob 3.2s ease-in-out infinite; }"
        "@keyframes bob { 0%, 100% { transform: translateY(0) rotate(-1.2deg); } 50% { transform: translateY(3px) rotate(1.2deg); } }"
        ".wave-a { animation: arm .9s steps(1) infinite; } .wave-b { animation: arm .9s steps(1) -.45s infinite; }"
        "@keyframes arm { 50% { opacity: 0; } }"
        ".puff { transform-box: fill-box; transform-origin: center; animation: puff 3.6s ease-out infinite backwards; }"
        "@keyframes puff { from { transform: translate(0, 0) scale(.5); opacity: .7; } to { transform: translate(-26px, -34px) scale(1.7); opacity: 0; } }"
        ".whale { animation: whale 23s ease-in-out -3s infinite; }  /* 23s = half the 46s crossing, phased so the whale never surfaces under the ship */"
        "@keyframes whale { 0%, 100% { transform: translateY(100px); } 8%, 30% { transform: translateY(0); } 40% { transform: translateY(100px); } }"
        ".spout { transform-box: fill-box; transform-origin: bottom; animation: spout 23s ease-out -3s infinite; }"
        "@keyframes spout { 0%, 11% { transform: scaleY(0); opacity: 0; } 14% { transform: scaleY(1); opacity: 1; } 22%, 100% { transform: scaleY(1.1); opacity: 0; } }"
        ".cloud { animation: drift 80s linear infinite; } .cloud2 { animation: drift 120s linear -50s infinite; }"
        "@keyframes drift { from { transform: translateX(-200px); } to { transform: translateX(1000px); } }"
        ".gull { animation: gull 28s linear -6s infinite; }"
        "@keyframes gull { from { transform: translate(940px, 0); } 50% { transform: translate(420px, -10px); } to { transform: translate(-60px, 4px); } }"
        ".flap { transform-box: fill-box; transform-origin: center; animation: flap .5s ease-in-out infinite alternate; }"
        "@keyframes flap { to { transform: scaleY(-.6); } }"
        ".tw { animation: tw 3s ease-in-out infinite; } @keyframes tw { 50% { opacity: .2; } }"
        ".flag { transform-box: fill-box; transform-origin: right center; animation: flag .7s ease-in-out infinite alternate; }"
        "@keyframes flag { to { transform: skewY(8deg) scaleX(.85); } }"
    )
    b = [f'<defs><clipPath id="body"><path d="M1,41 H{W-1} V{H-13} a12 12 0 0 1 -12 12 H13 a12 12 0 0 1 -12 -12 Z"/></clipPath></defs>',
         '<g clip-path="url(#body)">']
    # sky: moon and stars at night, sun by day
    if dark:
        b.append('<g fill="#e6edf3">' + "".join(
            f'<circle class="tw" style="animation-delay:{d}s" cx="{x}" cy="{y}" r="{r}"/>'
            for x, y, r, d in [(90, 70, 1.2, 0), (210, 96, 1, 1.2), (330, 62, 1.4, .6), (470, 88, 1, 2), (560, 58, 1.2, 1.5),
                               (690, 104, 1, .3), (760, 70, 1.3, 2.4), (840, 92, 1, 1)]) + "</g>")
        b.append('<circle cx="800" cy="84" r="16" fill="#e6edf3" opacity=".9"/><circle cx="808" cy="78" r="15" fill="#0d1117"/>')
    else:
        b.append('<circle cx="800" cy="86" r="34" fill="#f2cc60" opacity=".18"/><circle cx="800" cy="86" r="18" fill="#f2cc60" opacity=".7"/>')
    cloud = lambda x, y, s: (f'<g transform="translate({x},{y}) scale({s})" fill="{c["cloud"]}">'
                             '<ellipse cx="30" cy="16" rx="30" ry="10"/><ellipse cx="22" cy="10" rx="14" ry="10"/><ellipse cx="40" cy="8" rx="16" ry="12"/></g>')
    b.append(f'<g class="cloud">{cloud(100, 64, 1)}</g><g class="cloud2">{cloud(300, 90, .7)}</g>')
    # seagull
    b.append(f'<g class="gull"><path class="flap" d="M0,80 q6,-7 12,0 q6,-7 12,0" fill="none" stroke="{c["muted"]}" stroke-width="1.8" stroke-linecap="round"/></g>')
    # back wave, then the whale, then the ship, then the front wave
    b.append(f'<path class="w2" d="{wave_path(sea_y - 6, 5, 90, -10, W + 200, H)}" fill="{c["sea1"]}"/>')
    whale = icon_d("docker")
    b.append(f'<g class="whale"><svg x="640" y="{sea_y - 26}" width="58" height="58" viewBox="0 0 24 24"><path fill="#2496ed" d="{whale}"/></svg>'
             f'<path class="spout" d="M686,{sea_y-18} q-4,-10 -10,-12 M686,{sea_y-18} q0,-12 0,-16 M686,{sea_y-18} q4,-10 10,-12" '
             f'fill="none" stroke="#2496ed" stroke-width="2" stroke-linecap="round" opacity="0"/></g>')
    # the ship (drawn around a local origin; hull top at y=0, ~200 wide)
    boxes, bx = [], 36
    for i in range(5):
        boxes.append(f'<rect x="{bx + i*28}" y="-17" width="26" height="16" rx="1.5" fill="{c["boxes"][i]}"/>'
                     f'<path d="M{bx + i*28 + 7},-15 v12 M{bx + i*28 + 13},-15 v12 M{bx + i*28 + 19},-15 v12" stroke="#00000033" stroke-width="1"/>')
    for i in range(3):
        boxes.append(f'<rect x="{bx + 28 + i*28}" y="-34" width="26" height="16" rx="1.5" fill="{c["boxes"][(i+3) % 6]}"/>'
                     f'<path d="M{bx + 35 + i*28},-32 v12 M{bx + 41 + i*28},-32 v12 M{bx + 47 + i*28},-32 v12" stroke="#00000033" stroke-width="1"/>')
    ship = (f'<g class="sail"><g transform="translate(0,{sea_y - 22})"><g class="bob">'
            f'<circle class="puff" cx="22" cy="-50" r="5" fill="{c["cloud"]}" style="animation-delay:0s"/>'
            f'<circle class="puff" cx="22" cy="-50" r="5" fill="{c["cloud"]}" style="animation-delay:1.2s"/>'
            f'<circle class="puff" cx="22" cy="-50" r="5" fill="{c["cloud"]}" style="animation-delay:2.4s"/>'
            f'<rect x="16" y="-48" width="12" height="16" rx="1" fill="{c["hull"]}"/><rect x="16" y="-44" width="12" height="4" fill="#326ce5"/>'
            f'<rect x="4" y="-32" width="28" height="32" rx="2" fill="{c["cabin"]}"/>'
            f'<rect x="8" y="-27" width="6" height="5" rx="1" fill="{c["bg"]}"/><rect x="18" y="-27" width="6" height="5" rx="1" fill="{c["bg"]}"/>'
            f'<svg x="10" y="-16" width="14" height="14" viewBox="0 0 24 24"><path fill="#326ce5" d="{icon_d("kubernetes")}"/></svg>'
            f'<line x1="6" y1="-32" x2="6" y2="-58" stroke="{c["hull"]}" stroke-width="1.6"/>'
            f'<path class="flag" d="M6,-58 h-15 l4,5 l-4,5 h15 Z" fill="#326ce5"/>'
            + "".join(boxes) +
            sprite(c, 178, -30, 2.5) +
            f'<path d="M0,0 H212 L196,22 H12 Z" fill="{c["hull"]}"/>'
            f'<path d="M5,9 H207" stroke="#cf222e" stroke-width="3" opacity=".75"/>'
            f'<text x="104" y="18" text-anchor="middle" class="m" font-size="8" fill="{c["bg"]}" letter-spacing="1">MV KUBERNETES</text>'
            '</g></g></g>')
    b.append(ship)
    b.append(f'<path class="w1" d="{wave_path(sea_y + 4, 4, 90, -10, W + 200, H)}" fill="{c["sea2"]}"/>')
    b.append("</g>")
    return pane(W, H, c, "./ship-it.sh", "".join(b), css,
                label=f'<tspan fill="{c["ok"]}">●</tspan> all pods healthy', aria="A tiny container ship sailing past")


# ---------------------------------------------------------------- buttons
def button(c, kind):
    W, H = 300, 56
    if kind == "linkedin":
        ic, label, sub = icon("linkedin", 22, 16, 24, c["text"]), "LinkedIn", "in/muhsinjifri"
    else:
        ic = (f'<svg x="22" y="16" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{c["text"]}" stroke-width="1.8">'
              f'<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="M3.5 6.5 L12 13 L20.5 6.5"/></svg>')
        label, sub = "Email", "muhsinjifri@gmail.com"
    return (f'{svg_open(W, H, label)}{style()}'
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="28" fill="{c["bar"]}" stroke="{c["border"]}"/>{ic}'
            f'<text x="58" y="34" class="s" font-size="15" font-weight="600" fill="{c["text"]}">{label}</text>'
            f'<text x="{58 + len(label)*9 + 10}" y="34" class="m" font-size="12.5" fill="{c["muted"]}">{sub}</text></svg>\n')


CARDS = {
    "header": header, "about": about, "pipeline": pipeline, "toolbox": toolbox, "logs": logs,
    "cert-aws": lambda c: cert(c, "aws"), "cert-terraform": lambda c: cert(c, "tf"), "cert-cka": lambda c: cert(c, "cka"),
    "project-loft": project_loft, "project-rag": project_rag, "harbor": harbor,
    "btn-linkedin": lambda c: button(c, "linkedin"), "btn-email": lambda c: button(c, "email"),
}
for name, fn in CARDS.items():
    for t, c in THEMES.items():
        open(f"{OUT}/{name}-{t}.svg", "w").write(fn(c))
print("ok", len(CARDS) * 2, "files")
