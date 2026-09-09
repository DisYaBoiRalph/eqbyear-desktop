#!/usr/bin/env python3
"""Generate the three design-direction artboards for DMS Sweep.

Run from the design/ folder:  python3 build_mocks.py
Outputs *.dc.html and canvas.json next to this script.
"""
import math, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FMIN, FMAX, FS = 20.0, 20000.0, 48000.0
ACCENT = "#FCBE11"

# ---- sample session state shown in every direction -------------------------
BANDS = [
    dict(n=1, type="PK",  fc=3100, gain=-4.5, q=2.6, marks=(2500, 3100, 3750)),
    dict(n=2, type="LSC", fc=105,  gain=2.0,  q=0.7),
    dict(n=3, type="PK",  fc=8200, gain=-3.0, q=3.4),
]
PREAMP = -2.0
SWEEP_F = 3100
LEVEL_DB = -18

# ---- math ------------------------------------------------------------------
def xlog(f, w):
    return w * math.log(f / FMIN) / math.log(FMAX / FMIN)

def coeffs(b):
    A = 10 ** (b["gain"] / 40)
    w0 = 2 * math.pi * b["fc"] / FS
    c, s = math.cos(w0), math.sin(w0)
    al = s / (2 * b["q"])
    if b["type"] == "PK":
        return (1 + al * A, -2 * c, 1 - al * A, 1 + al / A, -2 * c, 1 - al / A)
    sa = 2 * math.sqrt(A) * al
    if b["type"] == "LSC":
        return (A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c),
                A * ((A + 1) - (A - 1) * c - sa), (A + 1) + (A - 1) * c + sa,
                -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa)
    # HSC
    return (A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c),
            A * ((A + 1) + (A - 1) * c - sa), (A + 1) - (A - 1) * c + sa,
            2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa)

def band_db(b, f):
    b0, b1, b2, a0, a1, a2 = coeffs(b)
    w = 2 * math.pi * f / FS
    def h(z0, z1, z2):
        re = z0 + z1 * math.cos(w) + z2 * math.cos(2 * w)
        im = -z1 * math.sin(w) - z2 * math.sin(2 * w)
        return complex(re, im)
    return 20 * math.log10(abs(h(b0, b1, b2) / h(a0, a1, a2)))

def freqs(n=320):
    return [FMIN * (FMAX / FMIN) ** (i / (n - 1)) for i in range(n)]

def path(w, h, fn, rng=12.0):
    pts = []
    for f in freqs():
        y = h / 2 - fn(f) / rng * (h / 2)
        pts.append(f"{xlog(f, w):.1f},{y:.1f}")
    return "M" + " L".join(pts)

def sum_db(f):
    return sum(band_db(b, f) for b in BANDS)

MAJOR = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
MINOR = [30, 40, 60, 70, 80, 90, 300, 400, 600, 700, 800, 900, 3000, 4000, 6000, 7000, 8000, 9000]

def flabel(f):
    if f >= 1000:
        v = f / 1000
        return (f"{v:g}k")
    return f"{f:g}"

def fmt_hz(f):
    return f"{f:,}".replace(",", " ")  # thin-space thousands

def export_text():
    lines = [f"Preamp: {PREAMP:.1f} dB"]
    for i, b in enumerate(sorted(BANDS, key=lambda b: b["fc"]), 1):
        lines.append(f"Filter {i}: ON {b['type']} Fc {b['fc']} Hz Gain {b['gain']:.1f} dB Q {b['q']:.2f}")
    return "\n".join(lines)

# ---- shared SVG builders ---------------------------------------------------
def tape_svg(w, h, st):
    """Horizontal log-frequency tape with a needle. st = style dict."""
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="display:block">']
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{st["bg"]}"/>')
    base = h - st.get("tape_base", 22)
    for f in MINOR:
        x = xlog(f, w)
        out.append(f'<line x1="{x:.1f}" y1="{base-8}" x2="{x:.1f}" y2="{base}" stroke="{st["tick"]}" stroke-width="1"/>')
    for f in MAJOR:
        x = xlog(f, w)
        out.append(f'<line x1="{x:.1f}" y1="{base-16}" x2="{x:.1f}" y2="{base}" stroke="{st["tick_major"]}" stroke-width="1.5"/>')
        anchor = "start" if f == 20 else ("end" if f == 20000 else "middle")
        dx = 4 if f == 20 else (-4 if f == 20000 else 0)
        out.append(f'<text x="{x+dx:.1f}" y="{base+15}" text-anchor="{anchor}" font-family="{st["mono"]}" font-size="11" fill="{st["label"]}">{flabel(f)}</text>')
    # fine ticks every 1/10 decade already covered; add hairline at 1k for orientation
    xs = xlog(SWEEP_F, w)
    if st.get("needle_glow"):
        out.append(f'<line x1="{xs:.1f}" y1="6" x2="{xs:.1f}" y2="{base+2}" stroke="{ACCENT}" stroke-width="6" opacity="0.18"/>')
    out.append(f'<line x1="{xs:.1f}" y1="6" x2="{xs:.1f}" y2="{base+2}" stroke="{st["needle"]}" stroke-width="{st.get("needle_w", 2)}"/>')
    if st.get("needle_cap") == "triangle":
        out.append(f'<path d="M{xs-6:.1f},4 L{xs+6:.1f},4 L{xs:.1f},14 Z" fill="{st["needle"]}"/>')
    out.append("</svg>")
    return "".join(out)

def graph_svg(w, h, st):
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="display:block">']
    if st.get("pencil"):
        out.append('<defs><filter id="pencil" x="-2%" y="-10%" width="104%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter></defs>')
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{st["bg"]}"/>')
    # fine grid (graph paper) if requested
    if st.get("fine_grid"):
        for f in [20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,20000]:
            x = xlog(f, w)
            out.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{h}" stroke="{st["grid_fine"]}" stroke-width="1"/>')
        for db in range(-12, 13, 2):
            y = h / 2 - db / 12 * (h / 2)
            out.append(f'<line x1="0" y1="{y:.1f}" x2="{w}" y2="{y:.1f}" stroke="{st["grid_fine"]}" stroke-width="1"/>')
    for f in MAJOR:
        x = xlog(f, w)
        out.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{h}" stroke="{st["grid"]}" stroke-width="1"/>')
        anchor = "start" if f == 20 else ("end" if f == 20000 else "middle")
        dx = 4 if f == 20 else (-4 if f == 20000 else 0)
        out.append(f'<text x="{x+dx:.1f}" y="{h-6}" text-anchor="{anchor}" font-family="{st["mono"]}" font-size="10.5" fill="{st["label"]}">{flabel(f)}</text>')
    for db in (-12, -6, 0, 6, 12):
        y = h / 2 - db / 12 * (h / 2)
        sw = 1.5 if db == 0 else 1
        col = st["zero"] if db == 0 else st["grid"]
        out.append(f'<line x1="0" y1="{y:.1f}" x2="{w}" y2="{y:.1f}" stroke="{col}" stroke-width="{sw}"/>')
        if db != 0:
            out.append(f'<text x="6" y="{y-4 if db>0 else y+12:.1f}" font-family="{st["mono"]}" font-size="10.5" fill="{st["label"]}">{db:+d} dB</text>')
    # per-band ghosts
    for b in BANDS:
        out.append(f'<path d="{path(w, h, lambda f, b=b: band_db(b, f))}" fill="none" stroke="{st["ghost"]}" stroke-width="1" stroke-dasharray="{st.get("ghost_dash","3 4")}"/>')
    # sum curve fill + stroke
    p = path(w, h, sum_db)
    if st.get("fill") != "none":
        out.append(f'<path d="{p} L{w},{h/2} L0,{h/2} Z" fill="{st["fill"]}"/>')
    filt = ' filter="url(#pencil)"' if st.get("pencil") else ""
    if st.get("curve_glow"):
        out.append(f'<path d="{p}" fill="none" stroke="{ACCENT}" stroke-width="7" opacity="0.14"/>')
    out.append(f'<path d="{p}" fill="none" stroke="{st["curve"]}" stroke-width="{st.get("curve_w", 2)}" stroke-linejoin="round"{filt}/>')
    # three-point marks for band 1
    m = BANDS[0]["marks"]
    names = st.get("mark_names", ("start", "top", "end"))
    xs = [xlog(f, w) for f in m]
    ytop = st.get("mark_y", 22)
    if st.get("mark_style") == "bracket":
        out.append(f'<path d="M{xs[0]:.1f},{ytop+8} L{xs[0]:.1f},{ytop} L{xs[2]:.1f},{ytop} L{xs[2]:.1f},{ytop+8}" fill="none" stroke="{st["mark"]}" stroke-width="1.5"/>')
        out.append(f'<line x1="{xs[1]:.1f}" y1="{ytop}" x2="{xs[1]:.1f}" y2="{ytop+14}" stroke="{st["mark"]}" stroke-width="1.5"/>')
    for i, x in enumerate(xs):
        y = h / 2 - sum_db(m[i]) / 12 * (h / 2)
        if st.get("mark_style") == "dot":
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{st["mark"]}"/>')
        elif st.get("mark_style") == "x":
            out.append(f'<path d="M{x-5:.1f},{y-5:.1f} L{x+5:.1f},{y+5:.1f} M{x+5:.1f},{y-5:.1f} L{x-5:.1f},{y+5:.1f}" stroke="{st["mark"]}" stroke-width="1.6" fill="none"{filt}/>')
        else:
            out.append(f'<line x1="{x:.1f}" y1="{ytop+14}" x2="{x:.1f}" y2="{y-6:.1f}" stroke="{st["mark"]}" stroke-width="1" stroke-dasharray="2 3" opacity="0.7"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{st["bg"]}" stroke="{st["mark"]}" stroke-width="1.6"/>')
        anchor = ("end", "middle", "start")[i]
        lx = x + (-6, 0, 6)[i]
        ly = ytop - 6 if i != 1 else ytop - 20
        out.append(f'<text x="{lx:.1f}" y="{ly}" text-anchor="{anchor}" font-family="{st["mono"]}" font-size="{st.get("mark_fs", 10.5)}" font-style="{st.get("mark_italic","normal")}" fill="{st["mark"]}">{names[i]} {flabel(m[i]) if m[i] < 1000 else f"{m[i]/1000:g}k"}</text>')
    # playhead
    xp = xlog(SWEEP_F, w)
    out.append(f'<line x1="{xp:.1f}" y1="0" x2="{xp:.1f}" y2="{h}" stroke="{st["playhead"]}" stroke-width="{st.get("playhead_w",1.5)}" opacity="{st.get("playhead_op",0.9)}"/>')
    out.append("</svg>")
    return "".join(out)

