# Evidence-Weighted Purchase Ranking

A reusable Codex skill that **calculates** marketplace purchase rankings from variant-specific delivered value, product/listing evidence, and seller evidence. It is designed to prevent qualitative recommendation drift: the agent must extract inputs, show intermediate scores, rank candidates, and name one winner.

## Install in Codex

`$skill-installer` is a **Codex skill invocation, not a Bash command**.

From your terminal, start Codex:

```bash
codex
```

Then at the Codex prompt enter:

```text
$skill-installer install https://github.com/future3OOO/evidence-weighted-purchase-ranking/tree/main/skills/evidence-weighted-purchase-ranking
```

Restart Codex after installation if the new skill is not discovered immediately.

### Direct shell installation

```bash
set -e
repo_tmp="$(mktemp -d)"
dest="${CODEX_HOME:-$HOME/.codex}/skills/evidence-weighted-purchase-ranking"
test ! -e "$dest" || { echo "Already exists: $dest" >&2; exit 1; }
git clone --depth 1 https://github.com/future3OOO/evidence-weighted-purchase-ranking.git "$repo_tmp/repo"
mkdir -p "$(dirname "$dest")"
cp -a "$repo_tmp/repo/skills/evidence-weighted-purchase-ranking" "$dest"
rm -rf "$repo_tmp"
echo "Installed to $dest"
```

## Invoke

```text
$evidence-weighted-purchase-ranking
```

The skill is model-invoked as well. Its trigger covers best-value, best-buy, and ranked marketplace comparisons when price/quantity, product rating/reviews/listing sales, or seller reputation evidence are available.

## Numerical architecture

The runtime skill computes four explicit outputs:

1. **ValueScore** — selected-variant delivered unit cost relative to the cheapest hard-fit candidate.
2. **ListingEvidenceScore** — product rating + product-review count + listing sold count.
3. **SellerConfidenceScore** — seller-wide quality + seller-feedback count + seller transactions.
4. **PurchaseScore** — deterministic non-compensatory combination of the active value/evidence axes, preceded by hard-fit and Pareto-dominance checks.

Count evidence uses a fixed diminishing-return transform rather than candidate-set P95 calibration. Missing evidence produces lower/upper score bounds instead of replacing observed ratings with an arbitrary prior.

The skill also requires:

- variant-specific quantity and delivered-price verification;
- explicit separation of listing and seller evidence populations;
- hard-fit handling for compatibility/safety requirements;
- a complete scored ranking table before any recommendation;
- value, listing-evidence, seller-confidence, and overall ranks;
- dominance and leave-one-axis-out stability checks;
- explicit identification of missing fields that could change the winner.

See [`SKILL.md`](skills/evidence-weighted-purchase-ranking/SKILL.md) for the runtime calculation and [`MARKETPLACE-FIELDS.md`](skills/evidence-weighted-purchase-ranking/references/MARKETPLACE-FIELDS.md) for marketplace-specific variant, pricing, evidence-scope, safety, and feature rules.
