# Evidence-Weighted Purchase Ranking

A reusable Codex skill for comparing marketplace listings using seller rating quality, review/feedback evidence, and seller sales history without confusing seller reputation with item value.

## Install in Codex

Run inside Codex:

```text
$skill-installer install https://github.com/future3OOO/evidence-weighted-purchase-ranking/tree/main/skills/evidence-weighted-purchase-ranking
```

Restart Codex after installation so the new skill is discovered.

## Invoke

```text
$evidence-weighted-purchase-ranking
```

The skill is model-invoked as well, so Codex can use it automatically when comparing marketplace listings where seller rating plus review/feedback or sales-volume evidence are available.

## What it does

The skill:

- separates item fit/value from seller confidence;
- Bayesian-shrinks thin seller ratings toward a marketplace/category prior;
- log-normalizes review and sales counts so evidence has diminishing returns;
- combines rating quality and evidence strength into a reproducible `SellerScore`;
- treats missing evidence as missing rather than observed failure;
- prevents listing-level sales from being mislabeled as seller-wide sales;
- supports marketplace-specific calibration and learned coefficients when historical outcomes are available.

See [`skills/evidence-weighted-purchase-ranking/SKILL.md`](skills/evidence-weighted-purchase-ranking/SKILL.md) for the runtime skill and [`CALIBRATION.md`](skills/evidence-weighted-purchase-ranking/references/CALIBRATION.md) for calibration guidance.
