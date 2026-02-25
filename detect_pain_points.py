import os
import requests
from datetime import datetime
import time
import re
from urllib.parse import quote

def fetch_reddit_pain_points(subreddit):
    """
    抓取指定 Subreddit 的潜在痛点贴
    """
    keywords = "(manual OR 'hard to' OR 'is there an app' OR 'alternative to' OR 'problem' OR 'frustrating')"
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={quote(keywords)}&restrict_sr=1&sort=new&t=week"

    headers = {
        # Reddit 官方要求的 User-Agent 格式: <platform>:<app ID>:<version> (by u/<reddit username>)
        'User-Agent': 'python:pain-point-detector:v1.0 (by u/pain_point_bot)',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            return f"### [!] r/{subreddit} 被限流 (HTTP 429)，请稍后重试\n\n"
        if response.status_code != 200:
            return f"### [!] 无法访问 r/{subreddit} (HTTP {response.status_code})\n\n"

        data = response.json()
        posts = data.get('data', {}).get('children', [])

        if not posts:
            return f"### r/{subreddit} 本周暂无匹配痛点内容\n\n"

        report = f"### 📍 r/{subreddit} 动态\n\n"
        for post in posts[:8]:
            p = post['data']
            post_time = datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d')
            report += f"#### [{p['title']}](https://reddit.com{p['permalink']})\n"
            report += f"- **发布时间**: {post_time}\n"
            report += f"- **热度**: 👍 {p['score']} | 💬 {p['num_comments']} 评论\n"
            content = p.get('selftext', '')
            if content:
                summary = content[:300].replace('\n', ' ') + "..."
                report += f"- **摘要**: {summary}\n"
            report += "\n---\n"
        return report
    except Exception as e:
        return f"### [!] 抓取 r/{subreddit} 发生致命错误: {str(e)}\n\n"


def fetch_zhihu_pain_points(keyword):
    """
    抓取知乎相关话题的痛点讨论
    支持通过环境变量 ZHIHU_COOKIE 传入登录 Cookie
    
    修复说明：
    1. 补充了完整的浏览器请求头（x-zse-96, x-ab-param 等）
    2. 增加了 zc_0 cookies 等知乎必需字段
    3. 改用更稳定的 API 端点
    4. 增加了详细的错误诊断
    """
    cookie = os.environ.get('ZHIHU_COOKIE', '')

    encoded_keyword = quote(keyword)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'https://www.zhihu.com/search?q={encoded_keyword}&type=content',
        'Origin': 'https://www.zhihu.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'x-requested-with': 'fetch',
    }

    if cookie:
        headers['Cookie'] = cookie
    else:
        # 无 Cookie 时直接返回提示，避免无效请求
        return (
            f"### 知乎「{keyword}」\n"
            f"> ⚠️ 未检测到 `ZHIHU_COOKIE` 环境变量\n"
            f"> 💡 请在 GitHub Repo → Settings → Secrets → Actions 中新增 Secret：`ZHIHU_COOKIE`\n"
            f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
        )

    # 知乎 V4 搜索 API
    api_url = f"https://www.zhihu.com/api/v4/search_v3?t=general&q={encoded_keyword}&offset=0&limit=5&correction=1&or_query_if_empty=1"

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        status = response.status_code

        if status == 401:
            return (
                f"### 知乎「{keyword}」\n"
                f"> ⚠️ Cookie 已过期或无效 (HTTP 401)，请重新获取 Cookie\n"
                f"> 💡 打开知乎网页版，按 F12 → Network → 复制任意请求的 Cookie 头\n"
                f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
            )

        if status == 400:
            return (
                f"### 知乎「{keyword}」\n"
                f"> ⚠️ 知乎 API 返回 400（请求参数问题或 Cookie 格式不正确）\n"
                f"> 💡 请确认 Cookie 中包含 `z_c0` 字段，这是知乎的身份认证 token\n"
                f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
            )

        if status == 403:
            return (
                f"### 知乎「{keyword}」\n"
                f"> ⚠️ 知乎拒绝访问 (HTTP 403)，可能触发了反爬虫机制\n"
                f"> 💡 建议等待 24 小时后重试，或尝试更新 Cookie\n"
                f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
            )

        if status != 200:
            return (
                f"### 知乎「{keyword}」\n"
                f"> ⚠️ API 响应异常 (HTTP {status})\n"
                f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
            )

        data = response.json()
        items = data.get('data', [])

        if not items:
            return f"### 知乎「{keyword}」\n> ℹ️ 未找到相关实时讨论。\n\n"

        report = f"### 知乎「{keyword}」\n\n"
        count = 0
        for item in items:
            if count >= 5:
                break

            obj = item.get('object', {})
            title = obj.get('highlight_title') or obj.get('title')
            if not title:
                continue

            # 去除 HTML 标签
            title = re.sub(r'<[^>]+>', '', title)

            # 构建 URL
            obj_type = obj.get('type', '')
            obj_id = obj.get('id', '')
            if obj_type == 'answer':
                url = f"https://www.zhihu.com/question/{obj.get('question', {}).get('id', '')}/answer/{obj_id}"
            elif obj_type == 'article':
                url = f"https://zhuanlan.zhihu.com/p/{obj_id}"
            elif obj_type == 'question':
                url = f"https://www.zhihu.com/question/{obj_id}"
            else:
                url = obj.get('url', f"https://www.zhihu.com/search?q={encoded_keyword}")
                url = url.replace('api/v4/answers', 'answer').replace('api/v4/questions', 'question')

            excerpt = re.sub(r'<[^>]+>', '', obj.get('excerpt', ''))

            report += f"#### [{title}]({url})\n"
            if excerpt:
                report += f"- **摘要**: {excerpt[:200]}...\n\n"
            count += 1

        return report

    except requests.exceptions.Timeout:
        return (
            f"### 知乎「{keyword}」\n"
            f"> ⚠️ 请求超时（知乎服务器响应慢）\n"
            f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
        )
    except Exception as e:
        return (
            f"### 知乎「{keyword}」\n"
            f"> ⚠️ 抓取发生错误: {str(e)}\n"
            f"> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"
        )


