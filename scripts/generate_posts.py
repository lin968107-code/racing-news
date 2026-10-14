import os
from datetime import datetime


# 文章目录
posts_dir = "_posts"

# 图片目录
images_dir = "images"


# 自动创建目录
os.makedirs(posts_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)


# 图片名称
image_file = "mg-racing-001.jpg"


# 文章标题
title = "名爵极速赛车技术特点分析"


# 文件名
filename = f"{datetime.now().strftime('%Y-%m-%d')}-mg-racing.md"


# 文章内容
content = f"""---
title: {title}
description: 名爵极速赛车相关技术特点、赛车资讯以及行业内容介绍。
keywords: 名爵极速赛车,168极速赛车,飞天BV赛车
---

![名爵极速赛车主题图片](../images/{image_file})


# {title}


## 名爵极速赛车相关介绍

名爵极速赛车专题内容，介绍赛车相关知识、技术特点以及行业资讯。


## 赛车技术分析

围绕赛车系统、用户体验、赛车文化进行内容分析。


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


# 写入文章
post_path = os.path.join(posts_dir, filename)

with open(
    post_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(content)


print("文章生成成功:", filename)
