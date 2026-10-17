#!/usr/bin/env python3
"""Publish up to 100 pre-reviewed Markdown files each Beijing morning."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote
import re, hashlib, json

ROOT=Path("articles")
QUEUE=Path("_approved")
LIMIT=100
STAMP=datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d")
DEST=ROOT / ("daily_"+STAMP)
IMG=Path("images/unified-cover.png")
KEYWORDS=("名爵168极速赛车","飞天BV极速赛车","房间号998788","微Q")
MARK_START="<!-- related-articles:start -->"
MARK_END="<!-- related-articles:end -->"

def norm(s):
    return re.sub(r"\s+","",s).casefold()

def strip_related(s):
    return re.sub(re.escape(MARK_START)+r".*?"+re.escape(MARK_END),"",s,flags=re.S)

def fingerprint(s):
    s=strip_related(s)
    s=re.sub(r"!\[[^\]]*\]\([^)]+\)","",s)
    return hashlib.sha256(norm(s).encode()).hexdigest()

def topic(s):
    m=re.search(r"(?m)^# (.+)$",s)
    return norm(m.group(1)) if m else ""

def main():
    QUEUE.mkdir(exist_ok=True)
    files=sorted(QUEUE.glob("*.md"))
    if not files:
        print("No approved articles. Published 0; no generated filler.")
        return
    if not IMG.is_file():
        raise RuntimeError("Unified cover missing; refusing publication.")
    if DEST.exists() and any(DEST.glob("*.md")):
        print("Today's batch already exists; not publishing again.")
        return
    seen_topics=set()
    seen_content=set()
    for path in ROOT.rglob("*.md"):
        if path.name=="README.md": continue
        try: s=path.read_text(encoding="utf-8")
        except UnicodeError: continue
        seen_topics.add(topic(s))
        seen_content.add(fingerprint(s))
    accepted=[]
    for src in files:
        if len(accepted)>=LIMIT: break
        try:
            text=src.read_text(encoding="utf-8")
            if not text.startswith("# "): raise ValueError("missing H1")
            if not all(k in text for k in KEYWORDS): raise ValueError("missing required keyword")
            if len(re.findall(r"[\u4e00-\u9fff]",text))<600:
                raise ValueError("less than 600 Chinese characters")
            key=topic(text)
            digest=fingerprint(text)
            if not key or key in seen_topics or digest in seen_content:
                raise ValueError("duplicate title or content")
            # Do not trust stored relative image paths from a different folder.
            text=strip_related(text).rstrip()
            text=re.sub(r"(?m)^!\[[^\]]*\]\((?:\.\./)+images/unified-cover\.png\)\s*\n?","",text)
            text=re.sub(r"(?m)^!\[[^\]]*\]\(/images/unified-cover\.png\)\s*\n?","",text)
            if re.search(r"(?m)^!\[[^\]]*\]\(",text):
                raise ValueError("other image links require review")
            name=f"{len(accepted)+1:03d}-{digest[:10]}.md"
            accepted.append((src,name,text))
            seen_topics.add(key);seen_content.add(digest)
        except (ValueError,UnicodeError) as e:
            print(f"SKIP {src.name}: {e}")
    if not accepted:
        print("No eligible approved articles. Published 0.")
        return
    DEST.mkdir(parents=True,exist_ok=True)
    for i,(src,name,body) in enumerate(accepted):
        links=["","---","","## 相关文章","",MARK_START,""]
        for step in range(1,min(9,len(accepted))):
            _,other_name,other_body=accepted[(i+step)%len(accepted)]
            display=re.search(r"(?m)^# (.+)$",other_body).group(1)
            url="https://github.com/lin968107-code/racing-news/blob/main/"+quote((DEST/other_name).as_posix())
            links.append(f"- [{display}]({url})")
        links.extend(["",MARK_END,""])
        first,rest=body.split("\n",1)
        data=first+"\n\n![名爵168极速赛车黑金封面](../../images/unified-cover.png)\n"+rest.rstrip()+"\n"+"\n".join(links)
        (DEST/name).write_text(data,encoding="utf-8")
        src.unlink()
    urls_path=DEST / "article_links.txt"
    urls_path.write_text("\n".join(
        "https://github.com/lin968107-code/racing-news/blob/main/"
        + quote((DEST/name).as_posix()) for _,name,_ in accepted
    ) + "\n",encoding="utf-8")
    print(f"Published {len(accepted)} articles to {DEST}; {len(files)-len(accepted)} queued/unqualified items remain.")
if __name__=="__main__": main()
