# Evidence-Weighted Purchase Ranking

A reusable Codex skill for comparing marketplace listings using seller rating quality, review/feedback evidence, and seller sales history without confusing seller reputation with item value.

## Install in Codex

`$skill-installer` is a **Codex skill invocation, not a Bash command**.

From your terminal, first start Codex:

```bash
codex
```

Then, at the Codex prompt, enter:

```text
$skill-installer install https://github.com/future3OOO/evidence-weighted-purchase-ranking/tree/main/skills/evidence-weighted-purchase-ranking
```

Restart Codex after installation if the new skill is not discovered immediately.

### Direct shell installation

If you want to install without invoking `$skill-installer`, run this in Bash:

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