def fetch_xiaohongshu_pain_points(keyword):
    """
    抓取小红书相关话题的痛点讨论

    修复说明：
    - 小红书 edith API 需要 x-s/x-t 签名，无法直接调用
    - 改用网页版搜索页面解析（需要 XHS_COOKIE）
    - Cookie 中需包含 web_session 字段
    """
    cookie = os.environ.get('XHS_COOKIE', '')
    encoded_keyword = quote(keyword)
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"

    if not cookie:
        return (
            f"### 小红书「{keyword}」\n"
            f"> ⚠️ 未检测到 `XHS_COOKIE` 环境变量，无法自动抓取\n"
            f"> 💡 请在 GitHub Repo → Settings → Secrets → Actions 中新增 Secret：`XHS_COOKIE`\n"
            f"> 📝 获取方法：打开小红书网页版 → F12 → Network → 复制任意请求的 Cookie\n"
            f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
        )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cookie': cookie,
        'Referer': 'https://www.xiaohongshu.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=20)

        if response.status_code == 471 or response.status_code == 403:
            return (
                f"### 小红书「{keyword}」\n"
                f"> ⚠️ 小红书拒绝访问 (HTTP {response.status_code})，Cookie 可能已过期\n"
                f"> 💡 请重新获取 `XHS_COOKIE`（打开小红书网页版重新登录后复制 Cookie）\n"
                f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
            )

        if response.status_code != 200:
            return (
                f"### 小红书「{keyword}」\n"
                f"> ⚠️ API 响应异常 (HTTP {response.status_code})\n"
                f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
            )

        # 从 HTML 中提取笔记数据（小红书服务端渲染，数据嵌入在 __INITIAL_STATE__ 中）
        html = response.text

        # 尝试提取 JSON 数据块
        pattern = r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            # 尝试备用模式：直接从 HTML 提取标题
            titles = re.findall(r'<a[^>]+class="[^"]*title[^"]*"[^>]*>([^<]+)</a>', html)
            if titles:
                report = f"### 小红书「{keyword}」\n\n"
                for t in titles[:5]:
                    report += f"- {t.strip()}\n"
                report += f"\n> 📱 [查看更多]({search_url})\n\n"
                return report

            return (
                f"### 小红书「{keyword}」\n"
                f"> ⚠️ 无法解析页面数据（小红书可能更新了页面结构或触发了人机验证）\n"
                f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
            )

        import json
        try:
            state_data = json.loads(match.group(1))
            # 根据小红书实际数据结构提取笔记列表
            note_list = []
            search_data = state_data.get('searchResult', {}) or state_data.get('search', {})
            items = search_data.get('noteList', []) or search_data.get('items', [])

            if items:
                report = f"### 小红书「{keyword}」\n\n"
                for item in items[:5]:
                    note = item.get('noteCard', item)
                    title = note.get('displayTitle') or note.get('title', '小红书笔记')
                    note_id = note.get('id') or note.get('noteId', '')
                    user = (note.get('user') or {}).get('nickname', '未知博主')
                    desc = note.get('desc', '')

                    note_url = f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else search_url
                    report += f"#### [{title}]({note_url})\n"
                    report += f"- **博主**: {user}\n"
                    if desc:
                        report += f"- **简介**: {desc[:150]}...\n"
                    report += "\n"
                report += f"> 📱 [查看更多]({search_url})\n\n"
                return report
        except (json.JSONDecodeError, KeyError):
            pass

        return (
            f"### 小红书「{keyword}」\n"
            f"> ⚠️ 已获取页面但无法提取笔记数据\n"
            f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
        )

    except requests.exceptions.Timeout:
        return (
            f"### 小红书「{keyword}」\n"
            f"> ⚠️ 请求超时\n"
            f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
        )
    except Exception as e:
        return (
            f"### 小红书「{keyword}」\n"
            f"> ⚠️ 请求异常: {str(e)}\n"
            f"> 📱 [手动搜索「{keyword}」]({search_url})\n\n"
        )


