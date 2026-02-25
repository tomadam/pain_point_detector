import os
import requests
from datetime import datetime
import time
import re
import json
import xml.etree.ElementTree as ET
import subprocess
from urllib.parse import quote
from playwright.sync_api import sync_playwright

def fetch_reddit_pain_points(subreddit):
    """
    Using curl via subprocess and parsing RSS to bypass Python HTTP WAF blocks
    """
    keywords = "(manual OR 'hard to' OR 'is there an app' OR 'alternative to' OR 'problem' OR 'frustrating')"
    url = f"https://www.reddit.com/r/{subreddit}/search.rss?q={quote(keywords)}&restrict_sr=1&sort=new&t=week"

    try:
        # We use curl because python's urllib/requests TLS fingerprint is heavily blocked by Reddit's CDN
        result = subprocess.run(
            ["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url], 
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 or not result.stdout.strip():
            return f"### [!] r/{subreddit} 获取失败或为空\n\n"
        
        xml_data = result.stdout
        if "403 Forbidden" in xml_data or "Blocked" in xml_data or "<title>Too Many Requests</title>" in xml_data:
            return f"### [!] r/{subreddit} 403/429 Forbidden (仍被防御拦截)\n> 💡 CDN 屏蔽了目前的访问策略\n\n"

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)

        if not entries: return f"### r/{subreddit} 本周无匹配内容\n\n"

        report = f"### 📍 r/{subreddit} 动态\n\n"
        for entry in entries[:5]:
            title_node = entry.find("atom:title", ns)
            link_node = entry.find("atom:link", ns)
            date_node = entry.find("atom:updated", ns)
            
            title = title_node.text if title_node is not None else "无标题"
            link = link_node.attrib["href"] if link_node is not None else ""
            date_str = date_node.text[:10] if date_node is not None else ""
            
            report += f"#### [{title}]({link})\n"
            report += f"- **发布时间**: {date_str}\n\n"
        return report
    except Exception as e:
        return f"### [!] r/{subreddit} 致命错误:\n```\n{str(e)}\n```\n\n"

def fetch_zhihu_pain_points_browser(page, keyword):
    """
    使用 Playwright 无头浏览器渲染解析知乎
    """
    try:
        url = f"https://www.zhihu.com/search?q={quote(keyword)}&type=content"
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        html = page.content()
        if "安全验证" in html or "访问异常" in html:
            return f"### 知乎「{keyword}」\n> ⚠️ 触发了知乎的安全验证系统，无头浏览器被拦截。\n> 🔗 [手动搜索链接]({url})\n\n"
        
        titles_and_links = page.evaluate('''() => {
            const items = document.querySelectorAll('.ContentItem-title');
            if(items.length === 0) return [];
            return Array.from(items).slice(0, 5).map(i => ({
                title: i.textContent,
                link: i.querySelector('a') ? i.querySelector('a').href : ''
            }));
        }''')
        
        if not titles_and_links:
            return f"### 知乎「{keyword}」\n> ℹ️ 获取成功但未匹配到标题（未登录或改版视图）。\n> 🔗 [手动搜索链接]({url})\n\n"

        report = f"### 知乎「{keyword}」\n\n"
        for item in titles_and_links:
            report += f"- [{item['title']}]({item['link']})\n"
        report += f"\n> 🔗 [查看全部内容]({url})\n\n"
        return report
    except Exception as e:
        return f"### 知乎「{keyword}」\n> ⚠️ 浏览器抓取错误: {str(e)}\n\n"

def fetch_xiaohongshu_pain_points_browser(page, keyword):
    """
    使用 Playwright 解析小红书
    """
    try:
        url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)

        html = page.content()
        if "验证码" in html or "captcha" in html.lower() or "验证一下" in html:
            return f"### 小红书「{keyword}」\n> ⚠️ 触发了滑动验证码或人机验证，无头浏览器被拦截。\n> 📱 [手动执行搜索]({url})\n\n"

        items = page.evaluate('''() => {
            const tiles = document.querySelectorAll('section, .note-item');
            if(tiles.length === 0) return [];
            return Array.from(tiles).slice(0, 5).map(t => {
                const titleEl = t.querySelector('.title, .footer .name');
                const title = titleEl ? titleEl.textContent.trim() : '小红书笔记';
                const linkEl = t.querySelector('a');
                const link = linkEl ? linkEl.href : '';
                return { title, link };
            });
        }''')

        if not items:
            report_str = page.evaluate('''() => {
                if(window.__INITIAL_STATE__) {
                    try {
                        let search = window.__INITIAL_STATE__.searchResult || window.__INITIAL_STATE__.search;
                        let notes = search.noteList || search.items || [];
                        if (notes.length > 0) {
                            return notes.slice(0, 5).map(n => {
                                let note = n.noteCard || n;
                                let title = note.displayTitle || note.title || '小红书笔记';
                                let id = note.id || note.noteId;
                                return { title: title, link: id ? "https://www.xiaohongshu.com/explore/"+id : "" };
                            });
                        }
                    } catch(e) {}
                }
                return [];
            }''')
            if report_str and isinstance(report_str, list):
                items = report_str
        
        if not items:
            return f"### 小红书「{keyword}」\n> ℹ️ 未能从页面结构提取到内容。\n> 📱 [点击手动搜索]({url})\n\n"

        report = f"### 小红书「{keyword}」\n\n"
        for item in items:
            link_str = item['link'] if item['link'] else url
            report += f"- [{item['title']}]({link_str})\n"
        report += f"\n> 📱 [手动查看详细内容]({url})\n\n"
        return report

    except Exception as e:
        return f"### 小红书「{keyword}」\n> ⚠️ 浏览器异常: {str(e)}\n\n"

