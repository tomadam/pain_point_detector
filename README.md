# 🚀 全球建筑/土木行情与痛点探测器

自动化工具，每天从 **Reddit（国际）、知乎、小红书（中国）** 等社交平台抓取建筑、土木工程、房地产科技等领域的痛点讨论，帮助发现潜在的产品机会和行业需求。

## 📋 功能特性

- 🌍 **国际平台**：自动扫描 5 个专业领域的 Subreddit
- 🇨🇳 **中国平台**：抓取知乎、小红书相关话题
- 🎯 智能筛选包含「手动操作」、「流程繁琐」、「寻找方案」等关键词的帖子
- 📊 生成结构化的 Markdown 格式报告
- ⏰ GitHub Actions 自动化：每天 UTC 00:00（北京时间 08:00）运行
- 📈 跟踪讨论热度、评论数等指标

## 🎯 探测平台与领域

### 国际平台 - Reddit

| Subreddit | 领域 |
|-----------|------|
| CivilEngineering | 土木工程 |
| Construction | 建筑施工 |
| QuantitySurveying | 工程造价/估算 |
| RealEstate | 房地产开发 |
| PropTech | 地产科技 |

### 中国平台

#### 知乎
- 建筑施工 难点
- 土木工程 痛点
- 工程造价 效率
- 施工管理 问题
- BIM 应用难题

#### 小红书
- 建筑设计
- 施工现场
- 工程管理

## 🚀 使用方法

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python detect_pain_points.py
```

### 自动化运行

本项目配置了 GitHub Actions，每天自动运行并更新报告：

1. Fork 本仓库
2. 确保仓库的 Settings > Actions > General > Workflow permissions 设置为 "Read and write permissions"
3. 每天自动生成的报告将保存在 `PAIN_POINTS_REPORT.md`

### 手动触发

在 GitHub 仓库的 "Actions" 标签页，选择 "Daily Pain Points Detection" 工作流，点击 "Run workflow" 即可手动触发。

## 📄 输出示例

查看 [PAIN_POINTS_REPORT.md](./PAIN_POINTS_REPORT.md) 了解实际输出格式。

## 🔧 自定义配置

编辑 `detect_pain_points.py` 中的以下部分：

```python
# 修改探测的 Reddit Subreddit
targets = {
    "YourSubreddit": "你的领域名称",
    # ...
}

# 修改 Reddit 搜索关键词
keywords = "(你的关键词 OR 'other keywords')"

# 修改知乎搜索关键词
zhihu_keywords = [
    "你的关键词1",
    "你的关键词2",
]

# 修改小红书搜索关键词
xhs_keywords = [
    "关键词1",
    "关键词2",
]
```

## ⚙️ GitHub Actions 配置

工作流配置文件位于 `.github/workflows/daily-detection.yml`

默认运行时间：每天 UTC 00:00（北京时间 08:00）

修改运行时间请编辑 cron 表达式：
```yaml
schedule:
  - cron: '0 0 * * *'  # 分 时 日 月 周
```

## ⚠️ 平台访问限制说明

### Reddit
✅ **当前可用** - 直接访问，无需认证
⚠️ 高频访问可能触发限流

**优化建议（可选）**：
1. 注册 Reddit App：https://www.reddit.com/prefs/apps
2. 获取 `client_id` 和 `client_secret`
3. 配置到 GitHub Secrets

### 知乎
⚠️ **需要认证** - 搜索API需要登录
📱 当前提供手动搜索链接

**优化建议**：
- 配置知乎 Cookie 到 GitHub Secrets: `ZHIHU_COOKIE`
- 或使用第三方知乎API服务

### 小红书
⚠️ **反爬虫严格** - 需要App登录
📱 当前提供手动搜索链接

**优化建议**：
- 直接使用小红书App搜索
- 或申请小红书官方API（需企业资质）

## 📝 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如有问题或建议，请访问：https://github.com/tomadam/pain_point_detector/issues
