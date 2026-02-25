# run_report.py
import os, json
import pandas as pd
from analysis import build_insight
from llm import generate_text
from report import create_pdf


USE_CACHE = True
os.makedirs("outputs", exist_ok=True)
CACHE_PATH = "outputs/llm_text.json"

def to_sections(report_text: str):
    return [("执行摘要", report_text)]

df = pd.read_csv("data/nielsen.csv")
insights = build_insight(df)

if USE_CACHE and os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        report_text = json.load(f)["report_text"]
    print("✅ 使用缓存的 LLM 文本")
else:
    report_text = generate_text(insights)
    print("✅ LLM 原始输出如下：\n")
    print(report_text)  # 你要的 print（调试用）
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"report_text": report_text}, f, ensure_ascii=False, indent=2)

sections = to_sections(report_text)

create_pdf(sections, out_path="outputs/Nielsen_Report.pdf")
print("✅ PDF 生成完成：outputs/Nielsen_Report.pdf")