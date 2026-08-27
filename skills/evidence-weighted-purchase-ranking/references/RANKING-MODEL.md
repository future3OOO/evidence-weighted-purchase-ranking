# Deterministic Ranking Model 2.0

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

With no reviews, `ProductFactor = prior qLow`. A displayed rating with count unavailable uses provisional `n=1` and sets `count_uncertain`. The cap prevents a sparse below-prior rating being improved above its own observed mean. Review volume therefore changes confidence/direction toward the observed rating; it never appears as separate quality points.

Sanity values: 5.0/6 is about `0.723`, 4.7/15 about `0.761`, 3.0/10,000 about `0.494`, and no reviews about `0.569`. Exact values come from the bundled Beta quantile implementation.

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

## Overall offer rank

With `ServiceLifeFactor = 1` unless credible comparable quantitative life evidence is supplied:

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

An unbounded cost cannot be a robust winner. A result is robust only when winner-changing uncertainty is absent and the conservative order remains separated; otherwise report provisional/incomplete plus breakpoints. An exact tie is provisional because the stable ID tie-break selects an order without evidence that one offer is better.

Tie order is: lower DecisionCost, lower exact landed cost, higher ProductFactor, NZ before AU before international, more independent product reviews, more seller feedback, sold/transactions, then stable offer ID. Use full precision for ordering.

`raw_landed_winner` is set only when the cheapest order is resolved. When an unknown charge could overturn it, `raw_landed_winner` is null, `raw_landed_leader` is the cheapest conservative known order, and `raw_landed_contenders` names the unresolved alternatives.

## Interpretation

Always show raw landed cost beside DecisionCost. ProductFactor is conservative evidence-adjusted satisfaction, not a defect probability. Regional multiplier is explicit operator preference, not a fee. Qualitative review defects remain narrative or hard-fit facts unless a complete deterministic coding population exists.
