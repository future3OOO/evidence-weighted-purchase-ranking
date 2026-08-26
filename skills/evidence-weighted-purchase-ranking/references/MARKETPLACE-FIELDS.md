# Marketplace Fields

Read this only when a marketplace exposes ambiguous variants, conditional prices, mixed evidence scopes, or materially different soft product attributes.

## Price ownership

The price used by the ranking belongs to the **selected variant**. Search-card teaser prices, crossed-out reference prices, and the cheapest unrelated variant do not belong to it.

Base delivered cost may include only amounts that apply to the user's actual purchase:

- selected-variant item price;
- shipping for that variant and destination;
- tax/VAT/GST actually charged or known to be included;
- mandatory fees;
- discounts whose conditions are satisfied by this purchase.

Keep a promotion out of the base case when it depends on an unmet condition, including:

- new-customer or welcome pricing;
- first-order pricing;
- app-only or membership-only pricing the user has not established;
- coins/points that require an unknown balance;
- minimum basket spend not met by the candidate purchase;
- multi-buy quantity not selected;
- coupon codes whose eligibility cannot be verified.

If the user is eligible for a conditional promotion, calculate it as a named scenario. Never silently compare one candidate's welcome price with another candidate's normal price.

## Quantity and usable units

`usable_quantity` is the number of functional units the user actually receives in the selected variant.

Do not count screws, adhesive pads, storage cases, free samples, or other accessories as product units. When variants are measured by length, weight, area, capacity, or another functional unit rather than piece count, use that common unit consistently across every candidate.

If one pack contains unusable or unwanted variants, use the quantity that satisfies the user's requirement rather than the headline pack count.

## Evidence populations

Keep these populations distinct:

| Field | Population |
| --- | --- |
| Product rating | product/listing buyers reviewing the product |
| Product-review count | reviews supporting the product rating |
| Listing sold count | orders/units attributed to that listing |
| Seller rating | seller-wide reputation metric |
| Seller positive-feedback % | seller-wide positive feedback proportion |
| Seller-feedback count | feedback observations supporting seller reputation |
| Seller transactions | seller-wide completed sales/orders/transactions |

A marketplace label such as `sold`, `orders`, `reviews`, `feedback`, or `transactions` is not enough by itself. Resolve whether it belongs to the selected variant, the whole listing, or the seller.

Do not combine two seller-quality metrics that substantially measure the same reputation population. Prefer the platform's primary seller-wide quality metric whose supporting count and definition are clearest.

## Variant evidence

Listing-level product evidence can support the selected variant when the listing's variants are materially equivalent, for example:

- pack quantity;
- colour;
- cosmetic finish;
- non-functional size choice where the underlying product is otherwise the same.

Do not attribute aggregate listing evidence to a selected variant when the variant menu mixes materially different products, constructions, functions, generations, or safety configurations.

When product evidence is heterogeneous and cannot be separated, mark the affected product fields `missing` for that variant. Seller-wide evidence remains usable if its scope is clear.

## Safety and compliance

A safety, legal, electrical, compatibility, load-bearing, child-safety, or other mandatory requirement is a hard-fit gate when it is relevant to the requested use. Price cannot compensate for failure.

Use only claims that are actually evidenced by the listing, manufacturer, standard, certification, or authoritative source. Do not turn vague marketing words such as `safe`, `premium`, or `heavy duty` into quantified feature advantages.

For hardware, confirm the selected variant includes any mounting method or supplied hardware required for the intended safe installation.

## Material soft differences

Most commodity comparisons should not invent another score. If retained candidates are genuinely equivalent after hard-fit filtering, do not create `FeatureScore`.

Create `FeatureScore` only when a material **non-mandatory** difference remains and can be represented from observable evidence, such as warranty length, measured capacity, material thickness, expected service life, included useful accessories, or another user-relevant feature.

For each active feature `j`, map candidate `i` to `[0,1]`:

```text
higher-is-better numeric:  f_ij = x_ij / max(x_j)
lower-is-better numeric:   f_ij = min(x_j) / x_ij
binary desirable feature:  f_ij = 1 if present else 0
```

Use user-specified feature weights when provided. Otherwise use equal weights across the explicitly active features:

```text
FeatureScore_i = 100 * weighted_mean(f_ij)
```

Do not score an attribute merely because a marketplace card happens to expose it. Every active feature must have a stated connection to the purchase objective.

If durability has a credible quantitative service-life measure, prefer converting value to **cost per expected service unit** rather than awarding arbitrary durability points:

```text
effective_unit_cost = delivered_cost / (usable_quantity * relative_service_life)
```

Use this only when service-life evidence is comparable across candidates. Otherwise keep durability as a feature or hard-fit fact and state the evidence limitation.

## Evidence extraction order

Before asking the user for missing information, exhaust in this order when accessible:

1. selected variant state on the listing page;
2. search/listing card;
3. product specification and description;
4. review summary;
5. seller/store profile;
6. structured metadata embedded in the page;
7. attached screenshots or files already supplied by the user.

Do not ask the user to transcribe evidence the agent can already read. If a field remains unavailable, use the lower/upper-bound treatment in `SKILL.md` and ask only when that uncertainty can change the winner.
