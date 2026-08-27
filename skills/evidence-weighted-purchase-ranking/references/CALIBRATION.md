# Empirical Calibration

Read this file only when historical outcomes are available and the user asks to replace versioned defaults. Normal rankings use `scripts/default-policy.json` unchanged.

Define the target first: satisfaction, return/refund, dispute, delivery failure, expected monetary loss, or a user-defined utility. Do not fit to clicks, marketplace position, or sales volume unless popularity itself is the desired outcome.

Preserve Product, ReviewCorpus, Offer, and Seller seams. Candidate features may include product rating successes/count, low-star share, seller feedback successes/count, landed cost, region, delivery outcome, returns/warranty, and a comparable service-life measure. Sold/transaction volume remains distinct from satisfaction outcomes.

Use future-held-out and seller/product-held-out validation to prevent repeated products, syndicated corpora, or merchants leaking across train and test. Compare the calibrated model against the unchanged default on the declared outcome. Replace defaults only when out-of-sample utility materially improves and monotone directions remain sensible:

- lower landed cost cannot hurt value;
- stronger above-prior review evidence cannot reduce conservative quality;
- stronger below-prior review evidence cannot improve conservative quality;
- sold/transactions alone cannot improve satisfaction quality;
- missing marketplace-only fields cannot penalize direct retailers;
- exact duplicate corpora count once;
- NZ/AU preference remains explicit rather than hidden in product quality.

Version any changed prior, credible interval, regional multiplier, or tie-break policy. Report training population, time range, held-out design, uncertainty, and categories where the model is not validated. Do not print precision unsupported by held-out stability.
