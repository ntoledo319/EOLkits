#!/usr/bin/env python3
"""Cross-publish the EOLkits articles to Hashnode (own blog, canonical back to
eolkits.com via originalArticleURL). Second backlink source after dev.to.
Idempotent, dry-run default. curl + GraphQL (system CA store).

Reuses the same articles as the dev.to publisher (./devto/*.md).
Env: HASHNODE_TOKEN. Usage: python3 publish_hashnode.py [--apply]
"""
import os
import sys
import re
import glob
import json
import time
import subprocess
import pathlib

GQL = "https://gql.hashnode.com/"
TOKEN = os.environ.get("HASHNODE_TOKEN", "")
DIR = pathlib.Path(__file__).parent / "devto"


def gql(query, variables=None):
    payload = {"query": query, "variables": variables or {}}
    cmd = ["curl", "-s", "-m", "30", "-X", "POST", GQL,
           "-H", f"Authorization: {TOKEN}", "-H", "Content-Type: application/json",
           "--data", json.dumps(payload)]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except Exception:
        return {"_raw": out}


def parse(path):
    txt = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    meta, body = {}, txt
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2).lstrip("\n")
    return meta, body


def main():
    if not TOKEN:
        print("ERROR: set HASHNODE_TOKEN (Hashnode -> Settings -> Developer -> Generate token)")
        sys.exit(1)
    apply = "--apply" in sys.argv
    me = gql("query { me { publications(first: 1) { edges { node { id title } } } } }")
    try:
        node = me["data"]["me"]["publications"]["edges"][0]["node"]
        pub_id, pub_title = node["id"], node.get("title", "")
    except Exception:
        print("could not resolve a publication for this token:", json.dumps(me)[:300])
        print("(create a blog at hashnode.com first, then retry)")
        sys.exit(1)
    print(f"publication: {pub_title} ({pub_id})")
    have = set()
    ex = gql("query($id: ObjectId!) { publication(id: $id) { posts(first: 30) { edges { node { title } } } } }", {"id": pub_id})
    try:
        have = {e["node"]["title"] for e in ex["data"]["publication"]["posts"]["edges"]}
    except Exception:
        pass
    for path in sorted(glob.glob(str(DIR / "*.md"))):
        meta, body = parse(path)
        title = meta.get("title")
        if not title:
            continue
        if title in have:
            print(f"  skip (exists): {title}")
            continue
        tags = [{"slug": t.strip(), "name": t.strip().upper()}
                for t in meta.get("tags", "").split(",") if t.strip()][:5]
        inp = {"title": title, "contentMarkdown": body, "publicationId": pub_id,
               "tags": tags, "originalArticleURL": meta.get("canonical_url", "")}
        if not apply:
            print(f"  DRY: would publish '{title}'  (canonical -> {inp['originalArticleURL']})")
            continue
        r = gql("mutation Publish($input: PublishPostInput!) { publishPost(input: $input) { post { url } } }", {"input": inp})
        url = (((r.get("data") or {}).get("publishPost") or {}).get("post") or {}).get("url")
        print(f"  published: {url or json.dumps(r)[:240]}")
        time.sleep(3)
    if not apply:
        print("\nDry run. Re-run with --apply.")


if __name__ == "__main__":
    main()
