#!/usr/bin/env python3
"""Validate and archive a tool inventory exported by an MCP client.

Expected input is a JSON array of tool objects with name, description and
inputSchema fields (the common MCP list-tools shape). This script never
discovers tools itself; export the live list from your authenticated client.
"""
import argparse, datetime, hashlib, json, pathlib, re
SECRET=re.compile(r"(token|authorization|cookie|secret|password|api.?key)",re.I)
def clean(x):
    if isinstance(x,dict):
        return {k:("[REDACTED]" if SECRET.search(k) else clean(v)) for k,v in x.items()}
    if isinstance(x,list): return [clean(v) for v in x]
    return x
def main():
    p=argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--surface",required=True,choices=["creator-mcp","platform-mcp","webmcp"])
    p.add_argument("--out",default="knowledge/raw")
    a=p.parse_args()
    raw=json.loads(pathlib.Path(a.input).read_text())
    tools=raw.get("tools") if isinstance(raw,dict) else raw
    if not isinstance(tools,list): raise SystemExit("Expected a JSON array or an object with a tools array")
    records=[]
    for t in tools:
        if not isinstance(t,dict) or not t.get("name"): continue
        item=clean(t)
        records.append({"name":item["name"],"description":item.get("description"),
                        "inputSchema":item.get("inputSchema") or item.get("input_schema"),
                        "annotations":item.get("annotations"),"availability":"OBSERVED"})
    result={"surface":a.surface,"captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "count":len(records),"tools":records,
            "sha256":hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()}
    out=pathlib.Path(a.out)/f"{a.surface}-tool-inventory.json"
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+"\n")
    print(out)
if __name__=="__main__": main()
