from openai import OpenAI
from config import API_KEY
import os

client = OpenAI(api_key=API_KEY,    
                base_url="https://api.deepseek.com")

def generate_text(insights):

    prompt = f"""
你是一名快消行业商业分析负责人。
根据以下市场数据生成管理层月报总结。

数据：
{insights}

请输出：
1. 总体市场判断
2. 关键问题
3. 建议动作（可执行）
语言风格：专业但自然。
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def main():
    # 内部调用即可
    generate_text()