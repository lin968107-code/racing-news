"""Publish up to five checked, previously-unpublished Chinese articles per batch.

Articles must first be placed in _drafts as .md files. This tool deliberately
does not manufacture 'new' articles by renaming or paraphrasing old templates.
"""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

DRAFTS = Path("_drafts")
POSTS = Path("_posts")
IMAGES = Path("images")
BATCHES = {"morning": 0, "noon": 1, "evening": 2}
MIN_HANZI = 1000
BATCH_SIZE = 5

def normalize(text):
    return re.sub(r"\s+", "", text).lower()

def get_title_and_body(raw):
    lines = raw.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("First line must be '# 文章标题'")
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:]).strip()
    if not title or not body:
        raise ValueError("Missing article title/body")
    return title, body

def get_images(body):
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)

def check_image_links(body):
    links = get_images(body)
    if not links:
        raise ValueError("Missing photo in article")
    for link in links:
        if not link.startswith("/images/"):
            raise ValueError("Image must use /images/filename.jpg syntax")
        filename = link.split("/", 2)[-1]
        if not filename or not (IMAGES / filename).is_file():
            raise ValueError("Image does not exist: " + link)

def load_prior():
    prior_titles = set()
    prior_bodies = []
    for post in POSTS.glob("*.md"):
        text = post.read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^# (.+)$", text)
        if headings:
            prior_titles.add(headings[0].strip())
        prior_bodies.append(normalize(text))
    return prior_titles, prior_bodies

def compose(title, body):
    metadata = (
        "---\n"
        "layout: post\n"
        "title: " + json.dumps(title, ensure_ascii=False) + "\n"
        "description: " + json.dumps(title + "｜赛车资讯与专题文章", ensure_ascii=False) + "\n"
        "---\n\n"
    )
    footer = (
        "\n\n## 相关信息\n\n"
        "名爵房间号：998788\n\n"
        "微Q：1177368\n\n"
        "网站：https://feitian168.com/\n"
    )
    return metadata + "# " + title + "\n\n" + body + footer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, choices=BATCHES)
    args = parser.parse_args()
    POSTS.mkdir(exist_ok=True)
    DRAFTS.mkdir(exist_ok=True)
    date = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    slot = BATCHES[args.batch]
    existing_in_slot = list(POSTS.glob(f"{date}-{args.batch}-*.md"))
    remaining = BATCH_SIZE - len(existing_in_slot)
    if remaining <= 0:
        print(f"Batch {args.batch} already has 5 posts; no action.")
        return
    prior_titles, prior_bodies = load_prior()
    candidates = sorted(DRAFTS.glob("*.md"))
    published = 0
    for draft in candidates:
        if published >= remaining:
            break
        try:
            title, body = get_title_and_body(draft.read_text(encoding="utf-8"))
            length = len(re.findall(r"[\u4e00-\u9fff]", body))
            if length < MIN_HANZI:
                raise ValueError(f"Only {length} Chinese characters; need >= {MIN_HANZI}")
            check_image_links(body)
            if title in prior_titles:
                raise ValueError("Title already published")
            normalized = normalize(body)
            if any(normalized == old or SequenceMatcher(None, normalized[:6000], old[:6000]).ratio() > 0.85 for old in prior_bodies):
                raise ValueError("Near-duplicate of existing article")
            content = compose(title, body)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10]
            filename = f"{date}-{args.batch}-{digest}.md"
            output = POSTS / filename
            if output.exists():
                raise ValueError("Article file already exists")
        except (ValueError, UnicodeError) as exc:
            print(f"SKIP {draft.name}: {exc}")
            continue
        output.write_text(content, encoding="utf-8")
        draft.unlink()
        prior_titles.add(title)
        prior_bodies.append(normalized)
        published += 1
        print(f"PUBLISHED {output.name} ({length} Hanzi)")
    print(f"{args.batch}: published {published}/{remaining} eligible articles.")
    if published < remaining:
        print("Not enough unique, photo-backed drafts with >=1000 Chinese characters. No filler generated.")

if __name__ == "__main__":
    main()
