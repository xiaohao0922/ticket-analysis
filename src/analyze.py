from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "tickets.json"
OUTPUT_DIR = ROOT / "output"
CHART_DIR = OUTPUT_DIR / "charts"

plt.rcParams["font.family"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False


def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def save_chart(fig, filename):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(CHART_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def pct(value):
    return f"{value * 100:.1f}%"


def build_report(df, category, priority, daily, channel, focus):
    total = len(df)
    avg_time = df["resolution_time_hours"].mean()
    avg_sat = df["satisfaction"].mean()
    resolution_rate = df["is_resolved"].mean()

    lines = [
        "# 客服工单趋势分析报告",
        "",
        "## 1. 数据概览",
        "",
        f"- 工单总数：**{total}**",
        f"- 平均处理时长：**{avg_time:.2f} 小时**",
        f"- 平均满意度：**{avg_sat:.2f} / 5**",
        f"- 整体解决率：**{pct(resolution_rate)}**",
        f"- 高优先级工单占比：**{pct((df['priority'] == '高').mean())}**",
        "",
        "## 2. 核心发现",
        "",
    ]

    # Category finding
    top_category = category.index[0]
    top_count = int(category.loc[top_category, "count"])
    slow_category = category["avg_time"].idxmax()
    low_sat_category = category["avg_sat"].idxmin()
    low_resolution_category = category["resolution_rate"].idxmin()

    lines += [
        f"### 2.1 工单主要集中在「{top_category}」",
        "",
        f"「{top_category}」共有 {top_count} 条，占全部工单 {pct(top_count / total)}。",
        "",
        f"### 2.2 「{slow_category}」处理时长最高",
        "",
        f"该类别平均处理时长为 {category.loc[slow_category, 'avg_time']:.2f} 小时，"
        f"明显高于整体平均 {avg_time:.2f} 小时。",
        "",
        f"### 2.3 「{low_sat_category}」满意度最低",
        "",
        f"该类别平均满意度为 {category.loc[low_sat_category, 'avg_sat']:.2f} / 5。",
        "",
        f"### 2.4 「{low_resolution_category}」解决率最低",
        "",
        f"该类别解决率为 {pct(category.loc[low_resolution_category, 'resolution_rate'])}。",
        "",
        "### 2.5 高优先级工单值得重点关注",
        "",
        f"高优先级工单共 {int((df['priority'] == '高').sum())} 条，"
        f"平均处理时长 {priority.loc['高', 'avg_time']:.2f} 小时，"
        f"平均满意度 {priority.loc['高', 'avg_sat']:.2f} / 5，"
        f"解决率 {pct(priority.loc['高', 'resolution_rate'])}。",
        "",
        "## 3. 异常信号",
        "",
    ]

    for item in focus:
        lines += [
            f"### {item['level']} · {item['title']}",
            "",
            item["reason"],
            "",
        ]

    lines += [
        "## 4. 分类指标",
        "",
        "| 类别 | 工单数 | 平均处理时长(h) | 平均满意度 | 解决率 |",
        "|---|---:|---:|---:|---:|",
    ]
    for idx, row in category.iterrows():
        lines.append(
            f"| {idx} | {int(row['count'])} | {row['avg_time']:.2f} | "
            f"{row['avg_sat']:.2f} | {pct(row['resolution_rate'])} |"
        )

    lines += [
        "",
        "## 5. 优先级指标",
        "",
        "| 优先级 | 工单数 | 平均处理时长(h) | 平均满意度 | 解决率 |",
        "|---|---:|---:|---:|---:|",
    ]
    for idx, row in priority.iterrows():
        lines.append(
            f"| {idx} | {int(row['count'])} | {row['avg_time']:.2f} | "
            f"{row['avg_sat']:.2f} | {pct(row['resolution_rate'])} |"
        )

    lines += [
        "",
        "## 6. 重点工单",
        "",
        "| 工单 | 类别 | 优先级 | 处理时长(h) | 满意度 | 已解决 |",
        "|---|---|---|---:|---:|---|",
    ]
    for _, row in df.sort_values(
        ["satisfaction", "is_resolved", "resolution_time_hours"],
        ascending=[True, True, False],
    ).head(5).iterrows():
        lines.append(
            f"| {row['ticket_id']} | {row['category']} | {row['priority']} | "
            f"{row['resolution_time_hours']:.1f} | {row['satisfaction']} | "
            f"{'是' if row['is_resolved'] else '否'} |"
        )

    lines += [
        "",
        "## 7. 建议",
        "",
        "1. 优先复盘退款退货相关流程，重点关注长处理时长和未解决工单。",
        "2. 对支付问题持续监控，区分重复扣款、支付成功但订单异常等子问题。",
        "3. 对高优先级且低满意度/未解决工单建立升级机制。",
        "4. 将低满意度工单与问题类别、渠道、处理时长联动分析，定位服务质量问题。",
        "",
        "## 8. 局限性",
        "",
        "- 当前样本只有 50 条工单，结论只能反映本批数据，不能直接代表长期趋势。",
        "- 数据覆盖时间约 11 天，无法判断周周期、月周期或季节性。",
        "- `category` 已由业务预先标注，本分析没有进一步从用户原文识别潜在新问题。",
        "- 渠道之间的问题类型可能不同，因此渠道差异只能作为关联信号，不能直接解释为因果关系。",
        "- 当前异常检测采用可解释规则，不代表统计学意义上的正式异常检测模型。",
        "",
    ]
    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    category = df.groupby("category").agg(
        count=("ticket_id", "count"),
        avg_time=("resolution_time_hours", "mean"),
        avg_sat=("satisfaction", "mean"),
        resolution_rate=("is_resolved", "mean"),
    ).sort_values("count", ascending=False)

    priority_order = ["高", "中", "低"]
    priority = df.groupby("priority").agg(
        count=("ticket_id", "count"),
        avg_time=("resolution_time_hours", "mean"),
        avg_sat=("satisfaction", "mean"),
        resolution_rate=("is_resolved", "mean"),
    ).reindex(priority_order)

    channel = df.groupby("channel").agg(
        count=("ticket_id", "count"),
        avg_time=("resolution_time_hours", "mean"),
        avg_sat=("satisfaction", "mean"),
        resolution_rate=("is_resolved", "mean"),
    )

    daily = df.groupby(df["created_at"].dt.date).agg(
        count=("ticket_id", "count"),
        avg_time=("resolution_time_hours", "mean"),
        avg_sat=("satisfaction", "mean"),
        resolution_rate=("is_resolved", "mean"),
    )

    # 1. Daily ticket volume
    fig, ax = plt.subplots(figsize=(9, 5))
    daily["count"].plot(kind="line", marker="o", ax=ax)
    ax.set_title("每日工单量")
    ax.set_xlabel("日期")
    ax.set_ylabel("工单数")
    ax.grid(alpha=0.25)
    save_chart(fig, "daily_ticket_trend.png")

    # 2. Daily satisfaction
    fig, ax = plt.subplots(figsize=(9, 5))
    daily["avg_sat"].plot(kind="line", marker="o", ax=ax)
    ax.axhline(df["satisfaction"].mean(), linestyle="--", label="整体平均")
    ax.set_title("每日平均满意度")
    ax.set_xlabel("日期")
    ax.set_ylabel("满意度")
    ax.set_ylim(1, 5)
    ax.legend()
    ax.grid(alpha=0.25)
    save_chart(fig, "daily_satisfaction_trend.png")

    # 3. Category distribution
    fig, ax = plt.subplots(figsize=(9, 5))
    category["count"].sort_values().plot(kind="barh", ax=ax)
    ax.set_title("工单类别分布")
    ax.set_xlabel("工单数")
    ax.set_ylabel("类别")
    ax.grid(axis="x", alpha=0.25)
    save_chart(fig, "category_distribution.png")

    # 4. Category metrics
    fig, ax = plt.subplots(figsize=(9, 5))
    category["avg_sat"].sort_values().plot(kind="barh", ax=ax)
    ax.set_title("各类别平均满意度")
    ax.set_xlabel("平均满意度")
    ax.set_ylabel("类别")
    ax.set_xlim(0, 5)
    ax.grid(axis="x", alpha=0.25)
    save_chart(fig, "category_satisfaction.png")

    # 5. Priority metrics
    fig, ax = plt.subplots(figsize=(8, 5))
    priority["avg_time"].plot(kind="bar", ax=ax)
    ax.set_title("不同优先级平均处理时长")
    ax.set_xlabel("优先级")
    ax.set_ylabel("小时")
    ax.grid(axis="y", alpha=0.25)
    save_chart(fig, "priority_resolution_time.png")

    # Rule-based anomaly signals
    overall_avg_time = df["resolution_time_hours"].mean()
    focus = []

    pay = category.loc["支付问题"]
    if pay["count"] / len(df) >= 0.25:
        focus.append({
            "level": "高关注",
            "title": "支付问题占比较高",
            "reason": f"支付问题 {int(pay['count'])} 条，占比 {pct(pay['count']/len(df))}，是样本中数量最多的类别。"
        })

    refund = category.loc["退款退货"]
    if refund["avg_time"] > overall_avg_time * 2:
        focus.append({
            "level": "高关注",
            "title": "退款退货处理时长明显偏高",
            "reason": f"退款退货平均处理时长 {refund['avg_time']:.2f} 小时，"
                       f"约为整体平均 {overall_avg_time:.2f} 小时的 {refund['avg_time']/overall_avg_time:.1f} 倍，"
                       f"同时解决率仅为 {pct(refund['resolution_rate'])}。"
        })

    high = priority.loc["高"]
    if high["avg_sat"] < 2.5 or high["resolution_rate"] < 0.8:
        focus.append({
            "level": "高关注",
            "title": "高优先级工单结果偏弱",
            "reason": f"高优先级工单平均满意度 {high['avg_sat']:.2f}，"
                       f"解决率 {pct(high['resolution_rate'])}，两项均低于理想水平。"
        })

    late = daily.tail(3)["avg_sat"].mean()
    early = daily.head(3)["avg_sat"].mean()
    if late < early - 0.8:
        focus.append({
            "level": "关注",
            "title": "观察期后段满意度下降",
            "reason": f"前3天平均满意度 {early:.2f}，后3天为 {late:.2f}，"
                       f"下降 {early-late:.2f} 分。样本期较短，因此这里只作为趋势信号。"
        })

    report = build_report(df, category, priority, daily, channel, focus)
    (OUTPUT_DIR / "report.md").write_text(report, encoding="utf-8")

    # Also save machine-readable summaries for later extension.
    summary = {
        "total_tickets": int(len(df)),
        "avg_resolution_time_hours": round(float(df["resolution_time_hours"].mean()), 2),
        "avg_satisfaction": round(float(df["satisfaction"].mean()), 2),
        "resolution_rate": round(float(df["is_resolved"].mean()), 4),
        "category": category.reset_index().to_dict(orient="records"),
        "priority": priority.reset_index().to_dict(orient="records"),
        "channel": channel.reset_index().to_dict(orient="records"),
        "focus_signals": focus,
    }
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Analysis completed.")
    print(f"Report: {OUTPUT_DIR / 'report.md'}")
    print(f"Charts: {CHART_DIR}")


if __name__ == "__main__":
    main()
