# report.py
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

def _register_zh_font() -> str:
    # Windows 常见字体：黑体（最稳）
    font_path = r"C:\Windows\Fonts\simhei.ttf"
    if not os.path.exists(font_path):
        raise RuntimeError("未找到中文字体 simhei.ttf。请确认 C:\\Windows\\Fonts\\simhei.ttf 存在。")

    pdfmetrics.registerFont(TTFont("ZH", font_path))
    return "ZH"

def _escape_for_paragraph(s: str) -> str:
    # Paragraph 需要转义 + <br/> 换行
    s = (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.replace("\n", "<br/>")

def create_pdf(sections, out_path="Nielsen_Report.pdf"):
    """
    sections: [(标题, 正文), (标题, 正文), ...]
    这样就天然实现“拆分PDF打印”的能力（逐段写入）。
    """
    font_name = _register_zh_font()

    doc = SimpleDocTemplate(out_path, pagesize=A4)
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ZhTitle",
        parent=base_styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )

    h2_style = ParagraphStyle(
        "ZhH2",
        parent=base_styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ZhBody",
        parent=base_styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
    )

    story = []
    story.append(Paragraph("尼尔森 市场分析报告", title_style))
    story.append(Spacer(1, 12))

    # 分段写入（你要的“拆分打印”就在这里）
    for sec_title, sec_body in sections:
        if sec_title:
            story.append(Paragraph(_escape_for_paragraph(sec_title), h2_style))
        if sec_body:
            story.append(Paragraph(_escape_for_paragraph(sec_body), body_style))
        story.append(Spacer(1, 10))

    doc.build(story)