---
name: evidence-weighted-purchase-ranking
description: Ranks comparable products and purchase offers across online retailers and marketplaces using landed cost, exact-product review evidence, applicable seller evidence, and NZ-first regional preference. Use when a New Zealand shopper asks for the best value or best buy, requests a cross-site comparison, or supplies listings or screenshots to rank.
---

# Evidence-Weighted Purchase Ranking

Produce a computed retail purchase ranking. Research first, normalize evidence, run the bundled scorer, and then name one winner or one provisional winner with the exact fact that can overturn it.

## Non-negotiable rules

- Separate **Product**, **Offer**, **Seller**, and **ReviewCorpus**. Product evidence follows an exact product; price, stock, delivery, seller, returns, and warranty remain offer-specific.
- Treat `observed`, `missing`, `unavailable`, `not_applicable`, and `ambiguous` as different field states. Missing sold or seller fields are never zero and never penalize a direct retailer.
- Review count controls confidence in the displayed rating. Sold counts and seller transactions describe adoption/maturity only; they never add quality points.
- Pool cross-site reviews only for exact product and material-variant identity. Count syndicated or duplicated corpora once. Cite probable matches but do not score them.
- Count only the quantity the user needs or explicitly values. Unwanted pack surplus has zero purchase value.
- Exclude any hard-fit, safety, compatibility, authenticity, condition, or legal failure before scoring.
- Use normal, user-eligible checkout pricing. Keep welcome, membership, coupon, minimum-spend, and other conditional promotions in named scenarios.
- Never replace the scorer with an unshown opinion or hand-adjust its result.

## Workflow

1. Define the purchase contract: New Zealand destination/postcode, required quantity, useful spares, mandatory fit/safety facts, relevant service-life measure, and any explicit user preference. If quantity is unknown, run plausible scenarios and ask only if the winner changes.
2. Search in this order: qualifying NZ offers, AU offers that actually deliver to NZ, then international offers. Include a credible NZ/AU alternative whenever one exists; an overseas offer may still win.
3. Exhaust evidence already accessible in product pages, selected variants, review summaries/histograms/comments, structured data, seller pages, screenshots, carts, and checkout estimates. Do not ask the user to transcribe visible evidence.
4. Build canonical products and their offers. Follow [EVIDENCE-AND-IDENTITY.md](references/EVIDENCE-AND-IDENTITY.md). For direct-retailer versus marketplace fields and review labels, follow [RETAILER-FIELDS.md](references/RETAILER-FIELDS.md).
5. Capture the selected order's landed cost in NZD: item total + shipping + tax/GST/duty + mandatory fees - eligible discount. Supply explicit FX rate, source, and timestamp for non-NZD prices. Use bounded unknown components when exact checkout cost is unavailable.
6. From this skill directory, generate the schema and run the deterministic scorer:

```text
python scripts/rank.py --template
python scripts/rank.py --input comparison.json --format markdown
```

Use `--format json` for machine-readable intermediates and `--policy custom-policy.json` only when the user explicitly changes the defaults. The executable schema is authoritative; see [RANKING-MODEL.md](references/RANKING-MODEL.md) for interpretation and [NZ-AU-PURCHASE-POLICY.md](references/NZ-AU-PURCHASE-POLICY.md) for regional policy.

7. If a decisive cost or identity fact is missing, research it before asking. When it remains unavailable, preserve the script's interval/status and report its break-even rather than guessing.

## Required answer

Show, compactly:

1. excluded offers and hard-fit reasons;
2. product identity and every included, deduplicated, or excluded review source;
3. selected offer/variant, retailer or seller type, region, fulfilment origin, landed NZD cost, useful quantity, and conditional-price scenarios;
4. product-quality rank, raw landed-cost rank, and final DecisionCost rank with intermediate factors;
5. one computed winner, its `robust`, `provisional`, or `incomplete` status, and why;
6. the best qualifying NZ/AU alternative when an overseas offer wins, including its local premium;
7. unknown fields and the exact winner-changing breakpoint;
8. source URLs and observation times.

Use the script's full-precision order; display money to two decimals and factors to three decimals. Explain qualitative review findings separately—never turn selected comments into invented sentiment points.

Read [CALIBRATION.md](references/CALIBRATION.md) only when historical purchase outcomes are available and the user asks to calibrate the versioned defaults.