def knob_svg(size, st, angle_deg=-40):
    r = size / 2
    a = math.radians(angle_deg - 90)
    x2, y2 = r + math.cos(a) * (r - 9), r + math.sin(a) * (r - 9)
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" style="display:block">'
            f'<defs><radialGradient id="kg" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="{st["knob_hi"]}"/><stop offset="1" stop-color="{st["knob_lo"]}"/></radialGradient></defs>'
            f'<circle cx="{r}" cy="{r}" r="{r-1}" fill="url(#kg)" stroke="{st["knob_edge"]}" stroke-width="1"/>'
            f'<line x1="{r}" y1="{r}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round"/>'
            f'</svg>')

def icon(name, color="currentColor", size=16):
    p = {
        "copy": '<rect x="9" y="9" width="11" height="11" rx="1.5"/><path d="M5 15H4a1.5 1.5 0 0 1-1.5-1.5V4A1.5 1.5 0 0 1 4 2.5h9.5A1.5 1.5 0 0 1 15 4v1"/>',
        "download": '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 20h16"/>',
        "stop": '<rect x="6" y="6" width="12" height="12" rx="1"/>',
        "play": '<path d="M7 4v16l13-8z"/>',
        "x": '<path d="M6 6l12 12M18 6 6 18"/>',
        "power": '<path d="M12 3v9"/><path d="M6.3 6.3a8 8 0 1 0 11.4 0"/>',
        "chev": '<path d="m6 9 6 6 6-6"/>',
        "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
        "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
        "undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
    }[name]
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{p}</svg>'

def wrap(title, fonts_href, css, body):
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <title>{title}</title>
  {f'<link rel="stylesheet" href="{fonts_href}">' if fonts_href else ''}
  <style>
{css}
  </style>
