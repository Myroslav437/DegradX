import sys, os, subprocess, json, re, difflib
import numpy as np, pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from analyze import analyze
ORIG = "/home/mmishchuk/projects/DegradX/paper/img"
S = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.join(S, "run/img")
def fonts(p):
    out = subprocess.run(["pdffonts", p], capture_output=True, text=True).stdout.splitlines()[2:]
    return sorted(l.split()[0] for l in out)
def raster(p, tag):
    base = os.path.join(S, "raster", tag)
    subprocess.run(["pdftoppm", "-r", "150", "-gray", "-singlefile", p, base], check=True)
    import pymupdf as fz
    pix = fz.Pixmap(base + ".pgm")
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
def content(p):
    return pymupdf.open(p)[0].read_contents().decode("latin1").splitlines()
res = {}
for f in sys.argv[1:]:
    o, n = os.path.join(ORIG, f + ".pdf"), os.path.join(NEW, f + ".pdf")
    ao, an = analyze(o), analyze(n)
    r = {"page_orig": ao["page"], "page_new": an["page"], "page_equal": ao["page"] == an["page"],
         "fonts_equal": fonts(o) == fonts(n), "fonts_orig": fonts(o), "fonts_new": fonts(n),
         "text_size_hist_equal": ao["text_sizes"] == an["text_sizes"],
         "text_colors_equal": ao["text_colors"] == an["text_colors"],
         "strokes_equal": ao["strokes"] == an["strokes"], "fills_equal": ao["fills"] == an["fills"]}
    if not r["text_size_hist_equal"]: r["sizes"] = (ao["text_sizes"], an["text_sizes"])
    if not r["strokes_equal"]: r["strokes"] = (ao["strokes"], an["strokes"])
    A, B = raster(o, f + "_orig"), raster(n, f + "_new")
    r["raster_shape"] = (A.shape, B.shape)
    h, w = min(A.shape[0], B.shape[0]), min(A.shape[1], B.shape[1])
    d = np.abs(A[:h, :w].astype(int) - B[:h, :w].astype(int))
    # pixels outside the overlap count as different
    total = max(A.shape[0], B.shape[0]) * max(A.shape[1], B.shape[1])
    extra = total - h * w
    r["raster_diff_frac_any"] = round(float(((d > 0).sum() + extra) / total), 6)
    r["raster_diff_frac_gt32"] = round(float(((d > 32).sum() + extra) / total), 6)
    co, cn = content(o), content(n)
    sm = difflib.SequenceMatcher(None, co, cn, autojunk=False)
    r["content_lines"] = (len(co), len(cn))
    r["content_identical"] = co == cn
    r["content_line_ratio"] = round(sm.ratio(), 6)
    res[f] = r
print(json.dumps(res, indent=1, default=str))
