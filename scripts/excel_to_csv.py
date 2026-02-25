# scripts/excel_to_csv.py
import os
import re
import pandas as pd

PROVINCES = {
    "北京","天津","上海","重庆","河北","山西","辽宁","吉林","黑龙江","江苏","浙江","安徽","福建","江西","山东",
    "河南","湖北","湖南","广东","海南","四川","贵州","云南","陕西","甘肃","青海","内蒙古","广西","西藏",
    "宁夏","新疆","香港","澳门","台湾"
}

CHANNEL_HINTS = {
    "现代渠道","传统渠道","电商","餐饮","便利店","超市","大卖场","KA","CVS","GT","MT","O2O","社区团购","线上","线下"
}

def parse_market(market: str) -> dict:
    """
    市场字段示例：
      - 全国/东部/安徽/CN
      - 全国/现代渠道/超市/CN
    输出：大区、省份、渠道（尽量解析；解析不到就为空）
    """
    market = str(market) if market is not None else ""
    parts = [p.strip() for p in market.split("/") if p.strip()]
    # 去掉末尾 CN
    if parts and parts[-1].upper() == "CN":
        parts = parts[:-1]

    area = ""
    province = ""
    channel = ""

    # 经验：parts[0] 常是 全国
    for p in parts:
        if p in PROVINCES:
            province = p

    # 找渠道：优先匹配 CHANNEL_HINTS，其次取最后一段（但不等于省份）
    for p in parts:
        if p in CHANNEL_HINTS:
            channel = p

    if not channel and len(parts) >= 2:
        last = parts[-1]
        if last not in PROVINCES and last != "全国":
            channel = last

    # 大区：通常是 全国之后的第一个，且不是渠道/省份
    if len(parts) >= 2:
        cand = parts[1]
        if cand not in PROVINCES and cand not in CHANNEL_HINTS:
            area = cand

    return {"area": area, "province": province, "channel": channel, "market_raw": market}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    将不同来源/中文列名对齐到统一英文列名
    """
    colmap = {
        "日期": "date",
        "市场": "market",
        "品牌": "brand",
        "品类": "category",
        "销售额（千元）": "sales_value_k",
        "销售额": "sales_value",
        "销售额份额": "share_value_pct",
        "销量": "sales_volume",
        "销售量": "sales_volume",
        "最大加权销售铺货率": "wdist_pct",
        "最大数值销售铺货率": "ndist_pct",
        "数值铺货率": "ndist_pct",
        "加权铺货率": "wdist_pct",
        "单点销售额指数(销售额/加权铺货)": "velocity_value",
        "单点卖力": "velocity_value",
    }

    new_cols = {}
    for c in df.columns:
        c2 = str(c).strip()
        new_cols[c] = colmap.get(c2, c2)
    df = df.rename(columns=new_cols)

    # 日期
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df

def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一计算你关注的指标：
    - sales_value（销额）
    - sales_volume（销量，可选）
    - price = sales_value / sales_volume（可选）
    - wdist_pct（加权铺货率）
    - ndist_pct（数值铺货率）
    - velocity_value = sales_value / wdist_pct（单点卖力：销额/加权铺货率）
    """
    # 销额统一到 sales_value（元口径不强行统一；你后面可在这里乘1000等）
    if "sales_value" not in df.columns:
        if "sales_value_k" in df.columns:
            # 这里保留“千元”口径为 sales_value_k，同时也生成一个 sales_value（千元）
            df["sales_value"] = df["sales_value_k"]
        else:
            df["sales_value"] = pd.NA

    # 铺货率统一
    for c in ["wdist_pct", "ndist_pct", "share_value_pct"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 销量可选
    if "sales_volume" in df.columns:
        df["sales_volume"] = pd.to_numeric(df["sales_volume"], errors="coerce")
    else:
        df["sales_volume"] = pd.NA

    # 单价
    df["price"] = pd.NA
    if df["sales_volume"].notna().any():
        df["price"] = df["sales_value"] / df["sales_volume"]

    # 单点卖力（销额/加权铺货率）
    df["velocity_value_calc"] = pd.NA
    if "wdist_pct" in df.columns:
        # 注意：wdist_pct 是百分数（0-100），这里用“每1个百分点铺货对应的销额”口径
        df["velocity_value_calc"] = df["sales_value"] / df["wdist_pct"]

    # 如果原始就有 velocity_value，用原始；否则用计算值
    if "velocity_value" not in df.columns:
        df["velocity_value"] = df["velocity_value_calc"]
    else:
        df["velocity_value"] = pd.to_numeric(df["velocity_value"], errors="coerce")
        df["velocity_value"] = df["velocity_value"].fillna(df["velocity_value_calc"])

    return df

def main(
    input_path: str = "data/raw/nielsen.xlsx",
    output_path: str = "data/clean/nielsen_clean.csv",
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    xl = pd.ExcelFile(input_path)
    # 默认取第一个 sheet；你也可以按名字选择
    df = xl.parse(xl.sheet_names[0])
    df = normalize_columns(df)

    # 解析市场维度
    if "market" in df.columns:
        parsed = df["market"].apply(parse_market).apply(pd.Series)
        df = pd.concat([df, parsed], axis=1)
    else:
        df["market_raw"] = ""
        df["area"] = ""
        df["province"] = ""
        df["channel"] = ""

    df = compute_metrics(df)

    # 输出你后续分析需要的“规范字段”
    keep = [
        "date","brand","category","market_raw","area","province","channel",
        "sales_value","sales_volume","price",
        "share_value_pct","wdist_pct","ndist_pct","velocity_value"
    ]
    for k in keep:
        if k not in df.columns:
            df[k] = pd.NA

    df_out = df[keep].copy()
    df_out.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"✅ 输出完成: {output_path}")
    print(f"Rows: {len(df_out):,}")

if __name__ == "__main__":
    main()