import os
import requests
from datetime import datetime
import time

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
    report_content += f"> **探测说明**: 本报告自动扫描全球社交媒体，提取关于“流程繁琐”、“手动操作”及“寻找数字化方案”的真实讨论。\n\n"

    for sub, name in targets.items():
        print(f"正在扫描: {sub} ({name})...")
        report_content += f"## 🏢 领域：{name} (r/{sub})\n"
        report_content += fetch_reddit_pain_points(sub)
        time.sleep(2) # 礼貌抓取限制

    # 保存报告
    report_file = "PAIN_POINTS_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"任务完成，报告已生成至 {report_file}")

if __name__ == "__main__":
    main()
