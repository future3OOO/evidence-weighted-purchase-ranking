# Evidence-Weighted Purchase Ranking

A Codex skill for deterministic best-buy comparisons across ordinary retailers and marketplaces, designed for a New Zealand shopper. It separates exact-product evidence from retailer offers, handles missing marketplace-only fields without penalising direct retailers, pools deduplicated cross-site reviews only after an identity gate, calculates landed cost-to-need, and applies an explicit NZ/AU preference that overseas bargains can still overcome.

## Install in Codex

At a Codex prompt, run:

```text
$skill-installer install https://github.com/future3OOO/evidence-weighted-purchase-ranking/tree/main/skills/evidence-weighted-purchase-ranking
```

Restart Codex if the skill is not discovered immediately.

## Invoke

```text
$evidence-weighted-purchase-ranking
```

The skill also triggers for best-value, best-buy, cross-site, and ranked purchase comparisons involving ordinary NZ/AU retailers, Trade Me/eBay/AliExpress-style marketplaces, product reviews, seller evidence, screenshots, or landed pricing.

## Model 2.0

The previous additive evidence model has been replaced:

- review volume tightens a Beta posterior around the observed product rating; it does not award popularity points;
- sold and transaction counts are informational/tie-break evidence only;
- first-party retailers have no marketplace seller penalty;
- exact products can share independent review corpora across offers, while syndicated copies count once;
- unwanted surplus cannot manufacture unit value;
- unknown shipping/tax/fees create cost intervals and break-even output, with bounded uncertainty ranked conservatively rather than assigned an invented midpoint;
- regional preference is a visible offer-layer multiplier: NZ `1.00`, AU `1.10`, international `1.25`;
- `DecisionCost` is candidate-set independent, so an irrelevant listing cannot rescale existing candidates.

The script always reports raw landed price beside its evidence- and region-adjusted ranking.

## Deterministic scorer

From the skill directory:

```text
python scripts/rank.py --template
python scripts/rank.py --input comparison.json --format json
python scripts/rank.py --input comparison.json --format markdown
```

The scorer uses only the Python standard library. Its normalized JSON boundary is intentionally retailer-agnostic; the browser/agent extracts evidence, and the script validates, aggregates, scores, orders, and explains it.

## Files

- [`SKILL.md`](skills/evidence-weighted-purchase-ranking/SKILL.md): concise runtime workflow and output contract.
- [`RANKING-MODEL.md`](skills/evidence-weighted-purchase-ranking/references/RANKING-MODEL.md): formulas and interpretation.
- [`EVIDENCE-AND-IDENTITY.md`](skills/evidence-weighted-purchase-ranking/references/EVIDENCE-AND-IDENTITY.md): exact-product matching and review-corpus deduplication.
- [`RETAILER-FIELDS.md`](skills/evidence-weighted-purchase-ranking/references/RETAILER-FIELDS.md): adaptive extraction for direct retailers and marketplaces.
- [`NZ-AU-PURCHASE-POLICY.md`](skills/evidence-weighted-purchase-ranking/references/NZ-AU-PURCHASE-POLICY.md): regional sourcing and landed-cost rules.
- [`default-policy.json`](skills/evidence-weighted-purchase-ranking/scripts/default-policy.json): versioned executable defaults.

## Verify

```text
python -m unittest discover -s tests -v
```

The suite covers adverse rating volume, sparse-review shrinkage, the blind-cleat case, direct versus third-party sellers, cross-site identity, syndicated histograms, hard-fit exclusion, unknown freight, surplus packs, regional hurdles, the input template, and Markdown output.
