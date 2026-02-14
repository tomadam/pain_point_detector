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
    注意：知乎API需要认证，此版本使用模拟搜索
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.zhihu.com/'
    }

    # 使用Google搜索知乎内容作为替代方案
    google_search_url = f"https://www.google.com/search?q=site:zhihu.com+{quote(keyword)}"

    try:
        # 尝试直接访问知乎搜索页（可能需要cookie）
        search_url = f"https://www.zhihu.com/search?type=content&q={quote(keyword)}"
        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 403 or response.status_code == 400:
            return f"### 知乎「{keyword}」\n> ⚠️ 知乎需要登录认证才能访问搜索API\n> 💡 建议：使用知乎官方API或配置登录Cookie\n> 🔗 手动搜索：[点击这里在知乎搜索「{keyword}」](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

        if response.status_code != 200:
            return f"### 知乎「{keyword}」\n> ⚠️ 暂时无法访问 (HTTP {response.status_code})\n> 🔗 手动搜索：[点击这里在知乎搜索「{keyword}」](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

        # 成功获取页面，尝试解析（简化版）
        report = f"### 知乎「{keyword}」\n"
        report += f"> 🔗 [在知乎查看完整结果](https://www.zhihu.com/search?q={quote(keyword)})\n"
        report += "> ℹ️ 由于知乎API限制，建议手动访问上述链接查看详细内容\n\n"
        return report

    except Exception as e:
        return f"### 知乎「{keyword}」\n> ⚠️ 连接错误: {str(e)}\n> 🔗 [手动在知乎搜索「{keyword}」](https://www.zhihu.com/search?q={quote(keyword)})\n\n"

def fetch_xiaohongshu_pain_points(keyword):
    """
    抓取小红书相关话题的痛点讨论
    注意：小红书的反爬虫机制极强，提供手动搜索链接
    """
    # 小红书的反爬虫机制包括：设备指纹、滑块验证、登录要求等
    # 直接爬取几乎不可能，提供用户友好的替代方案

    search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"

    report = f"### 小红书「{keyword}」\n"
    report += f"> 📱 [在小红书App中搜索「{keyword}」]({search_url})\n"
    report += "> ℹ️ 小红书需要App登录才能查看内容，建议使用手机App进行搜索\n"
    report += "> 💡 提示：可以在小红书App中搜索关键词，关注相关话题的痛点讨论\n\n"

    return report

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
