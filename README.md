# Best Buy

A Codex skill for deterministic best-buy comparisons across ordinary retailers and marketplaces, designed for a New Zealand shopper. It separates exact-product evidence from retailer offers, handles missing marketplace-only fields without penalising direct retailers, pools deduplicated cross-site reviews only after an identity gate, calculates landed cost-to-need, and applies an explicit NZ/AU preference that overseas bargains can still overcome.

## Install in Codex

At a Codex prompt, run:

```text
$skill-installer install https://github.com/future3OOO/evidence-weighted-purchase-ranking/tree/main/skills/best-buy
```

Restart Codex if the skill is not discovered immediately.

## Invoke

```text
$best-buy
```

The skill also triggers for best-value, best-buy, cross-site, and ranked purchase comparisons involving ordinary NZ/AU retailers, Trade Me/eBay/AliExpress-style marketplaces, product reviews, seller evidence, screenshots, or landed pricing.

## Model 3.0

The scorer now separates two questions that must not be conflated:

- **Best price** includes every qualifying offer and ranks resolved landed cost only. An unrated product can win price, but is labelled unverified.
- **Evidence-backed best value** admits only products with sufficient exact evidence. The default threshold is five known-count exact consumer reviews or one exact independent expert test.

Every product is labelled `evidence_backed`, `limited_evidence`, `unrated`, or `ambiguous_evidence`. A Bayesian prior still expresses uncertainty, but prior-only products cannot win or lead the value ranking. A value result is called a winner only when it is robust; overlapping intervals produce a provisional leader.

Model 3.0 deliberately changes the output contract: top-level `winner` is now non-null only for a robust evidence-backed value result, and top-level `ranking` contains only evidence-eligible offers. Use `leader` for provisional or cost-incomplete value results, `best_price`/`price_ranking` for the cost-only result, and `unverified_value_contenders` for excluded value candidates. Legacy `raw_landed_*` keys remain as price aliases.

Other model rules remain:

- review volume tightens a Beta posterior around the observed product rating; it does not award popularity points;
- sold and transaction counts are informational/tie-break evidence only;
- first-party retailers have no marketplace seller penalty;
- exact products can share independent review corpora across offers, while syndicated copies count once;
- unwanted surplus cannot manufacture unit value;
- unknown shipping/tax/fees create cost intervals and break-even output, with bounded uncertainty ranked conservatively rather than assigned an invented midpoint;
- regional preference is a visible offer-layer multiplier: NZ `1.00`, AU `1.10`, international `1.25`;
- `DecisionCost` is candidate-set independent, so an irrelevant listing cannot rescale existing candidates.

The script always reports the best-price table beside its evidence- and region-adjusted value table, including unverified contenders.

## Deterministic scorer

From the skill directory:

```text
python scripts/rank.py --template
python scripts/rank.py --input comparison.json --format json
python scripts/rank.py --input comparison.json --format markdown
```

The scorer uses only the Python standard library. Its normalized JSON boundary is intentionally retailer-agnostic; the browser/agent extracts evidence, and the script validates, aggregates, scores, orders, and explains it.

## Files

- [`SKILL.md`](skills/best-buy/SKILL.md): concise runtime workflow and output contract.
- [`RANKING-MODEL.md`](skills/best-buy/references/RANKING-MODEL.md): formulas and interpretation.
- [`EVIDENCE-AND-IDENTITY.md`](skills/best-buy/references/EVIDENCE-AND-IDENTITY.md): exact-product matching and review-corpus deduplication.
- [`RETAILER-FIELDS.md`](skills/best-buy/references/RETAILER-FIELDS.md): adaptive extraction for direct retailers and marketplaces.
- [`NZ-AU-PURCHASE-POLICY.md`](skills/best-buy/references/NZ-AU-PURCHASE-POLICY.md): regional sourcing and landed-cost rules.
- [`default-policy.json`](skills/best-buy/scripts/default-policy.json): versioned executable defaults.

## Verify

```text
python -m unittest discover -s tests -v
```

The suite covers evidence eligibility thresholds, unrated price winners, independent expert tests, ambiguous and duplicated evidence, provisional leaders, adverse rating volume, sparse-review shrinkage, the blind-cleat case, direct versus third-party sellers, cross-site identity, hard-fit exclusion, unknown freight, surplus packs, regional hurdles, legacy inputs, and Markdown output.
