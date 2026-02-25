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
    # 关键词组合：寻找“困难”、“手动”、“寻找App”、“现有工具缺项”
    keywords = "(manual OR 'hard to' OR 'is there an app' OR 'alternative to' OR 'problem' OR 'frusting')"
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={keywords}&restrict_sr=1&sort=new&t=week"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"### [!] 无法访问 r/{subreddit} (HTTP {response.status_code})\n\n"

        data = response.json()
        posts = data.get('data', {}).get('children', [])

        if not posts:
            return f"### r/{subreddit} 本周暂无匹配痛点内容\n\n"

        report = f"### 📍 r/{subreddit} 动态\n\n"
        for post in posts[:8]: # 选取前8条高相关内容
            p = post['data']
            # 时间转换
            post_time = datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d')

            report += f"#### [{p['title']}](https://reddit.com{p['permalink']})\n"
            report += f"- **发布时间**: {post_time}\n"
            report += f"- **热度**: 👍 {p['score']} | 💬 {p['num_comments']} 评论\n"

            # 截取摘要
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
    """
    cookie = os.environ.get('ZHIHU_COOKIE')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'https://www.zhihu.com/search?q={quote(keyword)}&type=content',
    }

    if cookie:
        headers['Cookie'] = cookie

    # 使用知乎 V4 搜索 API，通常返回 JSON
    api_url = f"https://www.zhihu.com/api/v4/search_v3?t=general&q={quote(keyword)}&offset=0&limit=5"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code in [403, 401, 400]:
            return f"### 知乎「{keyword}」\n> ⚠️ 知乎响应了 {response.status_code} (可能需要登录)\n> 💡 请在 GitHub Secrets 中配置 `ZHIHU_COOKIE` 以恢复自动抓取。\n> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

        if response.status_code != 200:
            return f"### 知乎「{keyword}」\n> ⚠️ 暂时无法访问 API (HTTP {response.status_code})\n> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

        data = response.json()
        items = data.get('data', [])

        if not items:
            return f"### 知乎「{keyword}」\n> ℹ️ 未找到相关实时讨论。\n\n"

        report = f"### 知乎「{keyword}」\n\n"
        count = 0
        for item in items:
            if count >= 5: break

            # 提取文章或回答
            obj = item.get('object', {})
            title = obj.get('highlight_title') or obj.get('title')
            if not title: continue

            # 去除 HTML 标签
            title = re.sub(r'<[^>]+>', '', title)
            url = obj.get('url', '').replace('api/v4/answers', 'answer').replace('api/v4/questions', 'question')
            if 'zhihu.com' not in url:
                if 'id' in obj:
                    url = f"https://www.zhihu.com/question/{obj.get('id')}"
                else:
                    url = f"https://www.zhihu.com/search?q={quote(keyword)}"

            excerpt = re.sub(r'<[^>]+>', '', obj.get('excerpt', ''))

            report += f"#### [{title}]({url})\n"
            report += f"- **摘要**: {excerpt[:200]}...\n\n"
            count += 1

        return report

    except Exception as e:
        return f"### 知乎「{keyword}」\n> ⚠️ 抓取发生错误: {str(e)}\n> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

def fetch_xiaohongshu_pain_points(keyword):
    """
    抓取小红书相关话题的痛点讨论
    支持通过环境变量 XHS_COOKIE 传入登录 Cookie
    """
    cookie = os.environ.get('XHS_COOKIE')

    if not cookie:
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"
        report = f"### 小红书「{keyword}」\n"
        report += f"> ⚠️ 缺少 `XHS_COOKIE`，无法自动抓取内容\n"
        report += f"> 📱 [在小红书App中搜索「{keyword}」]({search_url})\n"
        report += "> ℹ️ 小红书反爬虫机制极强，建议手动访问查看最新痛点内容\n\n"
        return report

    # 尝试使用 API（小红书需要签名，很可能失败）
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Cookie': cookie,
        'Referer': f'https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}'
    }

    try:
        # 使用网页版搜索 API（需要 x-sign 等签名，这里只是示例）
        api_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
        payload = {
            "keyword": keyword,
            "page": 1,
            "page_size": 10,
            "search_id": "auto_" + str(int(time.time()))
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                items = data.get('data', {}).get('items', [])
                if items:
                    report = f"### 小红书「{keyword}」\n\n"
                    for item in items[:5]:
                        note = item.get('note_card', {})
                        title = note.get('display_title', '小红书笔记')
                        note_id = note.get('id')
                        user = note.get('user', {}).get('nickname', '未知')
                        report += f"#### [{title}](https://www.xiaohongshu.com/explore/{note_id})\n"
                        report += f"- **博主**: {user}\n\n"
                    return report

        # 失败回退
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"
        return f"### 小红书「{keyword}」\n> ⚠️ API 未返回有效数据 (HTTP {response.status_code})\n> 🔗 [手动搜索链接]({search_url})\n\n"
    except Exception as e:
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"
        return f"### 小红书「{keyword}」\n> ⚠️ 请求异常: {str(e)}\n> 🔗 [手动搜索链接]({search_url})\n\n"

def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"开始执行全球探测任务: {start_time}")

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
        print(f"正在扫描 Reddit: {sub} ({name})...")
        report_content += f"## 🏢 领域：{name} (r/{sub})\n"
        report_content += fetch_reddit_pain_points(sub)
        time.sleep(2) # 礼貌抓取限制

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
        time.sleep(3) # 知乎限流较严格，延长间隔

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
        time.sleep(3) # 小红书限流更严格

    # 保存报告
    report_file = "PAIN_POINTS_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"任务完成，报告已生成至 {report_file}")

if __name__ == "__main__":
    main()
