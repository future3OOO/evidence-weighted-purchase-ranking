# Deterministic Ranking Model 3.0

`scripts/default-policy.json` is the executable default. `scripts/model.py` is the arithmetic source of truth; `scripts/rank.py` applies comparison ordering and renders the result.

## Product quality

Normalize rating `R` on displayed scale `[L,U]`:

```text
y = (R - L) / (U - L)
```

For each independent, deduplicated, exact-identity corpus, use `n` supporting reviews and `t = n*y`. With default `Beta(7.5, 2.5)` prior:

```text
a = 7.5 + sum(t)
b = 2.5 + sum(n - t)
qMean = a / (a + b)
qLow = BetaInverseCDF(0.10, a, b)
qHigh = BetaInverseCDF(0.90, a, b)
ProductFactor = min(pooled observed y, qLow)
```

With no reviews, `ProductFactor = prior qLow` for uncertainty and sensitivity only. This prior never counts as product evidence or value eligibility. A displayed rating with count unavailable uses provisional `n=1`, sets `count_uncertain`, and cannot satisfy a known-count review threshold. The cap prevents a sparse below-prior rating being improved above its own observed mean. Review volume therefore changes confidence/direction toward the observed rating; it never appears as separate quality points.

Sanity values: 5.0/6 is about `0.723`, 4.7/15 about `0.761`, 3.0/10,000 about `0.494`, and no reviews about `0.569`. Exact values come from the bundled Beta quantile implementation.

## Evidence eligibility

The executable defaults are:

```text
minimum_exact_reviews_for_value = 5
minimum_exact_reviews_for_limited = 1
allow_expert_test_as_evidence = true
```

Known-count, exact-identity consumer-review corpora count once after deduplication. A consumer rating whose count is unavailable remains limited and does not satisfy the review threshold. An exact independent `expert_test` source can establish value eligibility when policy allows it; the source itself represents one test and therefore omits consumer-style count and histogram fields. Probable or ambiguous identity, dependent expert tests, duplicated copies, and seller/listing sales do not satisfy the threshold.

Each product receives one status:

- `evidence_backed`: meets the configured exact-review threshold or expert-test rule;
- `limited_evidence`: has usable exact evidence below the threshold;
- `unrated`: has no usable exact product evidence;
- `ambiguous_evidence`: evidence exists but cannot be assigned to the selected product or variant.

The Bayesian prior and diagnostic DecisionCost remain visible for unverified contenders. They do not convert those contenders into evidence-backed value candidates.

## Seller factor and popularity

First-party retailer: `SellerFactor = 1` (`not_applicable`). Third-party seller uses the same posterior method with default `Beta(9,1)` and seller feedback count. Missing third-party seller evidence uses the prior interval, not zero or one.

Listing sold count and seller transactions do not enter ProductFactor or SellerFactor. They may break an otherwise exact tie after cost, quality, region, and review/feedback support.

## Quantity and cost

The normalized offer prices the actual order:

```text
received = pack_quantity * packs_purchased
useful = needed_quantity
surplus = received - useful
```

Require `received >= needed_quantity`. Unwanted surplus never divides down cost. `CostToNeed` is the selected order's landed total, not a candidate-set-relative value score.

Unknown positive charges produce `[costLow,costHigh]`; an absent upper bound yields unbounded `costHigh`. Unknown discounts contribute zero to the base case. The scorer reports the combined unknown-charge break-even. It does not invent a midpoint for a charge when the evidence supplies only bounds.

## Separate purchase rankings

### Best price

Best price includes every qualifying offer and orders resolved landed cost only. ProductFactor, SellerFactor, evidence status, sold counts, and regional preference do not change this order. If an unknown charge could change the cheapest offer, the result is `incomplete` and reports a price leader rather than a winner. A robust price winner may still be `unrated`.

### Evidence-backed best value

Only offers whose product is `evidence_backed` are admitted. With `ServiceLifeFactor = 1` unless credible comparable quantitative life evidence is supplied:

```text
DecisionCost = region_multiplier * costHigh
               / (ProductFactor * SellerFactor * ServiceLifeFactor)
```

Lower wins. For an exact landed cost, `costLow = costHigh`, so this is the ordinary landed CostToNeed formula. For a bounded unknown charge, the headline DecisionCost deliberately uses the conservative upper bound; `decision_cost_worst` repeats that value explicitly and `decision_cost_best` supplies the optimistic bound. An unbounded offer has no finite headline DecisionCost. This is candidate-set independent: adding an irrelevant candidate cannot rescale existing offers. Hard-fit failures are excluded first.

For uncertainty:

```text
DecisionCostBest  = region * costLow  / (qualityHigh * sellerHigh * lifeHigh)
DecisionCostWorst = region * costHigh / (qualityLow  * sellerLow  * lifeLow)
```

An unbounded cost sorts after every finite DecisionCost and cannot produce a robust value winner. If all eligible offers are unbounded, their optimistic bound, landed-cost lower bound, evidence factors, region, support counts, and stable offer ID provide a deterministic display order, but the result remains `incomplete` and break-even remains unknown.

A robust value winner requires all of the following:

- `evidence_backed` product status;
- resolved landed cost;
- exact product/material identity;
- its conservative DecisionCost is below every rival's optimistic DecisionCost.

Overlapping intervals, an exact tie, or non-exact product identity produce a `provisional` **leader**, never a winner. Missing eligible products or decisive cost/provenance facts produce `incomplete`.

A bounded but unresolved cost on the leading offer also remains `provisional`, even when its conservative interval is separated from every rival.

Tie order is: lower conservative DecisionCost, lower optimistic DecisionCost, lower landed-cost upper bound, lower landed-cost lower bound, higher ProductFactor, NZ before AU before international, more independent product reviews, more seller feedback, sold/transactions, then stable offer ID. Missing upper bounds sort after finite values. Use full precision for ordering.

`best_price` is the primary price result. The legacy `raw_landed_*` keys mirror it for compatibility. `evidence_backed_value.winner` is non-null only for `robust`; `leader` names the computed ordering head for provisional or cost-incomplete eligible comparisons. When no product is eligible, both are null and the status is `incomplete`.

## Interpretation

Always show best price beside evidence-backed DecisionCost and label unverified contenders. ProductFactor is conservative evidence-adjusted satisfaction, not a defect probability or eligibility status. Regional multiplier is explicit operator preference, not a fee. Qualitative review defects remain narrative or hard-fit facts unless a complete deterministic coding population exists.
