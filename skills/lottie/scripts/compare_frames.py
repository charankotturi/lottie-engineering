#!/usr/bin/env python3
"""Compare PNG frame directories using mean absolute pixel error."""
import argparse, pathlib, json
from PIL import Image, ImageChops, ImageStat

def main():
    p=argparse.ArgumentParser()
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.add_argument("--threshold",type=float,default=0.01,help="maximum normalized mean absolute error")
    p.add_argument("--report")
    a=p.parse_args()
    bdir,cdir=pathlib.Path(a.baseline),pathlib.Path(a.candidate)
    names=sorted(x.name for x in bdir.glob("*.png"))
    results=[]
    for name in names:
        bp,cp=bdir/name,cdir/name
        if not cp.exists():
            results.append({"frame":name,"status":"FAIL","reason":"candidate missing"})
            continue
        b=Image.open(bp).convert("RGBA"); c=Image.open(cp).convert("RGBA")
        if b.size!=c.size:
            results.append({"frame":name,"status":"FAIL","reason":"dimensions differ","baseline":b.size,"candidate":c.size})
            continue
        diff=ImageChops.difference(b,c)
        mean=sum(ImageStat.Stat(diff).mean)/4/255
        results.append({"frame":name,"mae":mean,"status":"PASS" if mean<=a.threshold else "FAIL"})
    report={"threshold":a.threshold,"frames":results,"overall":"FAIL" if any(x["status"]=="FAIL" for x in results) else "PASS"}
    print(json.dumps(report,indent=2))
    if a.report: pathlib.Path(a.report).write_text(json.dumps(report,indent=2)+"\\n")
    raise SystemExit(1 if report["overall"]=="FAIL" else 0)
if __name__=="__main__": main()
