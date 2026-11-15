#!/usr/bin/env python3
"""Render evenly spaced PNG frames using python-lottie, if installed.

Install the optional renderer separately: pip install lottie
This renderer is a smoke-test aid, not a substitute for platform players.
"""
import argparse, pathlib, sys
def main():
    p=argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--out-dir",default="reports/frames")
    p.add_argument("--count",type=int,default=12)
    a=p.parse_args()
    try:
        from lottie.parsers.tgs import parse_tgs
        from lottie.parsers.sif import parse_sif
        from lottie.parsers.svg import parse_svg
        from lottie.parsers.lottie import parse_tgs as _unused
    except Exception:
        try:
            from lottie.parsers import lottie as parser
            from lottie.exporters.cairo import export_png
        except Exception as e:
            print("Optional python-lottie renderer unavailable. Install and configure a supported renderer.", file=sys.stderr)
            print(str(e), file=sys.stderr)
            sys.exit(2)
        animation = parser.parse_tgs(a.file) if a.file.endswith(".tgs") else parser.parse_json(a.file)
        out=pathlib.Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
        total=max(1,int(animation.out_point-animation.in_point))
        for i in range(max(1,a.count)):
            frame=animation.in_point + round((total-1)*i/max(1,a.count-1))
            export_png(animation, str(out/f"frame-{i:03d}.png"), frame=frame)
        print(out)
        return
    print("Renderer API differs in this python-lottie version; use a pinned renderer adapter.", file=sys.stderr)
    sys.exit(2)
if __name__=="__main__": main()
