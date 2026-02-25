# run_report.py
import os, json
import pandas as pd
from analysis import build_insight
from llm import generate_text
from report import create_pdf

USE_CACHE = False
os.makedirs("outputs", exist_ok=True)
CACHE_PATH = "outputs/llm_text.json"

# 你想分析的品牌（按你 Excel 里的品牌名称精确填写）
BRAND = os.getenv("REPORT_BRAND", "外星人电解质水")  # 可在命令行设置 REPORT_BRAND 来切换

def to_sections(report_text: str):
    # MVP：先把 LLM 文本整体放进 PDF
    return [("执行摘要", report_text or "")]

# ✅ 改这里：读清洗后的数据
df = pd.read_csv("data/clean/nielsen_clean.csv")

# ✅ 改这里：新版 analysis.py 返回结构化 payload（给 LLM 用）
payload = build_insight(df, brand=BRAND)

# 可选：把 payload 也落盘，方便你调试（不耗 token）
with open("outputs/insight_payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

if USE_CACHE and os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        report_text = json.load(f)["report_text"]
    print("✅ 使用缓存的 LLM 文本")
else:
    report_text = generate_text(payload)
    print("✅ LLM 原始输出如下：\n")
    print(report_text)  # 你要的 print（调试用）
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"report_text": report_text}, f, ensure_ascii=False, indent=2)

sections = to_sections(report_text)

create_pdf(sections, out_path="outputs/Nielsen_Report.pdf")
print("✅ PDF 生成完成：outputs/Nielsen_Report.pdf")
print("✅ 本次分析品牌：", BRAND)