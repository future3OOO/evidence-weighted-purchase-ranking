---
name: best-buy
description: Ranks products and offers across retailers and marketplaces for New Zealand shoppers. Use for best-buy, best-value, and cross-site comparisons.
---

# Best Buy

The primary result is **evidence-adjusted value**. **Best price** is secondary. Never hand-adjust the scorer.

## Invariants

- Define destination, quantity, and mandatory fit/safety/compatibility; exclude failures first.
- Keep Product, Offer, Seller, and ReviewCorpus separate. Pool only exact-product/material-variant reviews and deduplicate corpora. Seller feedback and sold counts never become product quality.
- Value eligibility requires at least **one known-count exact consumer review** or one exact independent expert test. Ratings with unknown counts remain limited. Products with no usable exact review evidence are unranked; prior-only values may be shown only as sensitivity diagnostics without an ordinal or runner-up label.
- Review count changes Bayesian confidence in the rating; it never adds popularity points.
- Use user-eligible landed NZD cost for the needed quantity. Separate conditional promotions and preserve unknown bounds.
- `ProductFactor` is review-supported quality and contains no price. `DecisionCost` is the offer-level best-buy metric:

  `DecisionCost = region × conservative landed cost ÷ (ProductFactor × SellerFactor × ServiceLifeFactor)`

  Rank value by `DecisionCost`, lower first. Best price never substitutes for it.
- Preserve `robust`, `provisional`, and `incomplete`. Say **winner** only for `robust`; otherwise say **leader** or incomplete.

## Run

1. Research product, variant, reviews, seller, cart, and checkout before asking. Search NZ, then AU delivery to NZ, then international.
2. Normalize with `scripts/input-template.json`. As needed, read [identity/reviews](references/EVIDENCE-AND-IDENTITY.md), [retailer fields](references/RETAILER-FIELDS.md), and [NZ/AU policy](references/NZ-AU-PURCHASE-POLICY.md).
3. Run `python scripts/rank.py --input comparison.json --format markdown` (`--template` creates input; JSON gives machine output). The schema is authoritative; use the [ranking model](references/RANKING-MODEL.md) only for interpretation or policy.

## Answer in this order

1. Purchase contract and hard-fit exclusions.
2. Value ranking first: status, winner/leader, rating/count, `ProductFactor`, landed cost, `DecisionCost`, and decisive uncertainty for every eligible product.
3. Unrated/ambiguous products unranked; identity/dedup decisions, scenarios, sources/times, and any NZ/AU alternative.
4. **Secondary comparison: best price** last, labelled as cost-only and not a value or product ranking.

A response fails this skill if its first ranking is ordered by price, if a best-price position is described as an overall rank, or if an unrated prior-only product receives a value rank.

Read [calibration](references/CALIBRATION.md) only when historical outcomes exist and the user requests it.
