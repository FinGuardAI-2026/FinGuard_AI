# FinGuard AI – Feature Selection & Engineering Report

## Resampling Balancing Strategies Comparison

| Strategy | Train Shape | Genuine Count | Fraud Count | Ratio |
| :--- | :--- | :--- | :--- | :--- |
| Original | (227845, 5) | 227,451 | 394 | 1:577 |
| Random Over Sampler (ROS) | (454902, 5) | 227,451 | 227,451 | 1:1 |
| Random Under Sampler (RUS) | (788, 5) | 394 | 394 | 1:1 |

- **Recommended Resampling Strategy**: `RANDOM_OVER_SAMPLING`

## Feature Relevance Rankings (Mutual Information)

| Rank | Feature Name | Mutual Information Score |
| :--- | :--- | :--- |
| 1 | `amount` | 0.001532 |

- **Dropped Constant Columns**: []
- **Dropped Collinear Columns**: []
