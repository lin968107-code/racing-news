"""Generate fresh Chinese articles through an OpenAI API key configured as a GitHub secret."""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TOPICS = [
    "赛车轮胎胎压与温度管理", "赛道日刹车衰减与驾驶安全", "赛车空气动力学基础",
    "转向不足与转向过度的区别", "赛道安全旗语和安全规则", "赛车悬挂系统与调校原理",
    "赛车数据记录和圈速分析", "赛道湿地驾驶风险", "赛车轮胎抓地力原理",
    "赛车变速箱基础与传动损失", "赛车座椅与安全带", "赛车车身结构安全",
    "赛车制动系统维护", "赛车模拟器训练的局限", "日常汽车和赛道用车的区别",
    "车手体能训练", "赛车发动机散热原理", "轮胎磨损形态识别", "制动距离",
    "赛车前后轮定位角", "赛事计时系统", "赛车进站维护", "赛车转弯路线",
    "高性能车辆保养", "赛车技术名词", "赛道防护装备", "赛车燃油管理",
    "雨天赛道水漂", "赛车防滚架", "赛道布局与车辆要求"
]
BATCHES = {"morning": 0, "noon": 1, "evening": 2}
DRAFTS = Path("_drafts")
POSTS = Path("_posts")

def count_hanzi(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

def existing_titles():
    names = set()
    for folder in (DRAFTS, POSTS):
        for file in folder.glob("*.md"):
            text = file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^# ([^\n]+)", text)
            if match:
                names.add(match.group(1).strip())
    return names

def ask_ai(topic, date, batch, number, key, model):
    prompt = f"""撰写一篇中文赛车科普长文，主题为：{topic}。今天是{date}，批次{batch}，文章序号{number}。
要求：文章内容目标1500汉字，至少1100汉字（不含标点）；内容须独立、有实际技术解释、安全建议和清晰段落，杜绝用重复废话凑数。第一行必须是'# 独特标题'，下面写Markdown正文，至少4个具体小标题。
不要捏造新闻、数据、测试结果和引用，不冒充任何车企官方，不写博彩、投注、彩票建议。不堆砌搜索关键词和联系方式。文中合理位置插入且仅插入一次图片：![赛车示意图片](/images/mg-racing-001.jpg)。除文章本身外不要任何解释。"""
    data = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "你是严谨的中文汽车科普编辑，重视真实性、独立价值和可读性。"},
        {"role": "user", "content": prompt}
    ], "temperature": 0.7}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                obj = json.loads(response.read().decode("utf-8"))
            return obj["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as ex:
            detail = ex.read(400).decode("utf-8", errors="replace")
            if ex.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f"AI API HTTP {ex.code}: {detail}") from ex
    raise RuntimeError("AI API failed")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, choices=BATCHES)
    args = parser.parse_args()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not configured. No AI content generated.")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    DRAFTS.mkdir(exist_ok=True)
    day = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    offset = (datetime.strptime(day, "%Y-%m-%d").toordinal() * 17 + BATCHES[args.batch] * 5) % len(TOPICS)
    titles = existing_titles()
    count = 0
    for i in range(5):
        draft = DRAFTS / f"{day}-{args.batch}-{i+1:02d}.md"
        if draft.exists():
            print("Existing draft:", draft)
            continue
        topic = TOPICS[(offset + i) % len(TOPICS)]
        text = ask_ai(topic, day, args.batch, i + 1, key, model)
        title = re.search(r"^# ([^\n]+)", text)
        if not title or title.group(1).strip() in titles:
            print("Skipped missing/duplicate title for", topic)
            continue
        if count_hanzi(text) < 1000 or "/images/mg-racing-001.jpg" not in text:
            print("Skipped insufficient length/missing image for", topic)
            continue
        draft.write_text(text + "\n", encoding="utf-8")
        titles.add(title.group(1).strip())
        count += 1
        print("Created draft:", draft)
    print(f"Created {count} drafts; final validation runs in generate_posts.py.")

if __name__ == "__main__":
    main()
