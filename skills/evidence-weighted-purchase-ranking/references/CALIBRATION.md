# Empirical Calibration

Read this file only when the user has historical marketplace outcomes and wants the default ranking model calibrated. Normal recommendation runs do not need it.

The runtime defaults in `SKILL.md` are deliberately fixed so an agent can rank candidates from ordinary marketplace evidence without inventing category baselines. Do not call them empirically optimal.

## Calibration target

Define the outcome that "best purchase" means before fitting anything. Useful targets include:

- successful purchase or conversion;
- refund/return probability;
- dispute or item-not-as-described probability;
- delivery failure;
- post-purchase satisfaction;
- expected monetary loss;
- a composite utility explicitly defined by the user.

Do not fit to clicks or marketplace ranking position unless those are genuinely the desired outcomes; they encode platform behaviour rather than purchase quality.

## Preserve the population seams

Keep the raw runtime features separate during fitting:

- product/listing quality;
- product-review support;
- listing-sales support;
- seller quality;
- seller-feedback support;
- seller-transaction support;
- delivered unit cost;
- any explicitly active product features.

Do not merge listing sales with seller transactions or product reviews with seller feedback before fitting. A learned coefficient cannot repair a population mismatch.

## Fit and validate

Use future-held-out or seller-held-out validation so repeated observations from the same listing/seller do not leak into both train and test sets.

Prefer a monotone model or constraints that preserve sane directions unless the data identifies a separately interpretable adverse signal:

- lower delivered unit cost should not reduce value;
- higher product quality should not be a penalty;
- more supporting product evidence should not be a penalty;
- higher seller quality should not be a penalty;
- more supporting seller evidence should not be a penalty.

Compare the calibrated model against the unchanged runtime default on the held-out objective. Replace defaults only when the calibrated model materially improves out-of-sample ranking/utility and remains stable across relevant product categories or when a category-specific model is explicitly intended.

## Precision

Do not print extra decimal places merely because a fitted model has floating-point coefficients. Report only the precision justified by held-out stability. The runtime skill intentionally presents scores to one decimal place.
