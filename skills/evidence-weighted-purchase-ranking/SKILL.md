---
name: evidence-weighted-purchase-ranking
description: Deterministic evidence-weighted ranking for comparable marketplace listings. Use when the user asks for the best value, best buy, or ranked choice among products and price/quantity, product rating/reviews/listing sales, or seller rating/feedback/transactions are available.
---

# Evidence-Weighted Purchase Ranking

Produce a **computed purchase ranking**, not a qualitative recommendation. Keep three populations separate:

- **listing evidence**: product rating, product-review count, listing sold count;
- **seller evidence**: seller rating or positive-feedback percentage, seller-feedback count, seller-wide transactions;
- **purchase value**: the selected variant's delivered cost divided by usable quantity.

Never recommend a winner before the input table and scores are calculated.

## 1. Exhaust the available evidence

For every candidate, extract all fields already visible in the page, listing, search card, structured data, screenshot, or accessible seller page before asking the user for anything.

Record:

```text
candidate_id
url
selected_variant
usable_quantity
hard_fit
item_price
shipping
tax
mandatory_fees
eligible_discount
product_rating + rating_scale
product_review_count
listing_sold_count
seller_rating + rating_scale OR seller_positive_feedback_pct
seller_feedback_count
seller_transaction_count
scope/time-horizon for every rating or count
```

A field is either a numeric value with its scope or `missing`. Never infer seller-wide transactions from listing sales, product reviews from seller feedback, or variant-specific evidence from a listing-wide number.

Do not ask the user for a field that is already visible or accessible. Ask only when a missing field can still change the winner after the uncertainty check in step 6.

**Complete when:** every candidate has a reproducible input record and every rating/count is labelled product/listing/seller and variant/listing/seller scope.

## 2. Resolve variant and hard-fit integrity

Score the **selected purchasable variant**, not the title, hero image, cheapest teaser variant, or default search-card quantity.

Exclude a candidate (`hard_fit = 0`) if it fails a mandatory requirement such as model/specification, compatibility, authenticity, condition, required mounting method, safety requirement, or other user constraint.

Listing-wide reviews or sold counts may support a selected variant only when the variants are materially the same product and differ only in quantity, colour, size, or another non-material choice. If one listing mixes materially different products, do not attribute its aggregate product evidence to a specific variant.

For safety-related products, treat relevant mounting/configuration requirements and supplied safety hardware as hard-fit facts, not soft price trade-offs.

For marketplace pricing/variant edge cases, use [references/MARKETPLACE-FIELDS.md](references/MARKETPLACE-FIELDS.md).

**Complete when:** every retained candidate is a valid purchase for the user's requirement and every retained evidence field is scope-compatible with its selected variant.

## 3. Calculate delivered value

For each retained candidate:

```text
delivered_cost =
    item_price
  + shipping
  + tax
  + mandatory_fees
  - eligible_discount

unit_cost = delivered_cost / usable_quantity
```

Only subtract a discount that the user can actually receive for this purchase. Do not put welcome-only, new-account, minimum-spend, bundle, coin, membership, or conditional coupon pricing into the base case unless its condition is satisfied. Calculate conditional promotions as separate scenarios.

Let `Umin` be the lowest `unit_cost` among hard-fit candidates:

```text
ValueScore = 100 * Umin / unit_cost
```

The cheapest delivered unit therefore scores `100`; every other candidate is a transparent ratio to it.

**Complete when:** every retained candidate has delivered cost, usable quantity, unit cost, ValueScore, and a separately labelled conditional-price scenario if relevant.

## 4. Calculate listing and seller evidence

Use the same evidence model for the two different populations. Do not mix their inputs.

Normalize a quality metric to `[0,1]`:

```text
quality(x, L, U) = clamp((x - L) / (U - L), 0, 1)
```

Examples:

```text
1-5 stars:              quality = (rating - 1) / 4
0-5 stars:              quality = rating / 5
positive-feedback pct:  quality = percentage / 100
```

Convert a non-negative evidence count to `[0,1)` with fixed diminishing returns:

```text
support(c) = ln(1 + c) / (1 + ln(1 + c))
```

Then calculate the generic evidence score:

```text
EvidenceScore(Q, N, S) =
    100 * (
        0.45 * Q
      + 0.30 * support(N)
      + 0.25 * support(S)
    )
```

The weights mean: rating/feedback quality is the largest single signal, while observed review/transaction volume collectively carries slightly more weight (`55%`) than the displayed quality metric (`45%`). They are deterministic defaults, not claimed universal causal coefficients.

Apply it separately:

```text
ListingEvidenceScore = EvidenceScore(
    normalized_product_rating,
    product_review_count,
    listing_sold_count
)

SellerConfidenceScore = EvidenceScore(
    normalized_seller_quality,
    seller_feedback_count,
    seller_transaction_count
)
```

