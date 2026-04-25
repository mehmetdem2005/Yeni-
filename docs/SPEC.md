# Crypto Spot Bot — Paper Trade Core v1.0

This repository contains a research and paper-trade core for a spot-only long-only crypto bot.

## Rules

- Spot only
- Long only
- Max open positions: 2
- ATR is not part of the entry score
- Only closed candles are used

## Timeframes

- W1: regime gate
- D1: direction gate
- H1: entry score

## Score

```text
Final Score = (EMA_Signal + RSI_Signal + MFI_Signal) / 3
```

Default threshold: 0.70. It should be calibrated in walk-forward tests.

## Risk

```text
Risk_Distance = ATR(14) * 1.5
SL = Entry - Risk_Distance
Raw_TP = Entry + Risk_Distance * 3
```

If resistance reduces the target, the actual reward/risk must stay at least 2.

## Position Size

```text
Position_Pct = 0.005 / Stop_Distance_Pct
Position_Pct = min(Position_Pct, 0.05)
```

If the computed position is below 0.005, the trade is skipped.

## Paper Execution

A touched limit level is not assumed filled. Visible book depth and a conservative queue factor are used.
