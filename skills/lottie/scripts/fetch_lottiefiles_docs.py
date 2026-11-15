#!/usr/bin/env python3
"""Fetch public LottieFiles docs snapshots and machine-readable catalogs.

This does not authenticate to MCP or retrieve private workspace data. Use the
connected agent client to capture authenticated tool schemas and live outputs.
"""
import argparse, datetime, hashlib, json, pathlib, urllib.request, urllib.error

URLS = {
    "llms.txt": "https://docs.lottiefiles.com/llms.txt",
    "openapi.json": "https://docs.lottiefiles.com/openapi.json",
    "mcp-server-card.json": "https://docs.lottiefiles.com/.well-known/mcp/server-card.json",
    "agent-skills-index.json": "https://docs.lottiefiles.com/.well-known/agent-skills/index.json",
    "creator-mcp-reference.html": "https://docs.lottiefiles.com/en/creator-mcp/reference",
    "platform-mcp-tools.html": "https://docs.lottiefiles.com/en/platform/mcp/tools",
    "webmcp.html": "https://docs.lottiefiles.com/en/creator/13_ai-tools/lottie-creator-webmcp",
}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="knowledge/raw/docs")
    ap.add_argument("--timeout",type=int,default=30)
    args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    manifest={"fetched_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"items":[]}
    for name,url in URLS.items():
        req=urllib.request.Request(url,headers={"User-Agent":"lottie-engineering/0.0.0 (documentation snapshot)"})
        try:
            with urllib.request.urlopen(req,timeout=args.timeout) as r:
                body=r.read()
                (out/name).write_bytes(body)
                manifest["items"].append({"name":name,"url":url,"status":"FETCHED","http_status":r.status,
                    "content_type":r.headers.get("Content-Type"),"bytes":len(body),
                    "sha256":hashlib.sha256(body).hexdigest()})
        except Exception as e:
            manifest["items"].append({"name":name,"url":url,"status":"UNAVAILABLE","error":str(e)})
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__": main()
