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
        # 尝试使用真实的浏览器 User-Agent，规避 403
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 403:
            return f"### [!] 无法访问 r/{subreddit} (HTTP 403: 访问被拒绝)\n> 💡 Reddit 经常屏蔽 GitHub Actions 的云端 IP，可能需要手动访问。\n\n"
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
    """
    cookie = os.environ.get('ZHIHU_COOKIE', '')
    encoded_keyword = quote(keyword)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': f'https://www.zhihu.com/search?q={encoded_keyword}&type=content',
        'X-Requested-With': 'fetch',
        'X-Api-Version': '3.0.91', # 知乎 API 版本
    }

    if cookie:
        headers['Cookie'] = cookie
    else:
        return f"### 知乎「{keyword}」\n> ⚠️ 未检测到 `ZHIHU_COOKIE`。\n\n"

    # 尝试改用通用搜索 API
    api_url = f"https://www.zhihu.com/api/v4/search_v3?t=general&q={encoded_keyword}&offset=0&limit=5"

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        status = response.status_code

        if status == 403:
            # 如果 API 403，尝试直接抓取网页内容（虽然更难解析）
            return f"### 知乎「{keyword}」\n> ⚠️ 知乎拒绝访问 (HTTP 403)。云端由于缺少加密参数（x-zse-96）可能被拦截。\n> 🔗 [手动搜索链接](https://www.zhihu.com/search?q={encoded_keyword})\n\n"

        if status != 200:
            return f"### 知乎「{keyword}」\n> ⚠️ API 响应异常 (HTTP {status})\n\n"

        data = response.json()
        items = data.get('data', [])

        if not items:
            return f"### 知乎「{keyword}」\n> ℹ️ 未找到相关实时讨论。\n\n"

        report = f"### 知乎「{keyword}」\n\n"
        count = 0
        for item in items:
            if count >= 5: break
            obj = item.get('object', {})
            title = obj.get('highlight_title') or obj.get('title')
            if not title: continue
            title = re.sub(r'<[^>]+>', '', title)
            
            obj_type = obj.get('type', '')
            obj_id = obj.get('id', '')
            if obj_type == 'answer':
                url = f"https://www.zhihu.com/question/{obj.get('question', {}).get('id', '')}/answer/{obj_id}"
            elif obj_type == 'article':
                url = f"https://zhuanlan.zhihu.com/p/{obj_id}"
            else:
                url = f"https://www.zhihu.com/question/{obj_id}" if obj_id else f"https://www.zhihu.com/search?q={encoded_keyword}"

            excerpt = re.sub(r'<[^>]+>', '', obj.get('excerpt', ''))
            report += f"#### [{title}]({url})\n"
            report += f"- **摘要**: {excerpt[:200]}...\n\n"
            count += 1
        return report
    except Exception as e:
        return f"### 知乎「{keyword}」\n> ⚠️ 抓取错误: {str(e)}\n\n"


def fetch_xiaohongshu_pain_points(keyword):
    """
    抓取小红书相关话题的痛点讨论
    """
    cookie = os.environ.get('XHS_COOKIE', '')
    encoded_keyword = quote(keyword)
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"

    if not cookie:
        return f"### 小红书「{keyword}」\n> ⚠️ 未检测到 `XHS_COOKIE`。\n\n"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Cookie': cookie,
        'Referer': 'https://www.xiaohongshu.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        if response.status_code != 200:
            return f"### 小红书「{keyword}」\n> ⚠️ 页面访问异常 (HTTP {response.status_code})\n\n"

        html = response.text
        
        # 记录前几百个字符协助调试
        # print(f"DEBUG: XHS HTML preview for {keyword}: {html[:500]}")

        # 尝试更兼容的匹配模式
        # 小红书的 JSON 数据可能在 <script>window.__INITIAL_STATE__={...}</script> 中
        # 注意：这里需要递归匹配或者非贪婪匹配
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>', html, re.DOTALL)
        
        if not match:
            # 备选：尝试从网页中直接提取标题和链接
            # 小红书笔记列表通常包含在 class 包含 "title" 的 div/a 中
            titles = re.findall(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', html)
            if titles:
                report = f"### 小红书「{keyword}」\n\n"
                for t in titles[:5]:
                    clean_t = re.sub(r'<[^>]+>', '', t).strip()
                    report += f"- {clean_t}\n"
                report += f"\n> 📱 [查看更多详细内容]({search_url})\n\n"
                return report
            
            return f"### 小红书「{keyword}」\n> ⚠️ 无法解析数据结构，可能是被反爬拦截（需滑动验证）或页面结构改变。\n> 📱 [手动搜索「{keyword}」]({search_url})\n\n"

        import json
        try:
            state = json.loads(match.group(1))
            # 小红书的数据结构经常变，这里尝试多种路径
            search_result = state.get('searchResult', {}) or state.get('search', {})
            notes = search_result.get('noteList', []) or search_result.get('items', [])
            
            if not notes:
                # 检查是否命中了验证码页面
                if "验证码" in html or "captcha" in html.lower():
                    return f"### 小红书「{keyword}」\n> ⚠️ 触发了滑动验证码，GitHub Actions 暂时无法绕过。\n\n"
                return f"### 小红书「{keyword}」\n> ℹ️ 未找到相关笔记。\n\n"

            report = f"### 小红书「{keyword}」\n\n"
            for note in notes[:5]:
                # 兼容不同层级
                note_data = note.get('noteCard', note)
                title = note_data.get('displayTitle') or note_data.get('title', '小红书笔记')
                note_id = note_data.get('id') or note.get('id')
                user = note_data.get('user', {}).get('nickname', '未知')
                
                report += f"#### [{title}](https://www.xiaohongshu.com/explore/{note_id})\n"
                report += f"- **博主**: {user}\n\n"
            return report
        except Exception as e:
            return f"### 小红书「{keyword}」\n> ⚠️ 解析 JSON 失败: {str(e)}\n\n"

    except Exception as e:
        return f"### 小红书「{keyword}」\n> ⚠️ 请求异常: {str(e)}\n\n"


def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"开始执行全球探测任务: {start_time}")

    report_content = f"# 🚀 全球建筑/土木行情与痛点探测报告\n\n"
    report_content += f"> **生成时间**: {start_time} (UTC)\n"
    report_content += "> **探测说明**: 本报告自动扫描全球社交媒体（Reddit、知乎、小红书），提取关于「流程繁琐」、「手动操作」及「寻找数字化方案」的真实讨论。\n\n"

    # 国际平台：Reddit
    report_content += "# 🌍 国际平台 - Reddit\n\n"
    targets = {"CivilEngineering": "土木工程", "Construction": "建筑施工", "QuantitySurveying": "工程造价/估算"}
    for sub, name in targets.items():
        print(f"正在扫描 Reddit: r/{sub}...")
        report_content += f"## 🏢 领域：{name} (r/{sub})\n"
        report_content += fetch_reddit_pain_points(sub)
        time.sleep(2)

    # 中国平台：知乎
    report_content += "\n# 🇨🇳 中国平台 - 知乎\n\n"
    zhihu_keywords = ["建筑施工 难点", "土木工程 痛点"]
    for keyword in zhihu_keywords:
        print(f"正在扫描知乎: {keyword}...")
        report_content += f"## 🔍 搜索词：{keyword}\n"
        report_content += fetch_zhihu_pain_points(keyword)
        time.sleep(3)

    # 中国平台：小红书
    report_content += "\n# 🇨🇳 中国平台 - 小红书\n\n"
    xhs_keywords = ["建筑设计", "施工现场"]
    for keyword in xhs_keywords:
        print(f"正在扫描小红书: {keyword}...")
        report_content += f"## 🔍 搜索词：{keyword}\n"
        report_content += fetch_xiaohongshu_pain_points(keyword)
        time.sleep(3)

    # 保存报告
    with open("PAIN_POINTS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    print("✅ 任务完成，报告已生成。")

if __name__ == "__main__":
    main()