For seller quality, use the platform's seller-wide rating aligned with its seller-feedback population. If the platform exposes only positive-feedback percentage, use that. Do not average overlapping seller reputation metrics merely because both are visible.

### Missing fields

Do not replace an observed rating with a prior. Preserve it.

For the conservative ranking score, a missing term contributes `0` only to its own weighted contribution. Also compute an upper bound by setting each missing normalized term to `1`:

```text
ScoreLower = score with missing terms = 0
ScoreUpper = score with missing terms = 1
```

Thus a visible 5.0 rating remains different from a visible 3.5 rating even when review count is unavailable, while missing supporting evidence cannot create an advantage.

Round displayed scores to **one decimal place**. Keep full precision for ranking.

**Complete when:** every retained candidate has ListingEvidenceScore and SellerConfidenceScore lower/upper bounds from correctly scoped inputs, or the entire axis is explicitly unavailable for all candidates.

## 5. Calculate the overall purchase ranking

Use these normalized active axes for each candidate:

```text
V = ValueScore / 100
L = ListingEvidenceScoreLower / 100
S = SellerConfidenceScoreLower / 100
```

If an evidence axis is unavailable for **every** candidate, omit that axis for everyone. Never omit an axis only for the candidate that happens to lack data.

If materially different but non-mandatory product attributes remain after hard-fit filtering, add a `FeatureScore` axis using the deterministic rules in [references/MARKETPLACE-FIELDS.md](references/MARKETPLACE-FIELDS.md). Do not invent a feature axis for genuinely equivalent commodity items.

### Dominance

Candidate A **dominates** candidate B when A is at least as good on every active axis and strictly better on at least one:

```text
A_j >= B_j for every active axis j
and
A_j > B_j for at least one j
```

A dominated candidate cannot rank above the candidate that dominates it.

### Overall score

For the active normalized axes `a1...am`:

```text
Floor   = min(a1 ... am)
Balance = (a1 * ... * am) ^ (1 / m)

PurchaseScore = 100 * sqrt(Floor * Balance)
```

This is deliberately non-compensatory: a terrible value, weak listing evidence, or weak seller cannot be completely hidden by strength elsewhere. It also avoids an arbitrary additive price-vs-reputation exchange rate.

Rank descending by:

```text
1. hard_fit = 1
2. PurchaseScore
3. Floor
4. Balance
5. lower unit_cost
6. higher ListingEvidenceScore
7. higher SellerConfidenceScore
```

**Complete when:** every hard-fit candidate has a reproducible overall PurchaseScore and rank, and no dominated candidate outranks its dominator.

## 6. Prove the recommendation is stable enough to state

Before naming the winner:

1. Recalculate the overall ranking once with each active soft axis removed in turn.
2. For every candidate with missing fields, recalculate its best-case overall score using the corresponding evidence-score upper bounds.
3. Check whether any missing-field best case can overtake the current winner.

Classify the result:

```text
DOMINANT     winner Pareto-dominates every other eligible candidate
ROBUST       same winner under every leave-one-axis-out recalculation and no missing-data upper bound can overtake it
SENSITIVE    winner changes when an active axis is removed
INCOMPLETE   a missing-data upper bound can overtake the current winner
```

If `INCOMPLETE`, obtain the specific missing field(s) capable of changing the winner when accessible. Ask the user only if those decisive fields cannot be obtained from available evidence.

**Complete when:** the winner has one of the four stability labels and every potentially winner-changing missing field has been identified.

## 7. Required output contract

Always show the calculation before the recommendation. At minimum include this table; split it into two tables only if width makes one table unreadable:

```text
Rank
Candidate / selected variant
Hard fit
Usable quantity
Delivered cost
Unit cost
Product rating
Product reviews
Listing sold
ListingEvidenceScore [lower-upper]
Seller rating / feedback %
Seller feedback count
Seller transactions
SellerConfidenceScore [lower-upper]
ValueScore
FeatureScore (only if active)
PurchaseScore
```

Then state, in this order:

1. **Overall purchase ranking** with one winner.
2. **Value ranking** by unit cost / ValueScore.
3. **Listing-evidence ranking**.
4. **Seller-confidence ranking**.
5. **Stability:** `DOMINANT`, `ROBUST`, `SENSITIVE`, or `INCOMPLETE`.
6. **Why the overall winner differs from any component winner**, using the actual score differences rather than qualitative phrases.

Do not substitute prose such as "seller confidence may outweigh a small price difference" for the calculation. Do not recommend before the ranked table exists.

**Complete when:** the output contains the scored table, all four requested rankings that have active data, one overall winner, and the stability result.
