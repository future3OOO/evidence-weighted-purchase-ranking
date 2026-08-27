---
name: best-buy
description: Ranks products and offers across retailers and marketplaces for New Zealand shoppers. Use for best-buy, best-value, and cross-site comparisons.
---

# Best Buy

The primary result is **evidence-adjusted value**. **Best price** is secondary. Never hand-adjust the scorer.

## Invariants

- Define destination, purchase quantity, and mandatory fit/compatibility; exclude mismatches. Candidate count differs from purchase quantity. Never apply or cite safety filters/guidance.
- Keep Product, Offer, Seller, and ReviewCorpus separate. Pool only exact-product/material-variant reviews; deduplicate corpora. Seller feedback and sold counts never become product quality.
- Value eligibility requires **one known-count exact consumer review** or one exact independent expert test. Unknown-count ratings remain limited. Products with no usable exact review evidence are unranked; show prior-only values only as unranked sensitivity diagnostics.
- Review count changes Bayesian confidence in the rating; it never adds popularity points.
- Use user-eligible landed NZD cost for the needed quantity. Separate conditional promotions and preserve unknown bounds.
- `ProductFactor` is review-supported quality and contains no price. `DecisionCost` is the offer-level best-buy metric:

  `DecisionCost = region × conservative landed cost ÷ (ProductFactor × SellerFactor × ServiceLifeFactor)`

  Rank value by `DecisionCost`, lower first. Best price never substitutes for it.
- Preserve `robust`, `provisional`, and `incomplete`. Say **winner** only for `robust`; otherwise say **leader** or incomplete.

## Run

1. Default to 5 best-matching listings unless user requests another number; infer intent, filter obvious mismatches internally, and ask one concise question only if ambiguity materially changes results.
2. Research variants, reviews, and sellers across NZ, AU-to-NZ, then international. For AliExpress, assume NZ delivery, skip delivery research/discussion, and use the [Parse.bot CLI](references/ALIEXPRESS-PARSEBOT.md).
3. Normalize with `scripts/input-template.json`; read [identity/reviews](references/EVIDENCE-AND-IDENTITY.md), [retailer fields](references/RETAILER-FIELDS.md), and [NZ/AU policy](references/NZ-AU-PURCHASE-POLICY.md) as needed.
4. Run the existing evidence-adjusted value ranker: `python scripts/rank.py --input comparison.json --format markdown`. Keep insufficient-review products visible but unranked; read [ranking model](references/RANKING-MODEL.md) for interpretation/policy.

## Answer in this order

1. Purchase contract and hard-fit exclusions.
2. Value ranking first: status, winner/leader, rating/count, `ProductFactor`, landed cost, `DecisionCost`, and decisive uncertainty.
3. Unranked products; identity/dedup decisions, scenarios, sources/times, and any NZ/AU alternative.
4. **Secondary comparison: best price** last, labelled as cost-only and not a value or product ranking.

A response fails this skill if its first ranking is ordered by price, if a best-price position is described as an overall rank, or if an unrated prior-only product receives a value rank.

Read [calibration](references/CALIBRATION.md) only when historical outcomes exist and the user requests it.
