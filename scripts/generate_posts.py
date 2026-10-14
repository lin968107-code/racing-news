import os
from datetime import datetime


posts_dir = "_posts"
images_dir = "images"

os.makedirs(posts_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)


image_file = "mg-racing-001.jpg"


titles = [
    "名爵极速赛车技术特点分析",
    "名爵极速赛车系统功能介绍",
    "168极速赛车行业发展趋势",
    "飞天BV赛车专题解析",
    "名爵赛车用户体验分析",
    "赛车资讯内容整理",
    "赛车技术发展观察",
    "168极速赛车相关知识介绍",
    "赛车文化专题分析",
    "飞天BV赛车行业观察"
]


for index, title in enumerate(titles, start=1):

    filename = (
        f"{datetime.now().strftime('%Y-%m-%d')}"
        f"-mg-racing-{index}.md"
    )

    content = f"""---
title: {title}
description: 名爵极速赛车相关资讯、技术分析、赛车内容介绍。
keywords: 名爵极速赛车,168极速赛车,飞天BV赛车
---

![名爵极速赛车主题图片](../images/{image_file})


# {title}


## 名爵极速赛车相关介绍

介绍名爵极速赛车相关知识、赛车技术特点以及行业资讯。


## 赛车技术分析

围绕赛车系统、赛车文化、用户体验进行内容分析。


## 房间信息

名爵极速赛车相关房间：

房间号：998788


## 飞天BV赛车专题

飞天BV赛车相关资讯：

官方网站：

https://feitian168.com


## 联系方式

微Q：1177368


## 总结

持续更新赛车资讯、技术分析和行业内容。
"""


    post_path = os.path.join(posts_dir, filename)

    with open(
        post_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)


    print("生成文章:", filename)
