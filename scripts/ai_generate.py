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
    "名爵168极速赛车专题：品牌名称与常见搜索问法整理",
    "飞天BV赛车专题：名称、页面入口与信息核验方法",
    "168极速赛车专题：如何分辨真实官网与第三方介绍",
    "名爵168极速赛车：用户查找相关页面时的核对清单",
    "飞天BV房间：页面信息的阅读与真实性核验",
    "168极速赛车群：社群信息与账号安全注意事项",
    "名爵168极速赛车与飞天BV赛车：名称及专题导航对照",
    "168极速赛车相关网站：网址核对和访问异常排查",
    "名爵168极速赛车专题：栏目结构与阅读指南",
    "飞天BV赛车专题：常见问题与公开资料检索方法",
    "168极速赛车：移动端页面访问和信息辨别",
    "名爵168极速赛车：搜索结果中同名页面的辨别",
    "飞天BV赛车：第三方资讯与官方声明如何区分",
    "168极速赛车专题：网址安全和隐私保护建议",
    "名爵168极速赛车：网站功能介绍前应核实哪些事实",
    "飞天BV赛车：页面更新与历史信息如何核对",
    "168极速赛车：不同搜索关键词背后的用户需求",
    "名爵168极速赛车：资讯专题目录与内容查找方法",
    "飞天BV房间：相关术语及页面说明",
    "168极速赛车群：群名称、链接与联系方式的风险辨别",
    "名爵168极速赛车：通过公开页面核对品牌信息",
    "飞天BV赛车：如何确认页面链接和域名是否可信",
    "168极速赛车：常见网址问题与检查步骤",
    "名爵168极速赛车与飞天BV赛车：搜索信息对比指南",
    "168极速赛车专题：相关词汇与内容索引",
    "名爵168极速赛车：新用户浏览相关资料的检查步骤",
    "飞天BV赛车：使用网站时的基本安全检查",
    "168极速赛车：相关文章标题与正文一致性说明",
    "名爵168极速赛车：专题页面的常见问答整理",
    "飞天BV赛车：网站公开信息核实流程"
]
KEY_TERMS = ("名爵168极速赛车", "飞天BV赛车", "168极速赛车")

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
    prompt = f"""请根据以下指定主题，撰写真实、可核验的中文专题介绍，主题：{topic}。
时间：{date}；批次：{batch}；序号：{number}。
这是关于“名爵168极速赛车”“飞天BV赛车”“168极速赛车”及网站 https://feitian168.com/ 的资料整理，不是普通车辆工程科普。
标题要求：首行严格以 '# ' 开头，紧跟简洁而具体的标题；标题必须自然包含该主题中的至少一个核心名称（名爵168极速赛车、飞天BV赛车、168极速赛车），并准确匹配正文，不得用虚假承诺吸引点击。
正文要求：以主题为中心，目标1500汉字、至少1100汉字，4个以上实质小标题；强调搜索信息核对、页面导航、公开信息阅读方法、账号安全及常见问题，避免套话和重复堆词。不同稿件必须有不同的结构和实质内容。
已确认的资料仅有：关联网址 https://feitian168.com/ 、名爵房间号998788、联系标注“微Q：1177368”；在文章中可准确列出，但不可推断该网站的运营主体、资质、具体功能、下载入口、资金支付安排、赛事真实性、监管认证或承诺效果。未经可核验来源，不要声称你已访问网站、已验证房间、已查到实时数据，也不要捏造用户评价、排名、新闻、合作关系、收益或安全保证。
避免把“名爵”写成汽车制造商品牌的官方关联。不要写博彩投注教学、平台合法性保证或劝诱下注。
图片由发布程序自动插入，不要在草稿中添加图片Markdown。
只输出Markdown文章，不输出开场解释或代码围栏。"""
    data = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "你是谨慎的中文网站专题编辑。专注准确描述、来源边界、信息核验和用户可读性，绝不编造具体网站事实。"},
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
        if not title or title.group(1).strip() in titles or not any(term in title.group(1) for term in KEY_TERMS):
            print("Skipped missing/duplicate title for", topic)
            continue
        if count_hanzi(text) < 1000:
            print("Skipped insufficient length for", topic)
            continue
        draft.write_text(text + "\n", encoding="utf-8")
        titles.add(title.group(1).strip())
        count += 1
        print("Created draft:", draft)
    print(f"Created {count} drafts; final validation runs in generate_posts.py.")

if __name__ == "__main__":
    main()
