"""Generate the profile README cards (light + dark) in one visual system.

usage: python3 cards.py <icons_dir> <img_dir> <out_dir>
"""
import base64, os, re, sys
from xml.sax.saxutils import escape as esc

ICONS, IMG, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(bg="#0d1117", bar="#161b22", tile="#161b22", border="#30363d", text="#e6edf3",
                 muted="#7d8590", prompt="#3fb950", accent="#58a6ff", accent_soft="#388bfd26",
                 ok="#3fb950", warn="#d29922", chip="#21262d"),
    "light": dict(bg="#ffffff", bar="#f6f8fa", tile="#f6f8fa", border="#d0d7de", text="#1f2328",
                  muted="#656d76", prompt="#1a7f37", accent="#0969da", accent_soft="#0969da1a",
                  ok="#1a7f37", warn="#9a6700", chip="#eaeef2"),
}


def icon(name, x, y, size, fill):
    d = re.search(r'd="([^"]+)"', open(f"{ICONS}/{name}.svg").read()).group(1)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path fill="{fill}" d="{d}"/></svg>')


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def style(extra=""):
    return f"""<style>
  .m {{ font-family: {MONO}; }}
  .s {{ font-family: {SANS}; }}
  {extra}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>"""


def pane(w, h, c, cmd, body, extra_style="", label=None, dashed=False):
    """A card with a terminal-style title bar showing the command that 'printed' it."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lab = (f'<text x="{w-20}" y="25" text-anchor="end" class="m" font-size="12" fill="{c["muted"]}">{esc(label)}</text>'
           if label else "")
    head = (f'<path d="M0.5 40 V12.5 a12 12 0 0 1 12 -12 H{w-12.5} a12 12 0 0 1 12 12 V40 Z" fill="{c["bar"]}"/>'
            f'<line x1="0.5" y1="40" x2="{w-0.5}" y2="40" stroke="{c["border"]}"/>'
            f'<text x="20" y="25" class="m" font-size="13"><tspan fill="{c["prompt"]}">$</tspan>'
            f'<tspan fill="{c["text"]}"> {esc(cmd)}</tspan></text>{lab}') if cmd else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'{style(extra_style)}'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{c["bg"]}" stroke="{c["border"]}"{dash}/>'
            f'{head}{body}</svg>\n')


def chips(items, x, y, c, size=12):
    out, cx = [], x
    for it in items:
        wdt = len(it) * size * 0.62 + 18
        out.append(f'<rect x="{cx}" y="{y}" width="{wdt:.0f}" height="24" rx="12" fill="{c["chip"]}"/>'
                   f'<text x="{cx + wdt/2:.0f}" y="{y+16}" text-anchor="middle" class="m" font-size="{size}" fill="{c["muted"]}">{esc(it)}</text>')
        cx += wdt + 8
    return "".join(out)


def lines(txt_lines, x, y, lh, c, size=15, color="text", cls="s", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return "".join(f'<text x="{x}" y="{y + i*lh}" class="{cls}" font-size="{size}" fill="{c[color]}"{w}>{esc(t)}</text>'
                   for i, t in enumerate(txt_lines))


# ---------------------------------------------------------------- about
def about(c):
    W, H = 880, 300
    cols = [
        ("01", "Ship", ["CI/CD and GitOps pipelines", "that take code from merge", "request to production."]),
        ("02", "Run", ["Containerized services on", "Kubernetes, with autoscaling", "and health probes."]),
        ("03", "Build", ["AWS infrastructure as", "Terraform: reproducible,", "reviewed and versioned."]),
        ("04", "Secure", ["Least-privilege IAM and", "no long-lived secrets", "inside workloads."]),
    ]
    b = [lines(["I'm a DevOps engineer. I get software from a merge request into production",
                "safely and repeatably, and keep it easy to see what's running."], 32, 82, 26, c, size=17)]
    cw, gap, x0, y0 = 196, 14, 32, 140
    for i, (n, title, body) in enumerate(cols):
        x = x0 + i * (cw + gap)
        b.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="132" rx="10" fill="{c["tile"]}" stroke="{c["border"]}"/>')
        b.append(f'<text x="{x+16}" y="{y0+30}" class="m" font-size="12" fill="{c["accent"]}">{n}</text>')
        b.append(f'<text x="{x+42}" y="{y0+30}" class="s" font-size="16" font-weight="600" fill="{c["text"]}">{title}</text>')
        b.append(lines(body, x + 16, y0 + 60, 21, c, size=13, color="muted"))
    return pane(W, H, c, "cat about.md", "".join(b))


# ---------------------------------------------------------------- pipeline
def pipeline(c):
    W, H = 880, 250
    stages = [("Commit", "Git", "git"), ("Build", "GitLab CI", "gitlab"), ("Package", "Docker", "docker"),
              ("Store", "Amazon ECR", "amazonwebservices"), ("Template", "Helm", "helm"),
              ("Sync", "Argo CD", "argo"), ("Run", "Kubernetes", "kubernetes"), ("Observe", "Datadog", "datadog")]
    n, x0, x1, cy = len(stages), 70, W - 70, 112
    step = (x1 - x0) / (n - 1)
    dur, travel = 7.0, 5.6  # seconds: full loop, time spent moving
    css = (f".node {{ animation: lit {dur}s linear infinite; }}"
           f"@keyframes lit {{ 0% {{ stroke: {c['accent']}; stroke-width: 2; }} 10% {{ stroke: {c['border']}; stroke-width: 1; }} 100% {{ stroke: {c['border']}; stroke-width: 1; }} }}")
    b = [f'<line x1="{x0}" y1="{cy}" x2="{x1}" y2="{cy}" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="4 6"/>']
    for i, (stage, tool, ic) in enumerate(stages):
        x = x0 + i * step
        delay = travel * i / (n - 1)
        b.append(f'<rect class="node" style="animation-delay:{delay:.2f}s" x="{x-28:.1f}" y="{cy-28}" width="56" height="56" rx="14" fill="{c["tile"]}" stroke="{c["border"]}"/>')
        b.append(icon(ic, f"{x-14:.1f}", cy - 14, 28, c["text"]))
        b.append(f'<text x="{x:.1f}" y="{cy+56}" text-anchor="middle" class="s" font-size="14" font-weight="600" fill="{c["text"]}">{stage}</text>')
        b.append(f'<text x="{x:.1f}" y="{cy+76}" text-anchor="middle" class="m" font-size="11.5" fill="{c["muted"]}">{tool}</text>')
    kt = f"0;{travel/dur:.3f};1"
    b.append(f'<circle r="5" fill="{c["accent"]}"><animateMotion dur="{dur}s" repeatCount="indefinite" '
             f'keyPoints="0;1;1" keyTimes="{kt}" calcMode="linear" path="M{x0},{cy} H{x1}"/></circle>')
    b.append(f'<text x="{W/2}" y="{H-20}" text-anchor="middle" class="m" font-size="12" fill="{c["muted"]}">'
             f'merge → build → image → registry → chart → GitOps sync → cluster → dashboards</text>')
    return pane(W, H, c, "git push origin main", "".join(b), css, label="how I ship")


# ---------------------------------------------------------------- toolbox
def toolbox(c):
    W, H = 880, 240
    cols = [("Cloud & IaC", [("AWS", "amazonwebservices"), ("Terraform", "terraform"), ("Cloudflare", "cloudflare")]),
            ("Containers", [("Kubernetes", "kubernetes"), ("Docker", "docker"), ("Helm", "helm")]),
            ("Delivery", [("GitLab CI/CD", "gitlab"), ("Argo CD", "argo"), ("Git", "git")]),
            ("Observability", [("Datadog", "datadog"), ("CloudWatch", "amazoncloudwatch"), ("Splunk", "splunk")]),
            ("Scripting", [("Python", "python"), ("Bash", "gnubash"), ("Linux", "linux")])]
    cw, gap, x0, y0 = 156, 13, 32, 62
    b = []
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
    return pane(W, H, c, "ls ~/toolbox", "".join(b))


# ---------------------------------------------------------------- certs
def cert(c, kind):
    W, H = 280, 330
    if kind == "cka":
        b = [f'<g opacity="0.9"><polygon points="140,62 197,95 197,161 140,194 83,161 83,95" fill="none" '
             f'stroke="{c["border"]}" stroke-width="2" stroke-dasharray="6 5"/>',
             icon("kubernetes", 112, 100, 56, c["muted"]), "</g>",
             lines(["Certified Kubernetes", "Administrator"], 140, 232, 22, c, size=16, weight=600),
             f'<circle cx="104" cy="291" r="4.5" fill="{c["warn"]}" class="pulse"/>'
             f'<text x="116" y="296" class="m" font-size="12.5" fill="{c["warn"]}">in progress</text>']
        css = ".pulse { animation: p 1.6s ease-in-out infinite; } @keyframes p { 50% { opacity: .25; } }"
        body = "".join(b).replace('class="s"', 'class="s" text-anchor="middle"')
        return pane(W, H, c, "", body, css, dashed=True)
    name, issuer, date, img = {
        "aws": (["AWS Certified Solutions", "Architect – Associate"], "Amazon Web Services", "Sep 2025", "aws-s.png"),
        "tf": (["HashiCorp Certified:", "Terraform Associate"], "HashiCorp", "Jan 2026", "tf-s.png"),
    }[kind]
    b = [f'<image href="{data_uri(os.path.join(IMG, img), "image/png")}" x="70" y="40" width="140" height="140"/>',
         lines(name, 140, 216, 22, c, size=16, weight=600).replace('class="s"', 'class="s" text-anchor="middle"'),
         f'<text x="140" y="266" text-anchor="middle" class="s" font-size="13" fill="{c["muted"]}">{issuer} · {date}</text>',
         f'<text x="140" y="298" text-anchor="middle" class="m" font-size="12" fill="{c["accent"]}">verify on credly ↗</text>']
    return pane(W, H, c, "", "".join(b))


# ---------------------------------------------------------------- projects
def project_loft(c):
    W, H = 430, 420
    shot = data_uri(os.path.join(IMG, "loft.jpg"), "image/jpeg")
    b = [f'<defs><clipPath id="clip"><rect x="20" y="58" width="{W-40}" height="190" rx="8"/></clipPath></defs>',
         f'<image href="{shot}" x="20" y="58" width="{W-40}" height="{(W-40)*1034/2000:.0f}" clip-path="url(#clip)" preserveAspectRatio="xMidYMin slice"/>',
         f'<rect x="20" y="58" width="{W-40}" height="190" rx="8" fill="none" stroke="{c["border"]}"/>',
         f'<text x="22" y="284" class="s" font-size="19" font-weight="600" fill="{c["text"]}">Loft</text>',
         f'<text x="70" y="284" class="m" font-size="12" fill="{c["muted"]}">personal project</text>',
         lines(["A private photo and video gallery on Cloudflare's",
                "free tier, about $0–3 a month. One Worker serves",
                "the React PWA and API; R2 and D1 store the media."], 22, 312, 21, c, size=13.5, color="muted"),
         chips(["Workers", "R2", "D1", "Zero Trust", "TypeScript"], 22, 372, c, size=11)]
    return pane(W, H, c, "open loft-photo-gallery", "".join(b), label="↗ repo")


def project_rag(c):
    W, H = 430, 420
    # mini architecture diagram in the same slot as the screenshot
    nodes = [("Audit", "findings"), ("Embed", "vectors"), ("ChromaDB", "index"), ("FastAPI", "search")]
    b = [f'<rect x="20" y="58" width="{W-40}" height="190" rx="8" fill="{c["tile"]}" stroke="{c["border"]}"/>',
         f'<rect x="{W/2-118}" y="76" width="236" height="26" rx="13" fill="{c["accent_soft"]}"/>',
         f'<text x="{W/2}" y="94" text-anchor="middle" class="m" font-size="11.5" fill="{c["accent"]}">★ HACKATHON FINALIST · TOP 10</text>']
    nx0, nw, ng, ny = 34, 78, 16, 136
    for i, (t, sub) in enumerate(nodes):
        x = nx0 + i * (nw + ng)
        b.append(f'<rect x="{x}" y="{ny}" width="{nw}" height="58" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>')
        b.append(f'<text x="{x+nw/2}" y="{ny+26}" text-anchor="middle" class="s" font-size="13" font-weight="600" fill="{c["text"]}">{t}</text>')
        b.append(f'<text x="{x+nw/2}" y="{ny+44}" text-anchor="middle" class="m" font-size="10.5" fill="{c["muted"]}">{sub}</text>')
        if i < len(nodes) - 1:
            ax = x + nw
            b.append(f'<path d="M{ax+3},{ny+29} h{ng-8} m-4,-4 l4,4 l-4,4" fill="none" stroke="{c["muted"]}" stroke-width="1.5"/>')
    b.append(f'<text x="{W/2}" y="226" text-anchor="middle" class="m" font-size="11" fill="{c["muted"]}">query → nearest findings → LLM answer</text>')
    b += [f'<text x="22" y="284" class="s" font-size="19" font-weight="600" fill="{c["text"]}">Regulatory Audit RAG</text>',
          f'<text x="222" y="284" class="m" font-size="12" fill="{c["muted"]}">IQVIA hackathon</text>',
          lines(["A retrieval service that indexes historical audit",
                 "findings and remediation playbooks, with semantic",
                 "search endpoints on top."], 22, 312, 21, c, size=13.5, color="muted"),
          chips(["Python", "FastAPI", "ChromaDB", "LLM APIs"], 22, 372, c, size=11)]
    return pane(W, H, c, "cat hackathon/README.md", "".join(b))


# ---------------------------------------------------------------- buttons
def button(c, kind):
    W, H = 300, 56
    if kind == "linkedin":
        ic, label, sub = icon("linkedin", 22, 16, 24, c["text"]), "LinkedIn", "in/muhsinjifri"
    else:
        ic = (f'<svg x="22" y="16" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{c["text"]}" stroke-width="1.8">'
              f'<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="M3.5 6.5 L12 13 L20.5 6.5"/></svg>')
        label, sub = "Email", "muhsinjifri@gmail.com"
    b = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{style()}'
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="28" fill="{c["bar"]}" stroke="{c["border"]}"/>{ic}'
         f'<text x="58" y="34" class="s" font-size="15" font-weight="600" fill="{c["text"]}">{label}</text>'
         f'<text x="{58 + len(label)*9 + 10}" y="34" class="m" font-size="12.5" fill="{c["muted"]}">{sub}</text></svg>\n')
    return b


CARDS = {
    "about": about, "pipeline": pipeline, "toolbox": toolbox,
    "cert-aws": lambda c: cert(c, "aws"), "cert-terraform": lambda c: cert(c, "tf"), "cert-cka": lambda c: cert(c, "cka"),
    "project-loft": project_loft, "project-rag": project_rag,
    "btn-linkedin": lambda c: button(c, "linkedin"), "btn-email": lambda c: button(c, "email"),
}
for name, fn in CARDS.items():
    for t, c in THEMES.items():
        open(f"{OUT}/{name}-{t}.svg", "w").write(fn(c))
print("ok", len(CARDS) * 2, "files")
