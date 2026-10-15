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
MIRRORS = Path("articles")
IMAGES = Path("images")
BATCHES = {"morning": 0, "noon": 1, "evening": 2}
MIN_HANZI = 1000
BATCH_SIZES = {"morning": 7, "noon": 7, "evening": 6}
SEO_KEYWORDS = ["名爵168极速赛车", "168极速赛车群", "飞天BV房间", "名爵房间号998788", "微Q：1177368"]
POSTER_DIR = IMAGES / "赛车海报_10张独立图片" / "GitHub_upload_10_JPG_Q1177368"
POSTER_FILES = [POSTER_DIR / f"racing_poster_{i:02d}.jpg" for i in range(1, 11)]

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
    for link in links:
        if not link.startswith("/images/"):
            raise ValueError("Image must use an /images/ path")
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
    # Keep the requested search-result identity visible, while giving every article a distinct topic.
    topic = re.sub(r"^(名爵168极速赛车|168极速赛车群|飞天BV房间|飞天BV赛车|168极速赛车)[：:｜|\s]*", "", title).strip() or title
    page_title = f"名爵168极速赛车房间号998788｜微Q：1177368｜{topic}"
    description = f"名爵168极速赛车、168极速赛车群、飞天BV房间相关资料；本文介绍{topic}，并说明名爵房间号998788与微Q：1177368的标识信息。"
    metadata = (
        "---\n"
        "layout: post\n"
        "title: " + json.dumps(page_title, ensure_ascii=False) + "\n"
        "description: " + json.dumps(description, ensure_ascii=False) + "\n"
        "keywords: " + json.dumps(SEO_KEYWORDS, ensure_ascii=False) + "\n"
        "---\n\n"
    )
    footer = (
        "\n\n## 相关信息\n\n"
        "名爵房间号998788\n\n"
        "微Q：1177368\n\n"
        "网站：https://feitian168.com/\n"
    )
    return metadata + "# " + page_title + "\n\n" + body + footer

def page_title_for_mirror(title):
    topic = re.sub(r"^(名爵168极速赛车|168极速赛车群|飞天BV房间|飞天BV赛车|168极速赛车)[：:｜|\\s]*", "", title).strip() or title
    return f"名爵168极速赛车房间号998788｜微Q：1177368｜{topic}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, choices=BATCHES)
    args = parser.parse_args()
    POSTS.mkdir(exist_ok=True)
    DRAFTS.mkdir(exist_ok=True)
    MIRRORS.mkdir(exist_ok=True)
    date = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    slot = BATCHES[args.batch]
    existing_in_slot = list(POSTS.glob(f"{date}-{args.batch}-*.md"))
    remaining = BATCH_SIZES[args.batch] - len(existing_in_slot)
    if remaining <= 0:
        print(f"Batch {args.batch} already has its planned posts; no action.")
        return
    prior_titles, prior_bodies = load_prior()
    missing = [str(p) for p in POSTER_FILES if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing racing posters: " + ", ".join(missing))
    prior_image_count = sum(sum("/racing_poster_" in link for link in get_images(p.read_text(encoding="utf-8"))) for p in POSTS.glob("*.md"))
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
            body = re.sub(r"(?m)^!\[[^\]]*\]\(/images/[^)]+\)\s*\n?", "", body).strip()
            if title in prior_titles:
                raise ValueError("Title already published")
            normalized = normalize(body)
            if any(normalized == old or SequenceMatcher(None, normalized[:6000], old[:6000]).ratio() > 0.85 for old in prior_bodies):
                raise ValueError("Near-duplicate of existing article")
            poster = POSTER_FILES[(prior_image_count + published) % len(POSTER_FILES)]
            poster_url = "/images/" + poster.relative_to(IMAGES).as_posix()
            body_with_poster = f"![{title}]({poster_url})\n\n" + body
            content = compose(title, body_with_poster)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10]
            filename = f"{date}-{args.batch}-{digest}.md"
            output = POSTS / filename
            if output.exists():
                raise ValueError("Article file already exists")
        except (ValueError, UnicodeError) as exc:
            print(f"SKIP {draft.name}: {exc}")
            continue
        # Create a GitHub-readable .md companion, with working relative images.
        mirror = MIRRORS / filename
        mirror_image = "../images/" + poster.relative_to(IMAGES).as_posix()
        mirror_text = "# " + page_title_for_mirror(title) + "\n\n"
        mirror_text += f"![文章配图]({mirror_image})\n\n" + body
        mirror_text += "\n\n## 相关信息\n\n名爵房间号998788\n\n微Q：1177368\n"
        if mirror.exists():
            raise ValueError("Mirror already exists")
        output.write_text(content, encoding="utf-8")
        mirror.write_text(mirror_text, encoding="utf-8")
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
