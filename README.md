# 客服工单趋势分析

这是 0111「客服工单趋势分析」测评题的第一版实现。

## 当前版本

- Python + pandas：数据处理与统计
- matplotlib：生成趋势和分布图
- 规则式异常检测：保证结论可解释、可复核
- Markdown：输出业务分析报告

## 运行

```bash
pip install -r requirements.txt
python src/analyze.py
```

运行后查看：

- `output/report.md`
- `output/summary.json`
- `output/charts/`

## 当前分析维度

1. 时间趋势
2. 问题类别
3. 优先级
4. 服务结果
5. 渠道

## 异常检测

当前采用可解释规则，例如：

- 某类别工单占比过高
- 某类别平均处理时长明显高于整体水平
- 高优先级工单满意度或解决率偏低
- 观察期前后满意度出现明显下降

后续可继续增加子问题聚类、异常工单详情和 HTML Dashboard。
