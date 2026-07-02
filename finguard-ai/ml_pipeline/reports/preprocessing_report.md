# FinGuard AI – Data Preprocessing Report

- **Total Rows Deduplicated**: 0
- **Final Preprocessing Shape**: (284807, 7)

## Outlier Capping Comparison

| Feature | Method | Lower Bound | Upper Bound | Records Capped |
| :--- | :--- | :--- | :--- | :--- |
| `amount` | IQR Capper | -102.13 | 185.26 | 25,476 |
| `amount` | Winsorizer (1%-99%) | 0.12 | 1012.34 | 4,499 |

## Scaling Performance Comparison

### Feature: `amount`
- **Raw Range**: `[0.00, 25691.16]`
- **StandardScaler**: Range `[-0.35, 102.12]` (Mean: -0.00, Std: 1.00)
- **MinMaxScaler**: Range `[0.00, 1.00]` (Mean: 0.00, Std: 0.01)
- **RobustScaler**: Median centered near `0.00`, Range `[-0.31, 357.26]`

### Scaler Recommendation
- **Recommended Scaler**: `ROBUST`
> [!TIP]
> **RobustScaler** is recommended because transaction amount displays extreme outlier ranges which would shrink variance of standard scales down to near-zero.
