# analysis.py
import pandas as pd
import numpy as np
from dataclasses import dataclass

def fiscal_year(date: pd.Timestamp) -> int:
    # 财年：12月-次年11月。用“财年结束年”命名：Dec 2024 -> FY2025
    if pd.isna(date):
        return np.nan
    return date.year + 1 if date.month == 12 else date.year

def fiscal_quarter(date: pd.Timestamp) -> str:
    # Q1: Dec-Feb, Q2: Mar-May, Q3: Jun-Aug, Q4: Sep-Nov
    if pd.isna(date):
        return ""
    m = date.month
    if m in (12, 1, 2):
        return "Q1"
    if m in (3, 4, 5):
        return "Q2"
    if m in (6, 7, 8):
        return "Q3"
    return "Q4"

def add_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["fy"] = df["date"].apply(fiscal_year)
    df["fq"] = df["date"].apply(fiscal_quarter)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df

def _safe_div(a, b):
    return np.where((b == 0) | pd.isna(b), np.nan, a / b)

def build_brand_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    你 demo 里有 share_value_pct 和 sales_value。
    用它估算 category_sales（避免必须提供品类总销额）：
      category_sales = brand_sales / (share/100)
    """
    df = df.copy()
    df["sales_value"] = pd.to_numeric(df["sales_value"], errors="coerce")
    df["share_value_pct"] = pd.to_numeric(df["share_value_pct"], errors="coerce")

    df["category_sales_value"] = df["sales_value"] / (df["share_value_pct"] / 100.0)
    return df

def agg_period(df: pd.DataFrame, keys: list[str], period_key: str) -> pd.DataFrame:
    """
    period_key: 'fq' or 'month'
    聚合字段：销额、销量、铺货率（简单加权/取平均策略可再迭代）
    """
    g = df.groupby(keys + [period_key], dropna=False).agg(
        sales_value=("sales_value", "sum"),
        sales_volume=("sales_volume", "sum"),
        category_sales_value=("category_sales_value", "sum"),
        # 铺货率类一般不求和，这里先取均值（你后续可按门店权重做更严谨加权）
        wdist_pct=("wdist_pct", "mean"),
        ndist_pct=("ndist_pct", "mean"),
    ).reset_index()

    g["share_value_pct"] = g["sales_value"] / g["category_sales_value"] * 100.0
    g["price"] = np.where(g["sales_volume"] > 0, g["sales_value"] / g["sales_volume"], np.nan)
    g["velocity_value"] = np.where(g["wdist_pct"] > 0, g["sales_value"] / g["wdist_pct"], np.nan)
    return g

def yoy_change(cur, last):
    return cur - last

def classify_share_move(brand_growth, cat_growth):
    """
    份额变化解释的 4 种情况（基于“品牌增速 vs 大盘增速”）
    brand_growth, cat_growth: 同比增速（%）
    """
    if pd.isna(brand_growth) or pd.isna(cat_growth):
        return "无法判断（缺少同比基期）"
    if brand_growth >= cat_growth and cat_growth >= 0:
        return "份额提升：品牌增长快于大盘"
    if brand_growth >= 0 and cat_growth < 0:
        return "份额提升：品牌下滑慢于大盘（相对更强）"
    if brand_growth < cat_growth and cat_growth >= 0:
        return "份额下跌：品牌增长慢于大盘"
    return "份额下跌：品牌下滑快于大盘（相对更弱）"

def decompose_share_change(df_agg: pd.DataFrame, dim: str, brand: str, fy: int):
    """
    按省份/渠道：输出 top3 份额增长 & 下跌
    拆解：销额份额 = 卖力份额 x 加权铺货率(相对/绝对)
    这里的“卖力份额”定义：
      velocity_share = brand_velocity / category_velocity
    category_velocity = category_sales / category_wdist
    brand_velocity = brand_sales / brand_wdist
    """
    d = df_agg.copy()
    d = d[(d["brand"] == brand) & (d["fy"] == fy)]

    # 取最新季度作为“最新季度”，同时做同比：同财年同季度 -1
    latest_fq = d["fq"].dropna().sort_values().iloc[-1] if d["fq"].notna().any() else None
    cur = d[d["fq"] == latest_fq].copy()

    # 去年同财年：fy-1，且同 fq
    last = df_agg[(df_agg["brand"] == brand) & (df_agg["fy"] == fy - 1) & (df_agg["fq"] == latest_fq)].copy()

    if cur.empty or last.empty:
        return {
            "latest_fq": latest_fq,
            "top_up": [],
            "top_down": [],
            "table": []
        }

    cur = cur.set_index(dim)
    last = last.set_index(dim)

    # 对齐
    idx = cur.index.union(last.index)
    cur = cur.reindex(idx)
    last = last.reindex(idx)

    # 计算份额同比变化（pp）
    cur_share = cur["share_value_pct"]
    last_share = last["share_value_pct"]
    share_pp = cur_share - last_share

    # 拆解项：品牌/品类卖力、铺货
    cur_cat_vel = cur["category_sales_value"] / cur["wdist_pct"]
    last_cat_vel = last["category_sales_value"] / last["wdist_pct"]
    cur_brand_vel = cur["sales_value"] / cur["wdist_pct"]
    last_brand_vel = last["sales_value"] / last["wdist_pct"]

    cur_vel_share = cur_brand_vel / cur_cat_vel
    last_vel_share = last_brand_vel / last_cat_vel

    # “铺货率贡献”这里先用 wdist_pct 的同比变化作为近似（后续可做对数拆解）
    wdist_pp = cur["wdist_pct"] - last["wdist_pct"]
    vel_share_pp = (cur_vel_share - last_vel_share) * 100.0  # 变成可读的点数

    out = pd.DataFrame({
        dim: idx,
        "cur_sales_value": cur["sales_value"],
        "cur_share": cur_share,
        "last_share": last_share,
        "share_pp": share_pp,
        "cur_wdist": cur["wdist_pct"],
        "wdist_pp": wdist_pp,
        "vel_share_pp": vel_share_pp,
        "cur_price": cur["price"],
    }).reset_index(drop=True)

    out = out.replace([np.inf, -np.inf], np.nan)

    top_up = out.sort_values("share_pp", ascending=False).head(3)
    top_down = out.sort_values("share_pp", ascending=True).head(3)

    # 表格：归因用（示意版）
    table = out.sort_values("cur_sales_value", ascending=False).head(30)

    return {
        "latest_fq": latest_fq,
        "top_up": top_up.to_dict(orient="records"),
        "top_down": top_down.to_dict(orient="records"),
        "table": table.to_dict(orient="records")
    }

def build_insight(df: pd.DataFrame, brand: str) -> dict:
    """
    产出：给 LLM 的结构化 payload
    """
    df = add_time_fields(df)
    df = build_brand_category(df)

    # 先聚合“总览”：按 brand + fq / month（不区分省份/渠道）
    base = df.copy()
    # 只保留“全国级/不带省份的行”可能更合理，但你的数据来源可能不同，这里先不过滤
    agg_fq = agg_period(base, keys=["brand"], period_key="fq")
    agg_m = agg_period(base, keys=["brand"], period_key="month")

    # 补 fy/fq 到聚合表
    # fq 聚合：用原始 df 的 fy 对应 fq 的最近值（简化）
    # 更严谨：fq 本身属于财年，这里按日期映射
    fq_map = df.dropna(subset=["fq","fy"])[["fq","fy"]].drop_duplicates().set_index("fq")["fy"].to_dict()
    agg_fq["fy"] = agg_fq["fq"].map(fq_map)

    # 取最新财年、最新季度
    brand_fq = agg_fq[agg_fq["brand"] == brand].dropna(subset=["fy","fq"]).copy()
    latest_fy = int(brand_fq["fy"].max()) if not brand_fq.empty else None
    latest_fq = brand_fq[brand_fq["fy"] == latest_fy]["fq"].iloc[-1] if latest_fy else None

    cur = brand_fq[(brand_fq["fy"] == latest_fy) & (brand_fq["fq"] == latest_fq)]
    last = brand_fq[(brand_fq["fy"] == latest_fy - 1) & (brand_fq["fq"] == latest_fq)] if latest_fy else pd.DataFrame()

    # 总览指标
    if not cur.empty:
        cur_row = cur.iloc[0]
        cur_sales = float(cur_row["sales_value"]) if pd.notna(cur_row["sales_value"]) else None
        cur_share = float(cur_row["share_value_pct"]) if pd.notna(cur_row["share_value_pct"]) else None
    else:
        cur_sales, cur_share = None, None

    share_pp = None
    brand_growth = None
    cat_growth = None
    share_story = "无法判断（缺少同比基期）"

    if not cur.empty and not last.empty:
        last_row = last.iloc[0]
        share_pp = float(cur_row["share_value_pct"] - last_row["share_value_pct"])
        brand_growth = float((cur_row["sales_value"] - last_row["sales_value"]) / last_row["sales_value"] * 100.0) if last_row["sales_value"] else None
        cat_growth = float((cur_row["category_sales_value"] - last_row["category_sales_value"]) / last_row["category_sales_value"] * 100.0) if last_row["category_sales_value"] else None
        share_story = classify_share_move(brand_growth, cat_growth)

    # 月度趋势（用于画图）
    m = agg_m[agg_m["brand"] == brand].copy().sort_values("month")
    monthly_trend = m[["month","sales_value","share_value_pct"]].to_dict(orient="records")

    # 省份下钻：对原始 df 先过滤省份非空，再按 fy+fq+province 聚合
    df_prov = df[df["province"].astype(str).str.len() > 0].copy()
    agg_prov = agg_period(df_prov, keys=["brand","province"], period_key="fq")
    agg_prov["fy"] = agg_prov["fq"].map(fq_map)

    prov_res = decompose_share_change(agg_prov.assign(fy=agg_prov["fy"]), dim="province", brand=brand, fy=latest_fy) if latest_fy else {}

    # 渠道下钻：过滤 channel 非空且 province 为空（尽量避免混维）
    df_ch = df[(df["channel"].astype(str).str.len() > 0) & ~(df["province"].astype(str).str.len() > 0)].copy()
    agg_ch = agg_period(df_ch, keys=["brand","channel"], period_key="fq")
    agg_ch["fy"] = agg_ch["fq"].map(fq_map)

    ch_res = decompose_share_change(agg_ch.assign(fy=agg_ch["fy"]), dim="channel", brand=brand, fy=latest_fy) if latest_fy else {}

    return {
        "brand": brand,
        "latest_fy": latest_fy,
        "latest_fq": latest_fq,
        "overview": {
            "latest_quarter_sales_value": cur_sales,
            "latest_quarter_share_value_pct": cur_share,
            "share_yoy_pp": share_pp,
            "brand_sales_yoy_pct": brand_growth,
            "category_sales_yoy_pct": cat_growth,
            "share_story": share_story,
        },
        "monthly_trend": monthly_trend,
        "province_drilldown": prov_res,
        "channel_drilldown": ch_res,
        "metric_definition": {
            "sales_value": "销售额",
            "sales_volume": "销售量",
            "price": "单价=销额/销量",
            "wdist_pct": "加权铺货率",
            "ndist_pct": "数值铺货率",
            "velocity_value": "单点卖力=销额/加权铺货率（百分点口径）",
            "share_value_pct": "销额份额",
            "share_decompose": "销额份额 = 卖力份额 x 加权铺货率（近似拆解）"
        }
    }