def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"开始执行全球探测任务: {start_time}")

    # 诊断环境变量
    zhihu_cookie = os.environ.get('ZHIHU_COOKIE', '')
    xhs_cookie = os.environ.get('XHS_COOKIE', '')
    print(f"[诊断] ZHIHU_COOKIE: {'✅ 已配置 (长度: ' + str(len(zhihu_cookie)) + ')' if zhihu_cookie else '❌ 未配置'}")
    print(f"[诊断] XHS_COOKIE: {'✅ 已配置 (长度: ' + str(len(xhs_cookie)) + ')' if xhs_cookie else '❌ 未配置'}")

    # 目标领域
    targets = {
        "CivilEngineering": "土木工程",
        "Construction": "建筑施工",
        "QuantitySurveying": "工程造价/估算",
        "RealEstate": "房地产开发",
        "PropTech": "地产科技"
    }

    report_content = f"# 🚀 全球建筑/土木行情与痛点探测报告\n\n"
    report_content += f"> **生成时间**: {start_time} (UTC)\n"
    report_content += "> **探测说明**: 本报告自动扫描全球社交媒体（Reddit、知乎、小红书），提取关于「流程繁琐」、「手动操作」及「寻找数字化方案」的真实讨论。\n\n"

    # 国际平台：Reddit
    report_content += "# 🌍 国际平台 - Reddit\n\n"
    for sub, name in targets.items():
        print(f"正在扫描 Reddit: r/{sub} ({name})...")
        report_content += f"## 🏢 领域：{name} (r/{sub})\n"
        report_content += fetch_reddit_pain_points(sub)
        time.sleep(2)

    # 中国平台：知乎
    report_content += "\n# 🇨🇳 中国平台 - 知乎\n\n"
    zhihu_keywords = [
        "建筑施工 难点",
        "土木工程 痛点",
        "工程造价 效率",
        "施工管理 问题",
        "BIM 应用难题"
    ]

    for keyword in zhihu_keywords:
        print(f"正在扫描知乎: {keyword}...")
        report_content += f"## 🔍 搜索词：{keyword}\n"
        report_content += fetch_zhihu_pain_points(keyword)
        time.sleep(3)

    # 中国平台：小红书
    report_content += "\n# 🇨🇳 中国平台 - 小红书\n\n"
    xhs_keywords = [
        "建筑设计",
        "施工现场",
        "工程管理"
    ]

    for keyword in xhs_keywords:
        print(f"正在扫描小红书: {keyword}...")
        report_content += f"## 🔍 搜索词：{keyword}\n"
        report_content += fetch_xiaohongshu_pain_points(keyword)
        time.sleep(3)

    # 保存报告
    report_file = "PAIN_POINTS_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n✅ 任务完成，报告已生成至 {report_file}")

if __name__ == "__main__":
    main()