def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = f"# 🚀 全球建筑/土木行情与痛点探测报告\n\n> **生成时间**: {start_time} (UTC)\n\n"
    
    print("正在扫描 Reddit (使用 Curl 绕过 WAF)...")
    report += "# 🌍 国际平台 - Reddit\n"
    targets = {"CivilEngineering": "土木工程", "Construction": "建筑施工", "QuantitySurveying": "工程造价/估算"}
    for sub, name in targets.items():
        print(f"-> r/{sub}...")
        report += f"## 🏢 领域：{name} (r/{sub})\n"
        report += fetch_reddit_pain_points(sub)
        time.sleep(2)
        
    print("启动 Playwright 浏览器以规避中国平台的反爬机制...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        zhihu_cookie = os.environ.get('ZHIHU_COOKIE', '')
        if zhihu_cookie:
            context.add_cookies([
                {'name': k.strip(), 'value': v.strip(), 'domain': '.zhihu.com', 'path': '/'}
                for block in zhihu_cookie.split(';') if '=' in block for k, v in [block.split('=', 1)]
            ])

        xhs_cookie = os.environ.get('XHS_COOKIE', '')
        if xhs_cookie:
             context.add_cookies([
                {'name': k.strip(), 'value': v.strip(), 'domain': '.xiaohongshu.com', 'path': '/'}
                for block in xhs_cookie.split(';') if '=' in block for k, v in [block.split('=', 1)]
            ])
            

        page = context.new_page()

        report += "\n# 🇨🇳 中国平台 - 知乎\n"
        zhihu_keywords = ["建筑施工 难点", "土木工程 痛点"]
        for keyword in zhihu_keywords:
            print(f"正在扫描知乎: {keyword}...")
            report += fetch_zhihu_pain_points_browser(page, keyword)
            time.sleep(3)

        report += "\n# 🇨🇳 中国平台 - 小红书\n"
        xhs_keywords = ["建筑设计", "施工现场"]
        for keyword in xhs_keywords:
            print(f"正在扫描小红书: {keyword}...")
            report += fetch_xiaohongshu_pain_points_browser(page, keyword)
            time.sleep(3)

        browser.close()

    with open("PAIN_POINTS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 任务完成，报告已生成。")

if __name__ == "__main__":
    main()
