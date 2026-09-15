import sys, collections, pymupdf, json
def analyze(path, verbose=False):
    doc = pymupdf.open(path); pg = doc[0]
    out = {"page": (round(pg.rect.width,3), round(pg.rect.height,3))}
    sizes = collections.Counter(); fonts = collections.Counter(); tcol = collections.Counter()
    spans = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                sizes[round(s["size"],2)] += len(s["text"])
                fonts[s["font"]] += 1
                tcol["#%06x" % s["color"]] += 1
                spans.append((s["text"], s["font"], round(s["size"],3), "#%06x"%s["color"], [round(v,1) for v in s["bbox"]]))
    out["text_sizes"] = dict(sorted(sizes.items())); out["fonts"] = dict(fonts); out["text_colors"] = dict(tcol)
    strokes = collections.Counter(); fills = collections.Counter()
    for d in pg.get_drawings():
        c = d.get("color"); f = d.get("fill")
        if c is not None:
            strokes[(round(d.get("width") or 0,3), tuple(round(v,3) for v in c), d.get("dashes"), d.get("lineCap") and tuple(d.get("lineCap")))] += 1
        if f is not None:
            fills[tuple(round(v,3) for v in f)] += 1
    out["strokes"] = {str(k): v for k, v in sorted(strokes.items(), key=lambda kv: str(kv[0]))}
    out["fills"] = {str(k): v for k, v in fills.items()}
    if verbose: out["spans"] = spans
    return out
if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("=====", p); print(json.dumps(analyze(p, True), indent=1, default=str))
