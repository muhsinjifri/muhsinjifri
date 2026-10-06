import sys, os
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
THEMES = {
  "dark":  dict(bg="#0d1117", bar="#161b22", border="#30363d", text="#e6edf3", key="#7d8590", prompt="#3fb950", cmd="#e6edf3", accent="#58a6ff", ok="#3fb950", title="#7d8590"),
  "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", text="#1f2328", key="#656d76", prompt="#1a7f37", cmd="#1f2328", accent="#0969da", ok="#1a7f37", title="#656d76"),
}
ROWS = [
  ("Name",      [("Sayed Muhsin Jifri", "text", True)]),
  ("Role",      [("DevOps Engineer", "text", False), (" @ ", "key", False), ("IQVIA", "text", False)]),
  ("Location",  [("Bengaluru, India", "text", False)]),
  ("Focus",     [("Kubernetes · GitOps · CI/CD · AWS · Terraform", "accent", False)]),
  ("Certified", [("AWS Solutions Architect Associate · Terraform Associate", "text", False)]),
  ("Next",      [("CKA (in progress)", "text", False)]),
]
W, H = 880, 352
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
BOLD = ' font-weight="700"'
def svg(t):
    c = THEMES[t]
    y0, lh, kx, vx = 96, 30, 40, 190
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Sayed Muhsin Jifri, DevOps Engineer">
<style>
  text {{ font-family: {FONT}; font-size: 16px; }}
  .cur {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .cur {{ animation: none; }} }}
</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{c['bg']}" stroke="{c['border']}"/>
<path d="M0.5 44 V12.5 a12 12 0 0 1 12 -12 H{W-12.5} a12 12 0 0 1 12 12 V44 Z" fill="{c['bar']}"/>
<line x1="0.5" y1="44" x2="{W-0.5}" y2="44" stroke="{c['border']}"/>
<circle cx="24" cy="22" r="6" fill="#ff5f57"/><circle cx="44" cy="22" r="6" fill="#febc2e"/><circle cx="64" cy="22" r="6" fill="#28c840"/>
<text x="{W/2}" y="27" text-anchor="middle" fill="{c['title']}" style="font-size:13px">muhsin@bengaluru: ~</text>
<text x="{kx}" y="{y0-12}" fill="{c['prompt']}">$<tspan fill="{c['cmd']}"> kubectl describe engineer muhsin</tspan></text>''']
    y = y0 + 22
    for k, vals in ROWS:
        tsp = "".join(f'<tspan fill="{c[col]}"{BOLD if b else ""}>{v}</tspan>' for v, col, b in vals)
        parts.append(f'<text x="{kx}" y="{y}" fill="{c["key"]}">{k}:</text><text x="{vx}" y="{y}" xml:space="preserve">{tsp}</text>')
        y += lh
    parts.append(f'<text x="{kx}" y="{y}" fill="{c["key"]}">Status:</text><circle cx="{vx+5}" cy="{y-5}" r="5" fill="{c["ok"]}"/><text x="{vx+18}" y="{y}" fill="{c["ok"]}">Running</text><text x="{vx+92}" y="{y}" fill="{c["key"]}">· open to new opportunities</text>')
    y += lh + 6
    parts.append(f'<text x="{kx}" y="{y}" fill="{c["prompt"]}">$</text><rect class="cur" x="{kx+18}" y="{y-14}" width="9" height="18" fill="{c["text"]}"/>')
    parts.append("</svg>\n")
    return "\n".join(parts)
for t in THEMES:
    open(f"{out}/header-{t}.svg", "w").write(svg(t))
