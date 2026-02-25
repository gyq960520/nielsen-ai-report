import pandas as pd

def classify_market(brand_growth, category_growth):

    if brand_growth > 0 and category_growth > 0:
        return "增量优势"
    elif brand_growth < 0 and category_growth > 0:
        return "增量竞争"
    elif brand_growth > 0 and category_growth < 0:
        return "存量优势"
    else:
        return "存量问题"


def build_insight(df):

    insights = []

    category_growth = 5  # MVP阶段先写死（后面自动算）

    for _, row in df.iterrows():

        brand_growth = (
            row["brand_sales"] - row["last_brand_sales"]
        ) / row["last_brand_sales"] * 100

        diagnosis = classify_market(brand_growth, category_growth)

        insights.append({
            "brand": row["brand"],
            "brand_growth": round(brand_growth,2),
            "distribution_change":
                row["distribution"] - row["last_distribution"],
            "diagnosis": diagnosis
        })

    return insights

