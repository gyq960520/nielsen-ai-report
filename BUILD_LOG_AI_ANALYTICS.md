# BUILD_LOG_AI_ANALYTICS.md

## AI 尼尔森自动分析系统搭建记录

---

# 一、尼尔森数据 Demo 流程架构

本项目目标是将传统 BI 看板升级为：

> 数据 → 自动诊断 → AI 生成洞察 → 自动生成 PDF 报告

实现商业分析能力的系统化与自动化。

---

## 🧠 整体流程结构

```
Nielsen 数据 (CSV)
        ↓
Python 数据处理层（pandas）
        ↓
分析规则引擎（六象限 / 结构化诊断）
        ↓
LLM 分析层（DeepSeek / OpenAI）
        ↓
文本缓存（避免重复消耗 token）
        ↓
PDF 渲染层（ReportLab + 中文字体）
        ↓
输出管理层报告
```

---

## ⚙ 技术栈

* 数据处理：pandas
* 分析规则：Python 函数逻辑
* AI 接口：OpenAI SDK / DeepSeek API
* 缓存机制：JSON 本地文件
* PDF 渲染：reportlab
* 字体支持：Windows simhei.ttf
* 版本管理：Git + GitHub
* 自动运行：GitHub Actions（已搭建）

---

## 🚀 实现步骤拆解

1. 创建 GitHub 仓库
2. VS Code 克隆到本地
3. 搭建核心模块：

   * analysis.py（规则判断）
   * llm.py（AI生成）
   * report.py（PDF渲染）
   * run_report.py（主流程）
4. 接入 API Key（使用 GitHub Secret 管理）
5. 加入缓存逻辑避免重复调用 LLM
6. 注册中文字体解决乱码
7. 实现分段 PDF 输出结构
8. 成功生成自动化管理报告

---

# 二、搭建过程中遇到的问题与解决方案

---

## Ⅰ. Git / 环境配置问题

### 1️⃣ Git 未配置 user.name / user.email

报错：

```
Make sure you configure your user.name and user.email
```

解决：

```
git config --global user.name "YourName"
git config --global user.email "youremail@email.com"
```

---

### 2️⃣ Push 很慢或卡住

原因：
Git 正在跟踪 data/nielsen.csv 等数据文件

解决：

创建 `.gitignore`

```
data/
.env
venv/
__pycache__/
```

执行：

```
git rm --cached -r data
```

原则：

> Git 只管理代码，不管理数据。

---

## Ⅱ. API / LLM 问题

### 3️⃣ 429 insufficient_quota

报错：

```
openai.RateLimitError: insufficient_quota
```

原因：
API 余额不足或未绑定计费

解决：

* 充值 OpenAI
* 或切换 DeepSeek API
* 使用 GitHub Secret 管理 API Key

---

### 4️⃣ 重复消耗 Token

问题：
每次调试 PDF 都会重新调用 LLM

解决：

加入缓存机制：

```
outputs/llm_text.json
```

逻辑：

* 若缓存存在 → 直接读取
* 若不存在 → 调用 LLM 并写入缓存

---

## Ⅲ. 代码结构问题

### 5️⃣ create_pdf 参数不匹配

报错：

```
unexpected keyword argument 'out_path'
```

原因：
run_report.py 与 report.py 版本不同步

解决：
统一函数签名：

```
def create_pdf(sections, out_path="Nielsen_Report.pdf")
```

---

### 6️⃣ PDF 中文乱码

原因：
ReportLab 默认字体不支持中文

解决：

注册 Windows 中文字体：

```
C:\Windows\Fonts\simhei.ttf
```

并指定 ParagraphStyle 使用该字体。

---

### 7️⃣ 换行无效

原因：
ReportLab Paragraph 不识别 \n

解决：

```
text.replace("\n", "<br/>")
```

---

## Ⅳ. 工程结构升级

### 8️⃣ 拆分 PDF 渲染结构

从单文本：

```
create_pdf(text)
```

升级为：

```
sections = [(标题, 内容), ...]
create_pdf(sections)
```

实现：

* 分段打印
* 未来支持分页
* 支持插入图表
* 支持品牌单页输出

---

# 三、当前系统能力

目前系统已实现：

* 自动读取尼尔森 CSV
* 自动规则判断
* AI 生成管理层分析
* 本地缓存避免重复消耗 token
* 中文 PDF 输出
* 分段渲染结构
* GitHub 版本管理

---

# 四、未来升级方向

* 自动识别异常变化并高亮
* 插入 matplotlib 图表
* 每品牌单独分页
* 定时自动运行（GitHub Actions）
* 输出结构化 JSON
* 构建 SaaS 版本

---

# 五、个人总结

本系统的本质不是“自动写报告”，而是：

> 将个人商业分析能力产品化。

从：

人工看数据 → 手写报告

升级为：

数据驱动 → AI 分析 → 自动输出

这是分析能力的结构化升级。

---

# 版本记录建议

```
v0.1 基础生成
v0.2 分段渲染
v0.3 图表插入
v1.0 自动部署
```

---

## 结语

今天完成的不是一次调试，而是：

> 搭建了一个可持续进化的 AI 商业分析系统雏形。

从使用工具的人，进化为构建系统的人。

---

（记录时间：2026-02-25）