</helmet>
{body}
</x-dc>
</body>
</html>
"""

def write(name, html):
    with open(os.path.join(HERE, name), "w") as f:
        f.write(html)
    print("wrote", name, len(html))

# =============================================================================
# DIRECTION A — Bench instrument
# =============================================================================
A_FONTS = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap"
A_ST = dict(bg="#0b0c0d", tick="#4a4e52", tick_major="#8a8f94", label="#9aa0a6", mono="'IBM Plex Mono', 'Menlo', monospace",
            needle=ACCENT, needle_glow=True, grid="rgba(252,190,17,0.10)", zero="rgba(252,190,17,0.32)",
            ghost="rgba(252,190,17,0.35)", fill="rgba(252,190,17,0.07)", curve=ACCENT, curve_glow=True,
            mark="#f2f4f5", mark_y=34, playhead="#ffffff", playhead_op=0.55, knob_hi="#3a3d41", knob_lo="#1a1c1e", knob_edge="#0a0b0c")

A_CSS = f"""
    body {{ margin:0; background:#1c1e21; color:#d9dcdf; font-family:'Barlow', 'Helvetica Neue', Arial, sans-serif; font-size:14px; }}
    a {{ color:{ACCENT}; }} a:hover {{ color:#ffd65c; }}
    .page {{ width:1440px; height:900px; box-sizing:border-box; padding:24px 28px; display:flex; flex-direction:column; gap:14px;
      background:
        repeating-linear-gradient(90deg, rgba(255,255,255,0.014) 0 1px, transparent 1px 3px),
        radial-gradient(1200px 600px at 50% -10%, #2a2d32 0%, #1c1e21 60%);
    }}
    .top {{ display:flex; align-items:center; justify-content:space-between; height:44px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .brand img {{ height:34px; width:auto; display:block; filter: drop-shadow(0 1px 0 rgba(0,0,0,0.6)); }}
    .wm {{ font-family:'Barlow Condensed', 'Arial Narrow', sans-serif; font-weight:700; font-size:30px; letter-spacing:0.06em; color:#f2f4f5; line-height:1; }}
    .wm-sub {{ font-family:'Barlow Condensed', 'Arial Narrow', sans-serif; font-weight:500; font-size:30px; letter-spacing:0.06em; color:#7c8288; line-height:1; margin-left:-6px; }}
    .top-right {{ display:flex; align-items:center; gap:18px; }}
    .lamp {{ width:10px; height:10px; border-radius:50%; background:{ACCENT}; box-shadow:0 0 8px {ACCENT}, inset 0 -1px 1px rgba(0,0,0,0.4); }}
    .lamp.off {{ background:#3a3d41; box-shadow:inset 0 1px 2px rgba(0,0,0,0.6); }}
    .lamp-row {{ display:flex; align-items:center; gap:8px; }}
    .eng {{ font-family:'Barlow Condensed', sans-serif; font-weight:600; font-size:12px; letter-spacing:0.16em; text-transform:uppercase; color:#8a9096; text-shadow:0 1px 0 rgba(0,0,0,0.9); }}
    .btn {{ display:inline-flex; align-items:center; gap:8px; height:34px; padding:0 14px; border-radius:5px; border:1px solid #0b0c0d;
      background:linear-gradient(#34373b, #24272a); color:#e6e8ea; font-family:'Barlow Condensed', sans-serif; font-weight:600; font-size:14px; letter-spacing:0.12em; text-transform:uppercase;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.09), 0 2px 4px rgba(0,0,0,0.5); cursor:pointer; }}
    .btn.primary {{ background:linear-gradient(#ffd24a, #f0b000); color:#1a1300; border-color:#7a5a00; box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 2px 6px rgba(0,0,0,0.5); }}
    .btn.big {{ height:44px; padding:0 18px; font-size:15px; }}
    .panel {{ position:relative; border-radius:7px; border:1px solid #0b0c0d; background:linear-gradient(#2c3035, #23262a);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.07), inset 0 -1px 0 rgba(0,0,0,0.5), 0 10px 26px rgba(0,0,0,0.45); padding:16px 18px; box-sizing:border-box; }}
    .plabel {{ position:absolute; top:-1px; left:18px; transform:translateY(-50%); padding:0 8px; background:#25282c; font-family:'Barlow Condensed', sans-serif; font-weight:600; font-size:11px; letter-spacing:0.2em; text-transform:uppercase; color:#8b9197; text-shadow:0 1px 0 rgba(0,0,0,0.9); border-radius:3px; }}
    .strip {{ height:156px; display:flex; align-items:stretch; gap:18px; }}
    .tape {{ flex:1 1 auto; border:1px solid #060707; border-radius:4px; overflow:hidden; box-shadow: inset 0 2px 8px rgba(0,0,0,0.8); }}
    .readout {{ display:flex; flex-direction:column; align-items:flex-end; justify-content:center; gap:4px; width:210px; }}
    .ro-win {{ width:100%; box-sizing:border-box; height:64px; display:flex; align-items:baseline; justify-content:flex-end; gap:8px; padding:0 14px; border-radius:4px; background:#070808; border:1px solid #000;
      box-shadow: inset 0 2px 10px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.05); font-family:'IBM Plex Mono', monospace; font-size:40px; font-weight:500; color:{ACCENT}; text-shadow:0 0 12px rgba(252,190,17,0.45); letter-spacing:0.02em; }}
    .ro-win small {{ font-size:15px; color:#b98c0a; text-shadow:none; }}
    .ro-note {{ font-family:'IBM Plex Mono', monospace; font-size:11px; color:#6e747a; letter-spacing:0.04em; }}
    .ctl {{ display:flex; align-items:center; gap:22px; padding-left:18px; border-left:1px solid #0b0c0d; box-shadow:inset 1px 0 0 rgba(255,255,255,0.05); }}
    .ctl-col {{ display:flex; flex-direction:column; align-items:center; gap:8px; }}
    .ctl-val {{ font-family:'IBM Plex Mono', monospace; font-size:12px; color:#c6cacd; }}
    .row {{ display:flex; gap:14px; flex:1 1 auto; min-height:0; }}
    .graph {{ flex:1 1 auto; display:flex; flex-direction:column; }}
    .screen {{ flex:1 1 auto; border:1px solid #060707; border-radius:4px; overflow:hidden; box-shadow: inset 0 2px 10px rgba(0,0,0,0.85); }}
    .col {{ width:432px; display:flex; flex-direction:column; gap:14px; }}
    .markrow {{ display:flex; gap:10px; margin-top:6px; }}
    .mk {{ flex:1 1 0; height:58px; border-radius:5px; border:1px solid #0b0c0d; background:linear-gradient(#34373b, #24272a); box-shadow: inset 0 1px 0 rgba(255,255,255,0.09), 0 2px 4px rgba(0,0,0,0.5);
      display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3px; cursor:pointer; }}
    .mk b {{ font-family:'Barlow Condensed', sans-serif; font-weight:600; font-size:14px; letter-spacing:0.14em; text-transform:uppercase; color:#e6e8ea; }}
    .mk span {{ font-family:'IBM Plex Mono', monospace; font-size:10px; color:#7c8288; }}
    .mk.dip b {{ color:#9aa0a6; }}
    .hint {{ margin-top:10px; display:flex; justify-content:space-between; align-items:center; font-family:'IBM Plex Mono', monospace; font-size:11px; color:#6e747a; }}
    .bands {{ flex:1 1 auto; display:flex; flex-direction:column; gap:8px; padding-top:20px; }}
    .band {{ display:grid; grid-template-columns: 22px 44px 62px minmax(0,1fr) minmax(0,1fr) 30px 18px; align-items:center; gap:10px; height:44px; padding:0 10px; border-radius:4px; background:#141618; border:1px solid #0a0b0c; box-shadow: inset 0 1px 0 rgba(255,255,255,0.03); }}
    .band.active {{ box-shadow: inset 0 0 0 1px rgba(252,190,17,0.55), inset 0 1px 0 rgba(255,255,255,0.03); }}
    .bn {{ font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:14px; color:#7c8288; }}
    .bt {{ font-family:'Barlow Condensed', sans-serif; font-weight:600; font-size:11px; letter-spacing:0.12em; color:#c6cacd; background:#26292c; border:1px solid #0b0c0d; border-radius:3px; padding:3px 0; text-align:center; }}
    .bf {{ font-family:'IBM Plex Mono', monospace; font-size:13px; color:#e6e8ea; }}
    .sl {{ display:flex; flex-direction:column; gap:4px; }}
    .sl label {{ font-family:'Barlow Condensed', sans-serif; font-size:10px; letter-spacing:0.14em; text-transform:uppercase; color:#6e747a; display:flex; justify-content:space-between; }}
    .sl label span {{ font-family:'IBM Plex Mono', monospace; color:#c6cacd; letter-spacing:0; text-transform:none; }}
    .track {{ position:relative; height:4px; border-radius:2px; background:#0a0b0c; box-shadow: inset 0 1px 2px rgba(0,0,0,0.9); }}
    .fill {{ position:absolute; top:0; bottom:0; background:{ACCENT}; border-radius:2px; }}
    .thumb {{ position:absolute; top:50%; width:12px; height:12px; margin:-6px 0 0 -6px; border-radius:50%; background:linear-gradient(#4a4e53, #2a2d31); border:1px solid #060707; box-shadow:0 1px 2px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.15); }}
    .sw {{ width:30px; height:16px; border-radius:8px; background:{ACCENT}; box-shadow: inset 0 1px 2px rgba(0,0,0,0.4); position:relative; }}
    .sw::after {{ content:""; position:absolute; top:2px; right:2px; width:12px; height:12px; border-radius:50%; background:#fff5d6; box-shadow:0 1px 2px rgba(0,0,0,0.5); }}
    .sw.off {{ background:#2a2d31; }} .sw.off::after {{ right:auto; left:2px; background:#8a8f94; }}
    .empty {{ height:44px; border-radius:4px; border:1px dashed #33373b; display:flex; align-items:center; padding:0 12px; font-family:'IBM Plex Mono', monospace; font-size:11px; color:#4f545a; }}
    .export {{ height:118px; display:flex; gap:18px; align-items:stretch; }}
    .pre {{ flex:1 1 auto; margin:0; padding:10px 14px; border-radius:4px; background:#0b0c0d; border:1px solid #000; box-shadow: inset 0 2px 8px rgba(0,0,0,0.8); font-family:'IBM Plex Mono', monospace; font-size:11.5px; line-height:1.55; color:#b9bec2; white-space:pre; overflow:hidden; }}
    .pre b {{ color:{ACCENT}; font-weight:500; }}
    .ex-col {{ display:flex; flex-direction:column; gap:10px; justify-content:center; width:190px; }}
    .preamp {{ display:flex; align-items:center; justify-content:space-between; font-family:'Barlow Condensed', sans-serif; font-size:12px; letter-spacing:0.14em; text-transform:uppercase; color:#8b9197; }}
    .preamp span {{ font-family:'IBM Plex Mono', monospace; font-size:14px; color:#e6e8ea; letter-spacing:0; text-transform:none; background:#0b0c0d; border:1px solid #000; border-radius:3px; padding:4px 8px; }}
"""

def slider(label, val, pct):
    return (f'<div class="sl"><label>{label}<span>{val}</span></label>'
            f'<div class="track"><div class="fill" style="left:0; width:{pct}%"></div><div class="thumb" style="left:{pct}%"></div></div></div>')

def a_band(b, active=False):
    gpct = (b["gain"] + 12) / 24 * 100
    qpct = (math.log(b["q"] / 0.3) / math.log(10 / 0.3)) * 100
    fc = fmt_hz(b["fc"])
    return (f'<div class="band{" active" if active else ""}"><div class="bn">{b["n"]}</div><div class="bt">{b["type"]}</div><div class="bf">{fc}</div>'
            f'{slider("Gain", f"{b['gain']:+.1f} dB", gpct)}{slider("Q", f"{b['q']:.2f}", qpct)}'
            f'<div class="sw"></div><div style="color:#5a6066; display:flex; align-items:center">{icon("x","#5a6066",14)}</div></div>')

def build_a():
    tape = tape_svg(884, 122, A_ST)
    graph = graph_svg(892, 450, A_ST)
    exp = export_text().replace("Preamp", "<b>Preamp</b>")
    body = f"""
<div class="page">
  <div class="top">
    <div class="brand"><img src="dms-mark.png" alt="DMS"><span class="wm">DMS</span><span class="wm-sub">Sweep</span></div>
    <div class="top-right">
      <div class="lamp-row"><div class="lamp"></div><span class="eng">EQ engaged</span></div>
      <div class="lamp-row"><div class="lamp"></div><span class="eng">Tone</span></div>
      <button class="btn">{icon("download","#e6e8ea",15)} Export</button>
    </div>
  </div>

  <div class="panel strip">
    <div class="plabel">Sweep · drag to move the tone</div>
    <div class="tape">{tape}</div>
    <div class="readout">
      <div class="ro-win">{fmt_hz(SWEEP_F)}<small>Hz</small></div>
      <div class="ro-note">← → nudge · shift for coarse · space stop</div>
    </div>
    <div class="ctl">
      <div class="ctl-col">{knob_svg(56, A_ST, -40)}<div class="ctl-val">{LEVEL_DB} dB</div></div>
      <button class="btn big">{icon("stop","#e6e8ea",16)} Stop</button>
    </div>
  </div>

  <div class="row">
    <div class="panel graph">
      <div class="plabel">Response</div>
      <div class="screen">{graph}</div>
    </div>
    <div class="col">
      <div class="panel">
        <div class="plabel">Mark</div>
        <div class="markrow">
          <div class="mk"><b>Start</b><span>key 1</span></div>
          <div class="mk"><b>Top</b><span>key 2</span></div>
          <div class="mk"><b>End</b><span>key 3</span></div>
        </div>
        <div class="hint"><span>Peak by default · hold D for a dip</span><span style="display:flex;gap:6px;align-items:center">{icon("undo","#6e747a",13)} undo</span></div>
      </div>
      <div class="panel bands">
        <div class="plabel">Bands · 3 of 8</div>
        {a_band(BANDS[0], True)}{a_band(BANDS[1])}{a_band(BANDS[2])}
        <div class="empty">4 · mark three points to add</div>
      </div>
    </div>
  </div>

  <div class="panel export">
    <div class="plabel">Parametric EQ · generic 8-band</div>
    <pre class="pre">{exp}</pre>
    <div class="ex-col">
      <div class="preamp">Preamp <span>{PREAMP:.1f} dB</span></div>
      <button class="btn primary">{icon("copy","#1a1300",15)} Copy</button>
      <button class="btn">{icon("download","#e6e8ea",15)} Download .txt</button>
    </div>
  </div>
</div>
"""
    write("BenchInstrument.dc.html", wrap("A · Bench instrument", A_FONTS, A_CSS, body))

def build_a_warn():
    body = f"""
<div style="width:720px; height:460px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; background:radial-gradient(800px 400px at 50% 0%, #202226 0%, #151618 70%); font-family:'Barlow', sans-serif;">
  <div class="panel" style="width:520px; padding:26px 28px 24px; display:flex; flex-direction:column; gap:18px;">
    <div class="plabel">Before you start</div>
    <div style="display:flex; gap:16px; align-items:flex-start;">
      <img src="dms-mark.png" alt="DMS" style="height:56px; width:auto; display:block; margin-top:2px;">
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div style="font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:28px; letter-spacing:0.03em; color:#f2f4f5; line-height:1.05;">Turn your volume down first.</div>
        <div style="font-size:14.5px; line-height:1.5; color:#b9bec2;">Sine tones at high level can damage hearing and equipment. Start quiet, then raise the level to where you normally listen to music.</div>
      </div>
    </div>
    <div style="display:flex; align-items:center; justify-content:space-between; padding-top:6px; border-top:1px solid #0b0c0d; box-shadow:inset 0 1px 0 rgba(255,255,255,0.05);">
      <div style="display:flex; align-items:center; gap:14px;">{knob_svg(44, A_ST, -120)}<div><div class="eng">Level</div><div class="ctl-val" style="margin-top:2px;">−40 dB</div></div></div>
      <button class="btn primary big">{icon("power","#1a1300",16)} I understand · start</button>
    </div>
  </div>
</div>
"""
    write("WarnBench.dc.html", wrap("A · first-run warning", A_FONTS, A_CSS, body))

# =============================================================================
# DIRECTION B — Lab notebook
# =============================================================================
B_FONTS = "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Libre+Franklin:wght@400;500;600&display=swap"
B_MONO = "'Courier Prime', 'Courier New', monospace"
B_ST = dict(bg="#25211d", tick="#57504a", tick_major="#a39a90", label="#a39a90", mono=B_MONO,
            needle="#f4efe6", needle_w=1.5, needle_cap="triangle",
            fine_grid=True, grid_fine="rgba(252,190,17,0.045)", grid="rgba(252,190,17,0.16)", zero="rgba(244,239,230,0.35)",
            ghost="rgba(244,239,230,0.35)", ghost_dash="1 3", fill="rgba(252,190,17,0.08)", curve=ACCENT, curve_w=2.2, pencil=True,
            mark="#f4efe6", mark_style="x", mark_y=34, mark_italic="italic", mark_fs=12, mark_names=("start", "top", "end"),
            playhead="#f4efe6", playhead_w=1, playhead_op=0.5)

B_CSS = f"""
    body {{ margin:0; background:#1a1714; color:#e9e3d8; font-family:'Libre Franklin', 'Helvetica Neue', Arial, sans-serif; font-size:13.5px; }}
    a {{ color:{ACCENT}; }} a:hover {{ color:#ffd65c; }}
    .page {{ position:relative; width:1440px; height:900px; box-sizing:border-box; padding:40px 44px 36px; background:#1a1714; overflow:hidden; }}
    .grain {{ position:absolute; inset:0; pointer-events:none; opacity:0.5; }}
    .sheet {{ position:relative; background:#25211d; border:1px solid rgba(255,255,255,0.045); box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 18px 40px rgba(0,0,0,0.45); }}
    .sheet::before {{ content:""; position:absolute; inset:-1px; transform:translate(9px, 9px); background:#2c2722; border:1px solid rgba(255,255,255,0.04); z-index:-1; }}
    .sheet::after {{ content:""; position:absolute; inset:-1px; transform:translate(18px, 18px); background:#211d19; border:1px solid rgba(255,255,255,0.03); z-index:-2; }}
    .head {{ display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:26px; }}
    .brand {{ display:flex; align-items:flex-end; gap:16px; }}
    .brand img {{ height:44px; width:auto; display:block; }}
    .title {{ font-family:'Instrument Serif', 'Georgia', serif; font-size:44px; line-height:0.95; color:#f4efe6; letter-spacing:-0.01em; }}
    .title i {{ color:{ACCENT}; }}
    .meta {{ font-family:{B_MONO}; font-size:12px; color:#9a9187; text-align:right; line-height:1.6; }}
    .meta b {{ color:#f4efe6; font-weight:400; }}
    .lab {{ font-family:'Libre Franklin', sans-serif; font-weight:600; font-size:10.5px; letter-spacing:0.18em; text-transform:uppercase; color:#8f8479; }}
    .strip {{ display:grid; grid-template-columns: minmax(0,1fr) 300px; gap:28px; padding:18px 22px 16px; margin-bottom:22px; }}
    .strip-l {{ display:flex; flex-direction:column; gap:8px; }}
    .ruler {{ border:1px solid rgba(255,255,255,0.06); background:#25211d; }}
    .strip-r {{ display:flex; flex-direction:column; justify-content:center; gap:10px; border-left:1px dashed rgba(244,239,230,0.18); padding-left:26px; }}
    .big {{ font-family:'Instrument Serif', serif; font-size:64px; line-height:0.9; color:#f4efe6; letter-spacing:-0.01em; }}
    .big i {{ font-size:26px; color:{ACCENT}; margin-left:6px; }}
    .key {{ font-family:{B_MONO}; font-size:12px; color:#9a9187; }}
    .ctl {{ display:flex; align-items:center; gap:18px; margin-top:6px; }}
    .lvl {{ display:flex; align-items:center; gap:10px; font-family:{B_MONO}; font-size:13px; color:#e9e3d8; }}
    .lvl .bar {{ width:110px; height:2px; background:rgba(244,239,230,0.2); position:relative; }}
    .lvl .bar::after {{ content:""; position:absolute; left:62%; top:-5px; width:12px; height:12px; border-radius:50%; background:{ACCENT}; box-shadow:0 0 0 3px #25211d; }}
    .lnk {{ font-family:'Libre Franklin', sans-serif; font-weight:500; font-size:12.5px; color:#f4efe6; border-bottom:1.5px solid {ACCENT}; padding-bottom:1px; display:inline-flex; align-items:center; gap:6px; cursor:pointer; }}
    .row {{ display:grid; grid-template-columns: minmax(0,1fr) 400px; gap:28px; margin-bottom:22px; }}
    .graph {{ padding:18px 22px 16px; display:flex; flex-direction:column; gap:10px; }}
    .aside {{ display:flex; flex-direction:column; gap:22px; }}
    .marks {{ padding:18px 22px 16px; }}
    .markrow {{ display:flex; gap:10px; margin-top:12px; }}
    .mk {{ flex:1 1 0; height:52px; border:1px solid rgba(244,239,230,0.22); display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px; cursor:pointer; background:transparent; }}
    .mk:first-child {{ border-color:{ACCENT}; }}
    .mk b {{ font-family:'Instrument Serif', serif; font-weight:400; font-size:20px; color:#f4efe6; line-height:1; }}
    .mk span {{ font-family:{B_MONO}; font-size:10.5px; color:#9a9187; }}
    .note {{ font-family:{B_MONO}; font-size:11.5px; color:#9a9187; margin-top:12px; font-style:italic; }}
    .bands {{ padding:18px 22px 14px; flex:1 1 auto; }}
    table {{ border-collapse:collapse; width:100%; margin-top:10px; }}
    th {{ text-align:left; font-family:'Libre Franklin', sans-serif; font-weight:600; font-size:10px; letter-spacing:0.16em; text-transform:uppercase; color:#8f8479; padding:0 6px 8px 0; border-bottom:1px solid rgba(244,239,230,0.25); }}
    td {{ font-family:{B_MONO}; font-size:13px; color:#e9e3d8; padding:9px 6px 9px 0; border-bottom:1px dashed rgba(244,239,230,0.14); vertical-align:middle; }}
    td.n {{ color:#8f8479; width:18px; }}
    td.g {{ color:{ACCENT}; }}
    td.on {{ width:26px; text-align:right; }}
    tr.active td {{ background:linear-gradient(90deg, rgba(252,190,17,0.10), transparent 70%); }}
    tr.empty td {{ color:#5c554e; font-style:italic; border-bottom:none; }}
    .dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; background:{ACCENT}; }}
    .export {{ padding:18px 22px 16px; display:grid; grid-template-columns: minmax(0,1fr) 240px; gap:28px; }}
    .pre {{ margin:8px 0 0; font-family:{B_MONO}; font-size:12px; line-height:1.55; color:#e9e3d8; white-space:pre; }}
    .pre b {{ color:{ACCENT}; font-weight:400; }}
    .ex-r {{ display:flex; flex-direction:column; justify-content:center; gap:14px; border-left:1px dashed rgba(244,239,230,0.18); padding-left:26px; }}
    .pill {{ display:inline-flex; align-items:center; gap:8px; height:38px; padding:0 16px; border:1px solid {ACCENT}; color:{ACCENT}; font-family:'Libre Franklin', sans-serif; font-weight:600; font-size:12.5px; letter-spacing:0.04em; cursor:pointer; }}
    .pill.solid {{ background:{ACCENT}; color:#1a1300; }}
"""

GRAIN = ('<svg class="grain" xmlns="http://www.w3.org/2000/svg"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch"/>'
         '<feColorMatrix values="0 0 0 0 0.9  0 0 0 0 0.85  0 0 0 0 0.75  0 0 0 0.07 0"/></filter><rect width="100%" height="100%" filter="url(#g)"/></svg>')

def b_row(b, active=False):
    return (f'<tr class="{"active" if active else ""}"><td class="n">{b["n"]}</td><td>{b["type"]}</td><td>{fmt_hz(b["fc"])} Hz</td>'
            f'<td class="g">{b["gain"]:+.1f} dB</td><td>Q {b["q"]:.2f}</td><td class="on"><span class="dot"></span></td></tr>')

def build_b():
    tape = tape_svg(970, 104, B_ST)
    graph = graph_svg(880, 366, B_ST)
    exp = export_text().replace("Preamp", "<b>Preamp</b>")
    body = f"""
<div class="page">
  {GRAIN}
  <div class="head">
    <div class="brand"><img src="dms-mark.png" alt="DMS"><div class="title">DMS <i>Sweep</i></div></div>
    <div class="meta">tone <b>playing</b> · eq <b>engaged</b><br>session autosaved · <span style="border-bottom:1px solid {ACCENT}; color:#f4efe6">export</span></div>
  </div>

  <div class="sheet strip">
    <div class="strip-l">
      <div class="lab">Sweep — drag slowly along the ruler</div>
      <div class="ruler">{tape}</div>
    </div>
    <div class="strip-r">
      <div class="big">{fmt_hz(SWEEP_F)}<i>Hz</i></div>
      <div class="key">← → nudge · shift coarse · space stop</div>
      <div class="ctl">
        <div class="lvl">level <div class="bar"></div> {LEVEL_DB} dB</div>
        <span class="lnk">{icon("stop","#f4efe6",13)} stop</span>
      </div>
    </div>
  </div>

  <div class="row">
    <div class="sheet graph">
      <div class="lab">Response · 20 Hz – 20 kHz · ±12 dB</div>
      <div style="border:1px solid rgba(255,255,255,0.06)">{graph}</div>
    </div>
    <div class="aside">
      <div class="sheet marks">
        <div class="lab">Mark the peak you hear</div>
        <div class="markrow">
          <div class="mk"><b>start</b><span>1</span></div>
          <div class="mk"><b>top</b><span>2</span></div>
          <div class="mk"><b>end</b><span>3</span></div>
        </div>
        <div class="note">peak by default · hold d to mark a dip · z undoes</div>
      </div>
      <div class="sheet bands">
        <div class="lab">Bands · 3 of 8</div>
        <table>
          <tr><th></th><th>type</th><th>centre</th><th>gain</th><th>width</th><th></th></tr>
          {b_row(BANDS[0], True)}{b_row(BANDS[1])}{b_row(BANDS[2])}
          <tr class="empty"><td class="n">4</td><td colspan="5">mark three points to add the next</td></tr>
        </table>
      </div>
    </div>
  </div>

  <div class="sheet export">
    <div>
      <div class="lab">Parametric EQ · generic 8-band</div>
      <pre class="pre">{exp}</pre>
    </div>
    <div class="ex-r">
      <div class="lab" style="display:flex; justify-content:space-between; align-items:center">preamp <span style="font-family:{B_MONO}; font-size:14px; color:#f4efe6; letter-spacing:0; text-transform:none">{PREAMP:.1f} dB</span></div>
      <span class="pill solid">{icon("copy","#1a1300",14)} Copy</span>
      <span class="pill">{icon("download",ACCENT,14)} Download .txt</span>
    </div>
  </div>
</div>
"""
    write("LabNotebook.dc.html", wrap("B · Lab notebook", B_FONTS, B_CSS, body))

def build_b_warn():
    body = f"""
<div style="position:relative; width:720px; height:460px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; background:#1a1714; font-family:'Libre Franklin', sans-serif; overflow:hidden;">
  {GRAIN}
  <div class="sheet" style="width:500px; padding:28px 30px 26px; display:flex; flex-direction:column; gap:16px;">
    <div class="lab">Before you start</div>
    <div style="font-family:'Instrument Serif', serif; font-size:38px; line-height:1; color:#f4efe6;">Turn your volume <i style="color:{ACCENT}">down</i> first.</div>
    <div style="font-size:14px; line-height:1.55; color:#cfc7bb;">Sine tones at high level can damage hearing and equipment. Start quiet, then raise the level to where you normally listen to music.</div>
    <div style="display:flex; align-items:center; justify-content:space-between; padding-top:14px; border-top:1px dashed rgba(244,239,230,0.2);">
      <div class="lvl">level <div class="bar" style="--x:10%"></div> −40 dB</div>
      <span class="pill solid">{icon("power","#1a1300",14)} I understand — start</span>
    </div>
  </div>
</div>
"""
    write("WarnNotebook.dc.html", wrap("B · first-run warning", B_FONTS, B_CSS, body))

# =============================================================================
# DIRECTION C — Broadcast console
# =============================================================================
C_FONTS = "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&family=Manrope:wght@400;500;600&display=swap"
C_MONO = "'Share Tech Mono', 'Menlo', monospace"
C_ST = dict(bg="#000000", tick="#3a3a3d", tick_major="#c48f00", label="#c48f00", mono=C_MONO,
            needle="#fff1c2", needle_w=2, needle_glow=True,
            grid="rgba(252,190,17,0.13)", zero="rgba(252,190,17,0.45)",
            ghost="rgba(252,190,17,0.28)", ghost_dash="2 3", fill="rgba(252,190,17,0.10)", curve=ACCENT, curve_w=2, curve_glow=True,
            mark=ACCENT, mark_style="bracket", mark_y=36, mark_names=("START", "TOP", "END"),
            playhead="#ffffff", playhead_w=1.5, playhead_op=0.8)

C_CSS = f"""
    body {{ margin:0; background:#09090a; color:#e4e4e6; font-family:'Manrope', 'Helvetica Neue', Arial, sans-serif; font-size:13px; }}
    a {{ color:{ACCENT}; }} a:hover {{ color:#ffd65c; }}
    .page {{ width:1440px; height:900px; box-sizing:border-box; padding:16px; display:grid; grid-template-columns: minmax(0,1fr) 420px; grid-template-rows: 48px 172px minmax(0,1fr) 128px; gap:12px; background:#09090a; }}
    .mod {{ position:relative; background:#141416; border:1px solid #232326; border-top-color:#2c2c30; box-shadow: 0 2px 0 #000, 0 14px 30px rgba(0,0,0,0.6); box-sizing:border-box; padding:14px 16px 14px; display:flex; flex-direction:column; gap:10px; min-height:0; }}
    .mh {{ display:flex; align-items:center; justify-content:space-between; }}
    .mt {{ font-family:'Bebas Neue', 'Impact', sans-serif; font-size:16px; letter-spacing:0.14em; color:#d9d9dc; line-height:1; display:flex; align-items:center; gap:10px; }}
    .mt::before {{ content:""; width:14px; height:3px; background:{ACCENT}; }}
    .ms {{ font-family:{C_MONO}; font-size:11px; color:#7d7d84; letter-spacing:0.04em; }}
    .bar {{ grid-column:1 / -1; background:#0e0e10; border:1px solid #232326; display:flex; align-items:center; justify-content:space-between; padding:0 16px; box-sizing:border-box; }}
    .brand {{ display:flex; align-items:center; gap:12px; }}
    .brand img {{ height:30px; width:auto; display:block; }}
    .wm {{ font-family:'Bebas Neue', sans-serif; font-size:30px; letter-spacing:0.12em; color:#ffffff; line-height:1; }}
    .wm span {{ color:{ACCENT}; }}
    .stat {{ display:flex; align-items:center; gap:22px; }}
    .led {{ display:flex; align-items:center; gap:8px; font-family:{C_MONO}; font-size:11.5px; color:#a5a5ab; letter-spacing:0.06em; }}
    .led i {{ width:8px; height:8px; background:{ACCENT}; box-shadow:0 0 6px {ACCENT}; display:inline-block; }}
    .led.off i {{ background:#2a2a2e; box-shadow:none; }}
    .b {{ display:inline-flex; align-items:center; justify-content:center; gap:8px; height:32px; padding:0 14px; border:1px solid #3a3a3f; background:#1c1c1f; color:#e4e4e6; font-family:'Bebas Neue', sans-serif; font-size:15px; letter-spacing:0.12em; cursor:pointer; box-shadow: 0 2px 0 #000; }}
    .b.amber {{ background:{ACCENT}; border-color:{ACCENT}; color:#1a1300; }}
    .b.stop {{ width:96px; height:96px; flex-direction:column; font-size:22px; border:2px solid {ACCENT}; background:#0b0b0c; color:{ACCENT}; box-shadow: 0 0 0 1px #000, 0 3px 0 #000, inset 0 0 24px rgba(252,190,17,0.08); }}
    .sweep {{ grid-column:1 / -1; }}
    .sweep-body {{ display:grid; grid-template-columns: minmax(0,1fr) 250px 112px; gap:16px; flex:1 1 auto; min-height:0; align-items:stretch; }}
    .win {{ background:#000; border:1px solid #2a2a2e; box-shadow: inset 0 0 0 1px #000, inset 0 0 24px rgba(0,0,0,0.9); overflow:hidden; }}
    .ro {{ display:flex; flex-direction:column; gap:8px; }}
    .seg {{ background:#000; border:1px solid #2a2a2e; height:66px; display:flex; align-items:baseline; justify-content:flex-end; gap:8px; padding:0 14px; box-sizing:border-box; font-family:{C_MONO}; font-size:46px; color:{ACCENT}; text-shadow:0 0 14px rgba(252,190,17,0.55); }}
    .seg small {{ font-size:14px; color:#c48f00; text-shadow:none; }}
    .meter {{ display:flex; flex-direction:column; gap:6px; }}
    .meter .row {{ display:flex; gap:3px; }}
    .meter .row i {{ flex:1 1 0; height:9px; background:#26261f; }}
    .meter .row i.on {{ background:{ACCENT}; box-shadow:0 0 5px rgba(252,190,17,0.6); }}
    .meter .row i.hot {{ background:#ffe08a; }}
    .meter .lab {{ display:flex; justify-content:space-between; font-family:{C_MONO}; font-size:10.5px; color:#7d7d84; }}
    .resp {{ grid-column:1; grid-row:3; }}
    .side {{ grid-column:2; grid-row:3; display:flex; flex-direction:column; gap:12px; min-height:0; }}
    .markrow {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; }}
    .mk {{ height:56px; border:1px solid #3a3a3f; background:#1c1c1f; box-shadow: 0 2px 0 #000; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3px; cursor:pointer; }}
    .mk b {{ font-family:'Bebas Neue', sans-serif; font-weight:400; font-size:18px; letter-spacing:0.12em; color:#e4e4e6; line-height:1; }}
    .mk span {{ font-family:{C_MONO}; font-size:10.5px; color:#7d7d84; }}
    .mk.armed {{ border-color:{ACCENT}; box-shadow: 0 2px 0 #000, inset 0 0 0 1px rgba(252,190,17,0.4); }}
    .bands {{ flex:1 1 auto; }}
    .bl {{ display:flex; flex-direction:column; gap:6px; }}
    .band {{ display:grid; grid-template-columns: 18px 42px 70px 74px 60px 26px; align-items:center; gap:8px; height:40px; padding:0 10px; background:#0e0e10; border:1px solid #232326; }}
    .band.active {{ border-color:{ACCENT}; }}
    .bn {{ font-family:'Bebas Neue', sans-serif; font-size:16px; color:#7d7d84; }}
    .bt {{ font-family:'Bebas Neue', sans-serif; font-size:14px; letter-spacing:0.1em; color:#e4e4e6; }}
    .bv {{ font-family:{C_MONO}; font-size:13px; color:#e4e4e6; background:#000; border:1px solid #2a2a2e; padding:5px 8px; box-sizing:border-box; text-align:right; }}
    .bv.g {{ color:{ACCENT}; }}
    .tg {{ width:26px; height:14px; background:{ACCENT}; position:relative; }}
    .tg::after {{ content:""; position:absolute; top:2px; right:2px; width:10px; height:10px; background:#1a1300; }}
    .empty {{ height:40px; border:1px dashed #2c2c30; display:flex; align-items:center; padding:0 10px; font-family:{C_MONO}; font-size:11px; color:#55555c; }}
    .export {{ grid-column:1 / -1; grid-row:4; flex-direction:row; align-items:stretch; gap:16px; }}
    .export .mh {{ flex-direction:column; align-items:flex-start; justify-content:space-between; width:220px; }}
    .pre {{ flex:1 1 auto; margin:0; padding:10px 14px; background:#000; border:1px solid #2a2a2e; font-family:{C_MONO}; font-size:12px; line-height:1.5; color:#c9c9cf; white-space:pre; overflow:hidden; }}
    .pre b {{ color:{ACCENT}; font-weight:400; }}
    .ex-btns {{ display:flex; flex-direction:column; gap:8px; justify-content:center; width:170px; }}
    .pa {{ display:flex; align-items:center; gap:10px; font-family:{C_MONO}; font-size:11.5px; color:#7d7d84; }}
    .pa span {{ color:#e4e4e6; background:#000; border:1px solid #2a2a2e; padding:5px 8px; font-size:13px; }}
"""

def c_meter():
    rows = []
    n = 24
    lit = 15
    segs = "".join(f'<i class="{"hot" if i >= 21 and i < lit else ("on" if i < lit else "")}"></i>' for i in range(n))
    return (f'<div class="meter"><div class="lab"><span>LEVEL</span><span>{LEVEL_DB} dB</span></div><div class="row">{segs}</div>'
            f'<div class="lab"><span>−40</span><span>−20</span><span>−6</span></div></div>')

def c_band(b, active=False):
    return (f'<div class="band{" active" if active else ""}"><div class="bn">{b["n"]}</div><div class="bt">{b["type"]}</div>'
            f'<div class="bv">{fmt_hz(b["fc"])}</div><div class="bv g">{b["gain"]:+.1f} dB</div><div class="bv">Q {b["q"]:.1f}</div><div class="tg"></div></div>')

def build_c():
    tape = tape_svg(980, 118, C_ST)
    graph = graph_svg(942, 428, C_ST)
    exp = export_text().replace("Preamp", "<b>Preamp</b>")
    body = f"""
<div class="page">
  <div class="bar">
    <div class="brand"><img src="dms-mark.png" alt="DMS"><div class="wm">DMS <span>SWEEP</span></div></div>
    <div class="stat">
      <div class="led"><i></i>TONE</div>
      <div class="led"><i></i>EQ ENGAGED</div>
      <div class="led off"><i></i>SAVED</div>
      <span class="b">{icon("download","#e4e4e6",14)} EXPORT</span>
    </div>
  </div>

  <div class="mod sweep">
    <div class="mh"><div class="mt">SWEEP</div><div class="ms">DRAG · ← → NUDGE · SHIFT COARSE · SPACE STOP</div></div>
    <div class="sweep-body">
      <div class="win">{tape}</div>
      <div class="ro">
        <div class="seg">{fmt_hz(SWEEP_F)}<small>Hz</small></div>
        {c_meter()}
      </div>
      <span class="b stop">{icon("stop",ACCENT,26)} STOP</span>
    </div>
  </div>

  <div class="mod resp">
    <div class="mh"><div class="mt">RESPONSE</div><div class="ms">20 Hz – 20 kHz · ±12 dB · SUM + BANDS</div></div>
    <div class="win" style="flex:1 1 auto">{graph}</div>
  </div>

  <div class="side">
    <div class="mod">
      <div class="mh"><div class="mt">MARK</div><div class="ms">PEAK · HOLD D FOR DIP</div></div>
      <div class="markrow">
        <div class="mk armed"><b>START</b><span>1</span></div>
        <div class="mk"><b>TOP</b><span>2</span></div>
        <div class="mk"><b>END</b><span>3</span></div>
      </div>
    </div>
    <div class="mod bands">
      <div class="mh"><div class="mt">BANDS</div><div class="ms">3 / 8</div></div>
      <div class="bl">
        {c_band(BANDS[0], True)}{c_band(BANDS[1])}{c_band(BANDS[2])}
        <div class="empty">4 · MARK THREE POINTS TO ADD</div>
      </div>
    </div>
  </div>

  <div class="mod export">
    <div class="mh"><div class="mt">PARAMETRIC EQ</div><div class="pa">PREAMP <span>{PREAMP:.1f} dB</span></div><div class="ms">GENERIC 8-BAND · TEXT</div></div>
    <pre class="pre">{exp}</pre>
    <div class="ex-btns">
      <span class="b amber">{icon("copy","#1a1300",14)} COPY</span>
      <span class="b">{icon("download","#e4e4e6",14)} DOWNLOAD .TXT</span>
    </div>
  </div>
</div>
"""
    write("BroadcastConsole.dc.html", wrap("C · Broadcast console", C_FONTS, C_CSS, body))

def build_c_warn():
    body = f"""
<div style="width:720px; height:460px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; background:#09090a; font-family:'Manrope', sans-serif;">
  <div class="mod" style="width:520px; padding:18px 20px 20px; gap:14px;">
    <div class="mh"><div class="mt">BEFORE YOU START</div><div class="ms">FIRST RUN</div></div>
    <div style="display:flex; gap:18px; align-items:center;">
      <img src="dms-mark.png" alt="DMS" style="height:64px; width:auto; display:block;">
      <div style="font-family:'Bebas Neue', sans-serif; font-size:40px; letter-spacing:0.04em; line-height:0.95; color:#ffffff;">TURN YOUR<br>VOLUME <span style="color:{ACCENT}">DOWN</span> FIRST.</div>
    </div>
    <div style="font-size:13.5px; line-height:1.55; color:#b5b5bb;">Sine tones at high level can damage hearing and equipment. Start quiet, then raise the level to where you normally listen to music.</div>
    <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:20px; padding-top:12px; border-top:1px solid #232326;">
      <div style="width:230px">{c_meter().replace(f"{LEVEL_DB} dB", "−40 dB").replace('class="on"', 'class=""').replace('class="hot"', 'class=""')}</div>
      <span class="b amber" style="height:40px; padding:0 18px; font-size:16px;">{icon("power","#1a1300",15)} I UNDERSTAND · START</span>
    </div>
  </div>
</div>
"""
    write("WarnConsole.dc.html", wrap("C · first-run warning", C_FONTS, C_CSS, body))


# =============================================================================
# ROUND 2 — Quiet (minimal), light and dark
# =============================================================================
M_FONTS = ""
M_MONO = "Menlo, Consolas, 'Courier New', monospace"
M_SANS = "Arial, 'Helvetica Neue', Helvetica, sans-serif"

THEMES = {
    "light": dict(bg="#f6f4ef", ink="#171614", mute="#8a867e", faint="#b9b5ab", hair="#e2ded4", hair2="#cfcabf", tint="#faf9f6",
                  ghost="rgba(23,22,20,0.22)", on_accent="#1a1300", playhead="rgba(23,22,20,0.55)"),
    "dark":  dict(bg="#121212", ink="#ececec", mute="#7f7f7f", faint="#4a4a4a", hair="#262626", hair2="#333333", tint="#161616",
                  ghost="rgba(236,236,236,0.22)", on_accent="#1a1300", playhead="rgba(236,236,236,0.55)"),
}

def m_st(t):
    return dict(bg="none", tick=t["hair2"], tick_major=t["faint"], label=t["mute"], mono=M_MONO,
                needle=t["ink"], needle_w=1.5,
                grid=t["hair"], zero=t["hair2"], ghost=t["ghost"], ghost_dash="2 4", fill="none", curve=ACCENT, curve_w=2.2,
                mark=t["ink"], mark_style="dot", mark_y=30, mark_fs=11, mark_names=("start", "top", "end"),
                playhead=t["playhead"], playhead_w=1, playhead_op=1)

def m_css(t):
    return f"""
    body {{ margin:0; background:{t["bg"]}; color:{t["ink"]}; font-family:{M_SANS}; font-size:14px; -webkit-font-smoothing:antialiased; }}
    a {{ color:{t["ink"]}; }} a:hover {{ color:{ACCENT}; }}
    .page {{ width:1440px; height:900px; box-sizing:border-box; padding:44px 64px 40px; display:flex; flex-direction:column; gap:0; background:{t["bg"]}; }}
    .top {{ display:flex; align-items:center; justify-content:space-between; height:36px; }}
    .brand {{ display:flex; align-items:center; gap:12px; }}
    .mark {{ width:34px; height:34px; border-radius:50%; background:#111; display:flex; align-items:center; justify-content:center; box-shadow: 0 0 0 1px {t["hair2"]}; }}
    .mark img {{ height:19px; width:auto; display:block; }}
    .wm {{ font-weight:700; font-size:17px; letter-spacing:-0.01em; }}
    .wm span {{ font-weight:400; color:{t["mute"]}; margin-left:6px; }}
    .nav {{ display:flex; align-items:center; gap:28px; font-size:13.5px; color:{t["mute"]}; }}
    .nav b {{ font-weight:500; color:{t["ink"]}; display:inline-flex; align-items:center; gap:6px; }}
    .nav .on::before {{ content:""; width:6px; height:6px; border-radius:50%; background:{ACCENT}; display:inline-block; margin-right:8px; vertical-align:middle; }}
    .rule {{ height:1px; background:{t["hair"]}; margin:18px 0 0; }}
    .strip {{ display:grid; grid-template-columns: minmax(0,1fr) 300px; gap:64px; align-items:end; padding:34px 0 26px; border-bottom:1px solid {t["hair"]}; }}
    .cap {{ font-size:12px; letter-spacing:0.02em; color:{t["mute"]}; margin-bottom:12px; display:flex; justify-content:space-between; }}
    .cap kbd {{ font-family:{M_SANS}; font-size:11.5px; color:{t["mute"]}; }}
    .freq {{ display:flex; align-items:baseline; justify-content:flex-end; gap:10px; font-family:{M_SANS}; font-weight:400; font-size:64px; line-height:0.9; letter-spacing:-0.03em; color:{t["ink"]}; font-variant-numeric:tabular-nums; }}
    .freq small {{ font-family:{M_SANS}; font-weight:400; font-size:15px; color:{t["mute"]}; letter-spacing:0; }}
    .sub {{ display:flex; justify-content:flex-end; align-items:center; gap:22px; margin-top:16px; font-size:13px; color:{t["mute"]}; }}
    .lvl {{ display:flex; align-items:center; gap:10px; }}
    .lvl .bar {{ width:96px; height:1px; background:{t["hair2"]}; position:relative; }}
    .lvl .bar::after {{ content:""; position:absolute; left:64%; top:-4px; width:9px; height:9px; border-radius:50%; background:{t["ink"]}; }}
    .lvl span {{ font-family:{M_SANS}; color:{t["ink"]}; font-size:12.5px; font-variant-numeric:tabular-nums; }}
    .tb {{ display:inline-flex; align-items:center; gap:7px; color:{t["ink"]}; font-weight:500; cursor:pointer; }}
    .row {{ display:grid; grid-template-columns: minmax(0,1fr) 340px; gap:64px; flex:1 1 auto; min-height:0; padding-top:28px; }}
    .graph {{ display:flex; flex-direction:column; min-height:0; }}
    .aside {{ display:flex; flex-direction:column; gap:34px; }}
    .h {{ font-size:12px; color:{t["mute"]}; margin-bottom:14px; display:flex; justify-content:space-between; }}
    .marks {{ display:flex; gap:8px; }}
    .mk {{ flex:1 1 0; height:44px; border:1px solid {t["hair2"]}; border-radius:999px; display:flex; align-items:center; justify-content:center; gap:8px; font-size:13.5px; font-weight:500; color:{t["ink"]}; cursor:pointer; }}
    .mk kbd {{ font-family:{M_SANS}; font-size:11.5px; color:{t["mute"]}; }}
    .mk.next {{ border-color:{t["ink"]}; }}
    .fn {{ font-size:12px; color:{t["mute"]}; margin-top:10px; }}
    .list {{ display:flex; flex-direction:column; }}
    .band {{ display:grid; grid-template-columns: 14px 34px 74px 66px 52px 1fr; align-items:center; gap:10px; height:42px; border-top:1px solid {t["hair"]}; font-family:{M_SANS}; font-size:13.5px; color:{t["ink"]}; font-variant-numeric:tabular-nums; }}
    .band:last-child {{ border-bottom:1px solid {t["hair"]}; }}
    .band .n {{ color:{t["faint"]}; font-size:11.5px; }}
    .band .t {{ font-family:{M_SANS}; font-size:12.5px; color:{t["mute"]}; }}
    .band .g {{ color:{t["ink"]}; }}
    .band .sw {{ justify-self:end; width:26px; height:14px; border-radius:7px; background:{ACCENT}; position:relative; }}
    .band .sw::after {{ content:""; position:absolute; top:2px; right:2px; width:10px; height:10px; border-radius:50%; background:{t["bg"]}; }}
    .band.empty {{ font-family:{M_SANS}; color:{t["faint"]}; font-size:12.5px; grid-template-columns: 14px 1fr; }}
    .band.cur .n {{ color:{ACCENT}; }}
    .export {{ display:grid; grid-template-columns: minmax(0,1fr) 340px; gap:64px; align-items:center; padding-top:22px; border-top:1px solid {t["hair"]}; }}
    .pre {{ margin:0; font-family:{M_MONO}; font-size:12px; line-height:1.6; color:{t["mute"]}; white-space:pre; }}
    .pre b {{ color:{t["ink"]}; font-weight:400; }}
    .acts {{ display:flex; align-items:center; gap:22px; justify-content:flex-end; }}
    .btn {{ display:inline-flex; align-items:center; gap:8px; height:40px; padding:0 18px; border-radius:999px; background:{t["ink"]}; color:{t["bg"]}; font-size:13.5px; font-weight:500; cursor:pointer; }}
    .btn.y {{ background:{ACCENT}; color:{t["on_accent"]}; }}
    .lnk {{ font-size:13.5px; font-weight:500; color:{t["ink"]}; display:inline-flex; align-items:center; gap:7px; cursor:pointer; }}
    .pa {{ font-size:12.5px; color:{t["mute"]}; }} .pa span {{ color:{t["ink"]}; margin-left:8px; }}
"""

def m_band(b, cur=False):
    return (f'<div class="band{" cur" if cur else ""}"><span class="n">{b["n"]}</span><span class="t">{ {"PK":"Peak","LSC":"Low shelf","HSC":"High shelf"}[b["type"]] if False else b["type"]}</span>'
            f'<span>{fmt_hz(b["fc"])} Hz</span><span class="g">{b["gain"]:+.1f} dB</span><span>Q {b["q"]:.1f}</span><span class="sw"></span></div>')

def build_min(theme, fname, title, label):
    t = THEMES[theme]; st = m_st(t)
    tape = tape_svg(948, 92, dict(st, tape_base=24))
    graph = graph_svg(908, 398, st)
    exp = export_text().replace("Preamp", "<b>Preamp</b>")
    icol = t["ink"]
    body = f"""
<div class="page">
  <div class="top">
    <div class="brand"><span class="mark"><img src="dms-mark.png" alt="DMS"></span><div class="wm">DMS<span>Sweep</span></div></div>
    <div class="nav"><b class="on">Tone</b><b class="on">EQ on</b><span>Saved</span><b>{icon("download",icol,14)} Export</b><b title="Theme">{icon("moon" if theme=="light" else "sun",icol,15)}</b></div>
  </div>
  <div class="rule"></div>

  <div class="strip">
    <div>
      <div class="cap"><span>Drag slowly to sweep</span><kbd>← → nudge · shift coarse · space stop</kbd></div>
      {tape}
    </div>
    <div>
      <div class="freq">{fmt_hz(SWEEP_F)}<small>Hz</small></div>
      <div class="sub"><div class="lvl">Level <div class="bar"></div><span>{LEVEL_DB} dB</span></div><span class="tb">{icon("stop",icol,13)} Stop</span></div>
    </div>
  </div>

  <div class="row">
    <div class="graph">
      <div class="h"><span>Response</span><span>20 Hz – 20 kHz · ±12 dB</span></div>
      {graph}
    </div>
    <div class="aside">
      <div>
        <div class="h"><span>Mark the peak you hear</span></div>
        <div class="marks">
          <div class="mk next">Start<kbd>1</kbd></div>
          <div class="mk">Top<kbd>2</kbd></div>
          <div class="mk">End<kbd>3</kbd></div>
        </div>
        <div class="fn">Hold D for a dip · Z undoes</div>
      </div>
      <div>
        <div class="h"><span>Bands</span><span>3 of 8</span></div>
        <div class="list">
          {m_band(BANDS[0], True)}{m_band(BANDS[1])}{m_band(BANDS[2])}
          <div class="band empty"><span class="n">4</span><span>Mark three points to add the next</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="export">
    <pre class="pre">{exp}</pre>
    <div class="acts">
      <span class="pa">Preamp<span>{PREAMP:.1f} dB</span></span>
      <span class="lnk">{icon("download",icol,14)} .txt</span>
      <span class="btn y">{icon("copy",t["on_accent"],14)} Copy</span>
    </div>
  </div>
</div>
"""
    write(fname, wrap(title, M_FONTS, m_css(t), body))

def build_min_warn(theme, fname, title):
    t = THEMES[theme]
    body = f"""
<div style="width:720px; height:460px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; background:{t["bg"]}; font-family:{M_SANS}; color:{t["ink"]};">
  <div style="width:440px; display:flex; flex-direction:column; gap:18px;">
    <span style="width:48px; height:48px; border-radius:50%; background:#111; display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 1px {t["hair2"]};"><img src="dms-mark.png" alt="DMS" style="height:26px; width:auto; display:block;"></span>
    <div style="font-size:30px; font-weight:500; letter-spacing:-0.02em; line-height:1.1;">Turn your volume down first.</div>
    <div style="font-size:15px; line-height:1.55; color:{t["mute"]};">Sine tones at high level can damage hearing and equipment. Start quiet, then raise the level to where you normally listen to music.</div>
    <div style="display:flex; align-items:center; justify-content:space-between; padding-top:16px; border-top:1px solid {t["hair"]};">
      <div class="lvl" style="display:flex; align-items:center; gap:10px; font-size:13px; color:{t["mute"]};">Level <div style="width:96px; height:1px; background:{t["hair2"]}; position:relative;"><div style="position:absolute; left:8%; top:-4px; width:9px; height:9px; border-radius:50%; background:{t["ink"]};"></div></div><span style="font-family:{M_MONO}; color:{t["ink"]}; font-size:12.5px;">−40 dB</span></div>
      <span class="btn y" style="display:inline-flex; align-items:center; gap:8px; height:40px; padding:0 18px; border-radius:999px; background:{ACCENT}; color:{t["on_accent"]}; font-size:13.5px; font-weight:500;">I understand, start</span>
    </div>
  </div>
</div>
"""
    write(fname, wrap(title, M_FONTS, m_css(t), body))

# =============================================================================
def build_canvas():
    W, H, GAP = 1440, 900, 100
    xs = [0, W + GAP, 2 * (W + GAP)]
    y2 = H + 140
    R1, R2 = "round-1", "round-2"
    canvas = {
        "pages": [{"id": R2, "name": "Round 2 · quiet"}, {"id": R1, "name": "Round 1 · dense"}],
        "artboards": [
            {"file": "Main.dc.html", "title": "D · Quiet, light", "x": xs[0], "y": 0, "w": W, "h": H, "page": R2},
            {"file": "QuietDark.dc.html", "title": "E · Quiet, dark", "x": xs[1], "y": 0, "w": W, "h": H, "page": R2},
            {"file": "WarnQuietLight.dc.html", "title": "D · first-run warning", "x": xs[0], "y": y2, "w": 720, "h": 460, "page": R2},
            {"file": "WarnQuietDark.dc.html", "title": "E · first-run warning", "x": xs[1], "y": y2, "w": 720, "h": 460, "page": R2},
            {"file": "BenchInstrument.dc.html", "title": "A · Bench instrument", "x": xs[0], "y": 0, "w": W, "h": H, "page": R1},
            {"file": "LabNotebook.dc.html", "title": "B · Lab notebook", "x": xs[1], "y": 0, "w": W, "h": H, "page": R1},
            {"file": "BroadcastConsole.dc.html", "title": "C · Broadcast console", "x": xs[2], "y": 0, "w": W, "h": H, "page": R1},
            {"file": "WarnBench.dc.html", "title": "A · first-run warning", "x": xs[0], "y": y2, "w": 720, "h": 460, "page": R1},
            {"file": "WarnNotebook.dc.html", "title": "B · first-run warning", "x": xs[1], "y": y2, "w": 720, "h": 460, "page": R1},
            {"file": "WarnConsole.dc.html", "title": "C · first-run warning", "x": xs[2], "y": y2, "w": 720, "h": 460, "page": R1},
        ],
        "annotations": [
            {"id": "note-d", "x": xs[0] + 760, "y": y2, "w": 320, "page": R2,
             "text": "D · Quiet, light\n\nOne grotesk, one mono, hairlines, no boxes. Warm off-white so it reads as paper, not a web app. Yellow only where it means something: the curve, the current band, Copy.\n\nTradeoff: a light page next to a dark music player or DAW can feel bright during a long session."},
            {"id": "note-e", "x": xs[1] + 760, "y": y2, "w": 320, "page": R2,
             "text": "E · Quiet, dark\n\nSame design on neutral near-black. Easier on the eyes for long sweeps and the yellow curve carries more.\n\nTradeoff: dark plus thin hairlines needs care on cheap displays; gray text contrast is the thing to watch."},
            {"id": "note-a", "x": xs[0] + 760, "y": y2, "w": 320, "page": R1,
             "text": "A · Bench instrument\n\nWhy: reads as a piece of test gear you trust. Engraved labels, a tape-style tuner, lamps. The tone readout is the hero.\n\nTradeoff: skeuomorphic details (knob, lamps) need restraint or they tip into kitsch. Densest of the three."},
            {"id": "note-b", "x": xs[1] + 760, "y": y2, "w": 320, "page": R1,
             "text": "B · Lab notebook\n\nWhy: warmest and most human. Layered paper sheets, serif display type, pencil-style marks on graph paper. Feels like your own notes, not a product.\n\nTradeoff: least 'tool-like'; some users may read it as less precise. Grain and paper edges must stay subtle."},
            {"id": "note-c", "x": xs[2] + 760, "y": y2, "w": 320, "page": R1,
             "text": "C · Broadcast console\n\nWhy: maximum contrast and clarity. Raised black modules, amber readouts, a big STOP. Fastest to scan while sweeping.\n\nTradeoff: the coldest of the three and closest to a generic pro-audio look; character comes from restraint and the amber-only palette."},
        ],
        "launch": {"view": "canvas", "page": R2},
    }
    with open(os.path.join(HERE, "canvas.json"), "w") as f:
        json.dump(canvas, f, indent=2)
    print("wrote canvas.json")

if __name__ == "__main__":
    build_a(); build_a_warn()
    build_b(); build_b_warn()
    build_c(); build_c_warn()
    build_min("light", "Main.dc.html", "D · Quiet, light", "D")
    build_min("dark", "QuietDark.dc.html", "E · Quiet, dark", "E")
    build_min_warn("light", "WarnQuietLight.dc.html", "D · first-run warning")
    build_min_warn("dark", "WarnQuietDark.dc.html", "E · first-run warning")
    build_canvas()
    print("\n" + export_text())
