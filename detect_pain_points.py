import os
import requests
from datetime import datetime
import time
import re
import json
import html as html_lib
from urllib.parse import quote

def fetch_reddit_pain_points(subreddit):
    """
    抓取 Reddit 痛点，增加更多伪装头部
    """
    keywords = "(manual OR 'hard to' OR 'is there an app' OR 'alternative to' OR 'problem' OR 'frustrating')"
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={quote(keywords)}&restrict_sr=1&sort=new&t=week"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.reddit.com/r/{subreddit}/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 403:
            return f"### [!] r/{subreddit} 403 Forbidden\n> 💡 Reddit 屏蔽了云端 IP。建议本地运行此脚本以获取国际数据。\n\n"
        if response.status_code != 200:
            return f"### [!] r/{subreddit} HTTP {response.status_code}\n\n"

        data = response.json()
        posts = data.get('data', {}).get('children', [])
        if not posts: return f"### r/{subreddit} 本周无匹配内容\n\n"

        report = f"### 📍 r/{subreddit} 动态\n\n"
        for post in posts[:5]:
            p = post['data']
            post_time = datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d')
            report += f"#### [{p['title']}](https://reddit.com{p['permalink']})\n"
            report += f"- **发布时间**: {post_time} | 👍 {p['score']}\n"
            report += "\n---\n"
        return report
    except Exception as e:
        return f"### [!] r/{subreddit} 致命错误: {str(e)}\n\n"

def fetch_zhihu_pain_points(keyword):
    """
    知乎抓取尝试，改用手机网页版视角
    """
    cookie = os.environ.get('ZHIHU_COOKIE', '')
    encoded_keyword = quote(keyword)

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Cookie': cookie,
    }

    # 尝试移动端搜索页
    m_url = f"https://www.zhihu.com/search?q={encoded_keyword}&type=content"

    try:
        response = requests.get(m_url, headers=headers, timeout=20)
        if response.status_code == 403:
            return f"### 知乎「{keyword}」\n> ⚠️ 知乎 403。建议手动访问获取最新动态。\n> 🔗 [手动搜索链接]({m_url})\n\n"

        # 简单的正则提取网页标题
        titles = re.findall(r'<span[^>]*class="ContentItem-title"[^>]*>(.*?)</span>', response.text)
        if not titles:
            titles = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', response.text)

        if titles:
            report = f"### 知乎「{keyword}」\n\n"
            for t in titles[:5]:
                clean_t = re.sub(r'<[^>]+>', '', t).strip()
                if len(clean_t) > 5:
                    report += f"- {clean_t}\n"
            report += f"\n> 🔗 [查看全部内容]({m_url})\n\n"
            return report
        
        return f"### 知乎「{keyword}」\n> ℹ️ 云端解析失败（结构变动或触发人机验证）。\n> 🔗 [手动搜索链接]({m_url})\n\n"
    except Exception as e:
        return f"### 知乎「{keyword}」\n> ⚠️ 抓取发生错误: {str(e)}\n\n"

def fetch_xiaohongshu_pain_points(keyword):
    """
    改进小红书 JSON 提取逻辑
    """
    cookie = os.environ.get('XHS_COOKIE', '')
    encoded_keyword = quote(keyword)
    url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.xiaohongshu.com/',
    }

    try:
        response = requests.get(url, headers=headers, timeout=25)
        text = response.text

        # 改进提取逻辑：先定位 window.__INITIAL_STATE__=，然后找下一个 </script>
        start_marker = "window.__INITIAL_STATE__="
        if start_marker in text:
            start_idx = text.find(start_marker) + len(start_marker)
            end_idx = text.find("</script>", start_idx)
            json_str = text[start_idx:end_idx].strip()
            
            # 处理可能的未定义或乱码
            if json_str.endswith(';'): json_str = json_str[:-1]
            
            try:
                # 使用 html_lib 解码 HTML 实体
                json_str = html_lib.unescape(json_str)
                data = json.loads(json_str)
                
                # 寻找笔记列表
                search_data = data.get('searchResult', {}) or data.get('search', {})
                items = search_data.get('noteList', []) or search_data.get('items', [])
                
                if items:
                    report = f"### 小红书「{keyword}」\n\n"
                    for item in items[:5]:
                        note = item.get('noteCard', item)
                        title = note.get('displayTitle') or note.get('title', '小红书笔记')
                        note_id = note.get('id') or note.get('noteId')
                        report += f"#### [{title}](https://www.xiaohongshu.com/explore/{note_id})\n"
                        report += f"- **博主**: {note.get('user', {}).get('nickname', '博主')}\n\n"
                    return report
            except Exception as e:
                # 记录报错的具体字符位置
                print(f"XHS JSON Error: {str(e)}")
        
        # 兜底：简单正则提取
        titles = re.findall(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', text)
        if titles:
            report = f"### 小红书「{keyword}」\n\n"
            for t in titles[:5]:
                report += f"- {re.sub(r'<[^>]+>', '', t).strip()}\n"
            report += f"\n> 📱 [手动查看详细内容]({url})\n\n"
            return report

        return f"### 小红书「{keyword}」\n> ⚠️ 自动抓取失败（页面结构变动或触发验证）。\n> 📱 [点击手动搜索]({url})\n\n"
    except Exception as e:
        return f"### 小红书「{keyword}」\n> ⚠️ 请求异常: {str(e)}\n\n"

def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = f"# 🚀 全球建筑/土木行情与痛点探测报告\n\n> **生成时间**: {start_time} (UTC)\n\n"
    
    # 减少并发和频率，降低被封概率
    print("扫描 Reddit...")
    report += "# 🌍 国际平台 - Reddit\n"
    report += fetch_reddit_pain_points("CivilEngineering")
    time.sleep(5)
    
    print("扫描知乎...")
    report += "\n# 🇨🇳 中国平台 - 知乎\n"
    report += fetch_zhihu_pain_points("建筑施工 难点")
    time.sleep(5)
    
    print("扫描小红书...")
    report += "\n# 🇨🇳 中国平台 - 小红书\n"
    report += fetch_xiaohongshu_pain_points("建筑设计")
    
    with open("PAIN_POINTS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 完成。")

if __name__ == "__main__":
    main()
