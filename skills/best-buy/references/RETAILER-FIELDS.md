# Retailer and Marketplace Evidence

Use this reference while extracting normalized input. Do not create site-specific scoring rules or scrapers.

## Field states

- `observed`: a scoped value is visible and reproducible.
- `missing`: not yet checked; research it before ranking when material.
- `unavailable`: checked, but the source does not disclose it.
- `not_applicable`: the population or charge does not exist for this offer.
- `ambiguous`: visible but its product, variant, seller, time, or pricing scope cannot be resolved.

`not_applicable` contributes zero to landed cost. Never convert `missing`, `unavailable`, or `ambiguous` to observed zero.

## Adaptive evidence matrix

| Source type | Common product evidence | Common offer/seller evidence | Required treatment |
| --- | --- | --- | --- |
| NZ/AU direct retailer (for example Bunnings, Mitre 10, Kmart) | stars, review count, sometimes histogram/comments | price, store/postcode stock, delivery, retailer returns/warranty; usually no sold count | seller factor is `not_applicable`; missing sold is neutral |
| Hybrid retailer/marketplace | product reviews plus first- or third-party offer | merchant identity, seller feedback when third-party | classify each selected offer as first- or third-party |
| AliExpress/eBay-style marketplace | listing/catalog rating, reviews, sometimes sold/orders | seller feedback/count/transactions, variant price and delivery | resolve listing versus selected-variant scope; keep sold separate from quality |
| Trade Me-style marketplace | product reviews often absent | in-trade/private status, selling feedback, total trades | prefer selling feedback; total trades are not current-listing sales |

`reviews / sold` is review participation, not positive-feedback percentage. Never derive satisfaction from it.

## Review extraction

Prefer, in order:

1. complete 1–5 star histogram;
2. average plus supporting review count;
3. average with count unavailable (the scorer uses provisional `n=1` and marks uncertainty);
4. complete individual-review population;
5. partial/sorted comments for qualitative defect, fit, or durability findings only;
6. no native reviews, followed by an exact-product cross-site search.

Record whether reviews are verified-purchase, staff, incentivized/promotional, native, manufacturer-syndicated, or unknown. Record the review provider and corpus ID when visible. Do not assume every solicited or moderated review is verified.

Record `evidence_type: consumer_reviews` for ordinary purchaser ratings. Use `expert_test` plus `independent: true` only for an independent specialist test with a reproducible score. A displayed rating without a known count can inform sensitivity but cannot satisfy the exact-review threshold.

## Selected variant and quantity

Score the purchasable selected variant, not the title, hero image, teaser price, or default search card. Resolve:

- functional product/model/material/voltage/condition;
- pack quantity and number of packs in the priced order;
- which reviews and sold count apply to that exact variant;
- stock and delivery for the user's NZ store/postcode.

The checkout item amount must cover enough packs to meet `needed_quantity`. Accessories, screws, samples, cases, and unwanted units do not increase useful quantity.

## Price states and promotions

Base-case cost includes the selected order's item total, destination shipping, GST/tax/duty, mandatory fees, and only discounts the user is known to qualify for. For foreign currency, record `fx_to_nzd`, rate source, and timestamp.

Treat welcome, first-order, app, member, points/coins, minimum-spend, multi-buy, and coupon prices as separate scenarios unless eligibility is established. An unknown shipping/tax/fee component uses `missing`, `unavailable`, or `ambiguous` plus an evidence-based `upper_amount` when one exists; otherwise the scorer reports an unbounded cost and break-even.

## Extraction order

Before asking the user, inspect the selected variant, product/specification page, review summary and filters, seller/store profile, structured product data, cart/checkout estimate, attached screenshots/files, and exact-product sources elsewhere. Ask only when unresolved evidence can change the winner.
