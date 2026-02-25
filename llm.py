# llm.py
import os
import json
from openai import OpenAI

def get_client():
    # 你可以用 OPENAI_API_KEY 或 DEEPSEEK_API_KEY
    # 如果你用 deepseek：设置 DEEPSEEK_API_KEY，并把 BASE_URL 改成 https://api.deepseek.com
    api_key = "sk-bfb199cd27974a9180c3282dc9abce55"
    #api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    
    base_url = "https://api.deepseek.com"
    #base_url = os.getenv("LLM_BASE_URL")  # 为空则走 OpenAI 默认
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

client = get_client()

def generate_text(payload: dict, model: str | None = None) -> str:
    model = "deepseek-chat" #model or os.getenv("deepseek-chat", "gpt-4o-mini")

    data = json.dumps(payload, ensure_ascii=False)

    prompt = f"""
你是一名快消行业（食品饮料）商业分析负责人。你要基于给定数据，产出“每期定制化”的管理层报告：既有结论，也有可执行建议。
注意：不要泛泛而谈，不要写教科书；要像真实业务负责人一样，明确指出哪里最好/最差、为什么、下一步做什么。

【财年口径】
- FY 从 12月 到 次年11月
- Q1=12-2, Q2=3-5, Q3=6-8, Q4=9-11
- 数据按季度更新，但颗粒度是月度

【指标优先级】
销售额、销售量、单价（销额/销量）、加权铺货率、数值铺货率、单点卖力（销额/加权铺货率）

【分析结构（必须按此输出，中文）】
1）第一层：销额&份额及趋势
- 最新财季：该品牌销额、份额、份额同比pp
- 解释份额变化属于哪种情况（品牌增速 vs 大盘增速四象限），并说清楚“这意味着什么”
- 给出对月度销额/份额趋势的解读（不要说“见图”，要写趋势结论）

2）第二层：分省份下钻
- 最新财季：Top3 份额增长省份 / Top3 份额下跌省份（分别给原因）
- 用“份额 ≈ 卖力份额 x 加权铺货率”的框架做归因：是卖力驱动还是铺货驱动？
- 讨论单价对生意的可能影响（如果 price 为空，就说‘当前数据未提供销量/单价，无法判断单价影响’）

3）第三层：分渠道下钻
- 同省份逻辑：Top3 增长/下跌渠道 + 原因归因 + 单价影响判断

4）总结层：建议（要具体）
- 给出 5-8 条建议，按优先级排序
- 每条建议要包含：做什么 / 为什么 / 预期影响 / 风险点
- 建议要尽量落到“哪些省份/渠道/动作”，而不是抽象口号

下面是数据
【数据（JSON）】
{data}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return resp.choices[0].message.content