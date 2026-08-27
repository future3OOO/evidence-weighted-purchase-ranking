# Product Identity and Review Evidence

## Keep four populations separate

- **Product**: canonical identity, material variant, specifications, hard-fit facts, and pooled product reviews.
- **Offer**: selected order, retailer, merchant, price, stock, delivery, returns, warranty, promotion, and fulfilment origin.
- **Seller**: third-party merchant reputation for one offer/platform. Never transfer it across offers.
- **ReviewCorpus**: one underlying review population, even if syndicated to several sites.

If the exact same product is cheaper elsewhere, attach the cheaper offer to the same product; do not create a second product competitor.

## Identity gate

Use the strongest available evidence:

1. `exact`: same manufacturer GTIN/EAN/UPC/ISBN for the same material variant and condition; or same brand + manufacturer MPN/model + no conflicting material specification.
2. `probable`: brand/model wording plus several distinctive specifications, but no decisive identifier. Cite it; do not pool automatically.
3. `ambiguous`: store SKU, title/image similarity, generic compatibility, or appearance alone. Never pool.

Material identity includes generation/model suffix, size/capacity, voltage/plug/region, formulation/material, condition/refurbishment, and experience-changing bundle contents. A retailer-created multipack may share product reviews only when the contained unit is exact; its offer price and quantity remain separate.

Generic/unbranded lookalikes are not exact merely because photos match. A store SKU is not a GTIN.

## Corpus gate and deduplication

Every review source needs a stable `corpus_id` scoped to one exact product/material variant. Assign the same corpus ID only when exact product identity is already established and the sources also show matching review IDs, `Originally posted on` attribution, or matching author/date/text populations. Provider/feed identity alone is insufficient. The scorer keeps the most complete observation of that corpus and reports discarded copies.

When aggregate overlap cannot be resolved, group the uncertain sources into one conservative corpus and use the most complete aggregate; do not sum them. Pool counts and normalized rating successes only across independent exact-identity corpora.

Listing-family reviews may support a selected variant only when all reviewed variants are materially equivalent. Otherwise mark the review source `probable`/`ambiguous` or split the corpus if variant-level evidence is available.

## Adaptive review evidence

- A full star histogram determines count, mean, low-star share, and dispersion inputs.
- Average + count supplies a bounded rating mean and support count.
- Rating with count unavailable remains visible, contributes provisional `n=1`, and sets `count_uncertain`.
- Written comments affect hard-fit or separately reported recurring risks only when the evidence supports that finding. Partial comments never receive free-form sentiment points.
- No reviews use the versioned prior interval; the product remains eligible rather than becoming zero-quality or perfect.

Record source URL, observation time, rating scale, count scope, verification/incentive/staff/syndication labels, and whether evidence is product-, listing-, variant-, store-, or seller-wide.

## Seller evidence

First-party retailers have no third-party seller population: `SellerFactor = 1` and seller evidence is `not_applicable`. Third-party offers use seller positive-feedback/rating plus its supporting feedback count. Seller transactions and listing sold counts are maturity/tie-break facts only. Never merge product reviews with seller feedback or listing sales with seller-wide transactions.
