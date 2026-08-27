"""Internal validated scoring primitives for the public rank.py CLI."""

import math
from collections.abc import Sequence


def require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def require_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return float(value)


def nonzero(value: float) -> float:
    return value if abs(value) >= 1e-300 else 1e-300


def advance_fraction(
    coefficient: float, denominator: float, current: float, result: float
) -> tuple[float, float, float, float]:
    denominator = 1.0 / nonzero(1.0 + coefficient * denominator)
    current = nonzero(1.0 + coefficient / current)
    delta = denominator * current
    return denominator, current, result * delta, delta


def beta_continued_fraction(alpha: float, beta: float, value: float) -> float:
    qab = alpha + beta
    qap = alpha + 1.0
    qam = alpha - 1.0
    current = 1.0
    denominator = 1.0 / nonzero(1.0 - qab * value / qap)
    result = denominator
    for iteration in range(1, 201):
        even = 2 * iteration
        coefficient = iteration * (beta - iteration) * value / (
            (qam + even) * (alpha + even)
        )
        denominator, current, result, _ = advance_fraction(
            coefficient, denominator, current, result
        )
        coefficient = -(
            (alpha + iteration)
            * (qab + iteration)
            * value
            / ((alpha + even) * (qap + even))
        )
        denominator, current, result, delta = advance_fraction(
            coefficient, denominator, current, result
        )
        if abs(delta - 1.0) < 3e-14:
            return result
    raise ArithmeticError("beta continued fraction did not converge")


def regularized_beta(value: float, alpha: float, beta: float) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    log_term = (
        math.lgamma(alpha + beta)
        - math.lgamma(alpha)
        - math.lgamma(beta)
        + alpha * math.log(value)
        + beta * math.log1p(-value)
    )
    term = math.exp(log_term)
    if value < (alpha + 1.0) / (alpha + beta + 2.0):
        return term * beta_continued_fraction(alpha, beta, value) / alpha
    return 1.0 - term * beta_continued_fraction(beta, alpha, 1.0 - value) / beta


def beta_quantile(probability: float, alpha: float, beta: float) -> float:
    lower = 0.0
    upper = 1.0
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if regularized_beta(midpoint, alpha, beta) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def normalized_rating(
    rating: dict[str, object], label: str
) -> tuple[float, float, float | None, bool]:
    scale_min = require_number(rating.get("scale_min"), f"{label}.scale_min")
    scale_max = require_number(rating.get("scale_max"), f"{label}.scale_max")
    if scale_max <= scale_min:
        raise ValueError(f"{label} has an invalid rating scale")
    histogram_value = rating.get("histogram")
    if histogram_value is not None:
        if not scale_min.is_integer() or not scale_max.is_integer():
            raise ValueError(f"{label} histogram requires an integer rating scale")
        histogram = require_mapping(histogram_value, f"{label}.histogram")
        total = 0.0
        weighted = 0.0
        low_count = 0.0
        for star in range(int(scale_min), int(scale_max) + 1):
            count = require_number(histogram.get(str(star), 0), f"{label}.histogram.{star}")
            if count < 0 or not count.is_integer():
                raise ValueError(f"{label}.histogram counts must be non-negative integers")
            total += count
            weighted += star * count
            if star <= scale_min + 1:
                low_count += count
        if total <= 0:
            raise ValueError(f"{label}.histogram must contain at least one rating")
        stated_count = rating.get("count")
        if stated_count is not None and require_number(stated_count, f"{label}.count") != total:
            raise ValueError(f"{label}.count does not match histogram")
        mean = weighted / total
        stated_mean = rating.get("mean")
        if stated_mean is not None and not math.isclose(
            require_number(stated_mean, f"{label}.mean"), mean, abs_tol=0.051
        ):
            raise ValueError(f"{label}.mean does not match histogram")
        return (mean - scale_min) / (scale_max - scale_min), total, low_count, False

    mean = require_number(rating.get("mean"), f"{label}.mean")
    if not scale_min <= mean <= scale_max:
        raise ValueError(f"{label} mean is outside its rating scale")
    count_value = rating.get("count")
    if count_value is None:
        return (mean - scale_min) / (scale_max - scale_min), 1.0, None, True
    count = require_number(count_value, f"{label}.count")
    if count < 0 or not count.is_integer():
        raise ValueError(f"{label}.count must be a non-negative integer")
    return (mean - scale_min) / (scale_max - scale_min), count, None, False


def policy_number(policy: dict[str, object], section: str, key: str) -> float:
    values = require_mapping(policy.get(section), f"policy.{section}")
    return require_number(values.get(key), f"policy.{section}.{key}")


def score_product(product_value: object, policy: dict[str, object]) -> dict[str, object]:
    product = require_mapping(product_value, "product")
    product_id = product.get("id")
    if not isinstance(product_id, str) or not product_id:
        raise ValueError("product.id must be a non-empty string")
    hard_fit = product.get("hard_fit")
    if not isinstance(hard_fit, bool):
        raise ValueError(f"product {product_id}.hard_fit must be boolean")
    provenance_warnings: list[dict[str, str]] = []
    identity = product.get("identity")
    if not isinstance(identity, dict) or identity.get("confidence") not in {
        "exact",
        "probable",
        "ambiguous",
    }:
        provenance_warnings.append(
            {
                "severity": "incomplete",
                "path": f"products.{product_id}.identity",
                "message": "identity confidence and identifiers/specification evidence are required",
            }
        )

    unique_corpora: dict[str, tuple[float, float, float | None, str, bool]] = {}
    deduplicated_source_ids: list[str] = []
    excluded_source_ids: list[str] = []
    source_summaries: list[dict[str, object]] = []
    seen_source_ids: set[str] = set()
    for index, source_value in enumerate(
        require_sequence(product.get("review_sources", []), f"product {product_id}.review_sources")
    ):
        source = require_mapping(source_value, f"product {product_id}.review_sources[{index}]")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(f"product {product_id} review source requires id")
        if source_id in seen_source_ids:
            raise ValueError(f"product {product_id} review source IDs must be unique")
        seen_source_ids.add(source_id)
        source_summaries.append(
            {
                "id": source_id,
                "url": source.get("url"),
                "source_ref": source.get("source_ref"),
                "corpus_id": source.get("corpus_id"),
                "identity_match": source.get("identity_match"),
                "observed_at": source.get("observed_at"),
                "labels": source.get("labels", []),
            }
        )
        if not source.get("url") and not source.get("source_ref"):
            provenance_warnings.append(
                {
                    "severity": "incomplete",
                    "path": f"products.{product_id}.review_sources.{source_id}.url_or_source_ref",
                    "message": "review evidence requires a URL or screenshot/file reference",
                }
            )
        if not source.get("observed_at"):
            provenance_warnings.append(
                {
                    "severity": "incomplete",
                    "path": f"products.{product_id}.review_sources.{source_id}.observed_at",
                    "message": "review evidence requires an observation time",
                }
            )
        if source.get("identity_match") != "exact":
            excluded_source_ids.append(source_id)
            continue
        corpus_id = source.get("corpus_id")
        if not isinstance(corpus_id, str) or not corpus_id:
            raise ValueError(f"product {product_id} exact review source requires corpus_id")
        rating = require_mapping(source.get("rating"), f"review source {corpus_id}.rating")
        normalized, count, low_count, count_uncertain = normalized_rating(
            rating, f"review source {corpus_id}.rating"
        )
        previous = unique_corpora.get(corpus_id)
        if previous is None or count > previous[1]:
            if previous is not None:
                deduplicated_source_ids.append(previous[3])
            unique_corpora[corpus_id] = (
                normalized,
                count,
                low_count,
                source_id,
                count_uncertain,
            )
        else:
            deduplicated_source_ids.append(source_id)

    reviewed_count = sum(corpus[1] for corpus in unique_corpora.values())
    observed_successes = sum(corpus[0] * corpus[1] for corpus in unique_corpora.values())
    alpha = policy_number(policy, "product_prior", "alpha") + observed_successes
    beta = policy_number(policy, "product_prior", "beta") + reviewed_count - observed_successes
    quality_lower = beta_quantile(
        policy_number(policy, "credible_interval", "lower"), alpha, beta
    )
    quality_upper = beta_quantile(
        policy_number(policy, "credible_interval", "upper"), alpha, beta
    )
    observed_mean = observed_successes / reviewed_count if reviewed_count else None
    product_factor = min(observed_mean, quality_lower) if observed_mean is not None else quality_lower
    low_star_share = None
    if unique_corpora and all(corpus[2] is not None for corpus in unique_corpora.values()):
        low_star_share = sum(float(corpus[2]) for corpus in unique_corpora.values()) / reviewed_count
    used_source_ids = sorted(corpus[3] for corpus in unique_corpora.values())
    used_set = set(used_source_ids)
    deduplicated_set = set(deduplicated_source_ids)
    review_source_decisions = [
        {
            **summary,
            "status": (
                "used"
                if summary["id"] in used_set
                else "deduplicated"
                if summary["id"] in deduplicated_set
                else "excluded"
            ),
        }
        for summary in source_summaries
    ]
    return {
        "product_id": product_id,
        "name": product.get("name"),
        "identity": identity,
        "hard_fit": hard_fit,
        "hard_fit_reason": product.get("hard_fit_reason"),
        "product_factor": product_factor,
        "quality_mean": alpha / (alpha + beta),
        "quality_low": quality_lower,
        "quality_high": quality_upper,
        "observed_normalized_rating": observed_mean,
        "review_count_used": reviewed_count,
        "low_star_share": low_star_share,
        "count_uncertain": any(corpus[4] for corpus in unique_corpora.values()),
        "used_source_ids": used_source_ids,
        "deduplicated_source_ids": sorted(deduplicated_source_ids),
        "excluded_source_ids": sorted(excluded_source_ids),
        "review_source_decisions": review_source_decisions,
        "provenance_warnings": provenance_warnings,
    }


def landed_cost(offer: dict[str, object]) -> tuple[float, float | None, list[str]]:
    cost = require_mapping(offer.get("cost"), f"offer {offer.get('id')}.cost")
    currency = cost.get("currency")
    if not isinstance(currency, str) or not currency:
        raise ValueError(f"offer {offer.get('id')}.cost.currency must be a string")
    fx_to_nzd = require_number(cost.get("fx_to_nzd"), f"offer {offer.get('id')}.cost.fx_to_nzd")
    if fx_to_nzd <= 0:
        raise ValueError(f"offer {offer.get('id')}.cost.fx_to_nzd must be positive")
    if currency == "NZD":
        if not math.isclose(fx_to_nzd, 1.0):
            raise ValueError(f"offer {offer.get('id')} NZD fx_to_nzd must equal 1")
    else:
        for field in ("fx_source", "fx_as_of"):
            value = cost.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"offer {offer.get('id')}.cost.{field} is required for {currency}")
    components = require_mapping(cost.get("components"), f"offer {offer.get('id')}.cost.components")
    total_low = 0.0
    total_high = 0.0
    unbounded = False
    unknown_components: list[str] = []
    for name in ("item", "shipping", "tax", "mandatory_fees", "eligible_discount"):
        component = require_mapping(components.get(name), f"offer {offer.get('id')}.cost.{name}")
        state = component.get("state")
        if state == "not_applicable":
            low_amount = 0.0
            high_amount = 0.0
        elif state == "observed":
            low_amount = require_number(component.get("amount"), f"offer {offer.get('id')}.cost.{name}.amount")
            if low_amount < 0:
                raise ValueError(f"offer {offer.get('id')}.cost.{name}.amount cannot be negative")
            high_amount = low_amount
        elif state in {"missing", "unavailable", "ambiguous"} and name != "item":
            unknown_components.append(name)
            if name == "eligible_discount":
                low_amount = 0.0
                high_amount = 0.0
            else:
                low_amount = require_number(
                    component.get("lower_amount", 0.0),
                    f"offer {offer.get('id')}.cost.{name}.lower_amount",
                )
                upper_value = component.get("upper_amount")
                if upper_value is None:
                    high_amount = 0.0
                    unbounded = True
                else:
                    high_amount = require_number(
                        upper_value, f"offer {offer.get('id')}.cost.{name}.upper_amount"
                    )
                    if high_amount < low_amount:
                        raise ValueError(f"offer {offer.get('id')}.cost.{name} bounds are invalid")
        else:
            raise ValueError(f"offer {offer.get('id')}.cost.{name} has an invalid state")
        if low_amount < 0 or high_amount < 0:
            raise ValueError(f"offer {offer.get('id')}.cost.{name} amounts cannot be negative")
        if name == "eligible_discount":
            total_low -= low_amount
            total_high -= high_amount
        else:
            total_low += low_amount
            total_high += high_amount
    if total_low < 0 or total_high < 0:
        raise ValueError(f"offer {offer.get('id')} landed cost cannot be negative")
    return total_low * fx_to_nzd, None if unbounded else total_high * fx_to_nzd, unknown_components


def score_seller(
    offer: dict[str, object], policy: dict[str, object]
) -> tuple[float, float, float]:
    merchant_type = offer.get("merchant_type")
    if merchant_type == "first_party":
        return 1.0, 1.0, 0.0
    if merchant_type != "third_party":
        raise ValueError(f"offer {offer.get('id')}.merchant_type is invalid")
    evidence_value = offer.get("seller_evidence")
    observed = 0.0
    count = 0.0
    if evidence_value is not None:
        evidence = require_mapping(evidence_value, f"offer {offer.get('id')}.seller_evidence")
        if "positive_feedback_pct" in evidence:
            observed = require_number(
                evidence.get("positive_feedback_pct"),
                f"offer {offer.get('id')}.seller_evidence.positive_feedback_pct",
            ) / 100.0
            if not 0.0 <= observed <= 1.0:
                raise ValueError(f"offer {offer.get('id')} seller feedback must be 0..100")
            count_value = evidence.get("count")
            count = 1.0 if count_value is None else require_number(
                count_value, f"offer {offer.get('id')}.seller_evidence.count"
            )
        else:
            observed, count, _, _ = normalized_rating(
                require_mapping(
                    evidence.get("rating"), f"offer {offer.get('id')}.seller_evidence.rating"
                ),
                f"offer {offer.get('id')}.seller_evidence.rating",
            )
        if count < 0 or not count.is_integer():
            raise ValueError(f"offer {offer.get('id')} seller evidence count must be integral")
    alpha = policy_number(policy, "seller_prior", "alpha") + observed * count
    beta = policy_number(policy, "seller_prior", "beta") + (1.0 - observed) * count
    factor = beta_quantile(policy_number(policy, "credible_interval", "lower"), alpha, beta)
    upper = beta_quantile(policy_number(policy, "credible_interval", "upper"), alpha, beta)
    if count:
        factor = min(observed, factor)
    return factor, upper, count


def offer_identity(offer: dict[str, object]) -> tuple[str, str]:
    offer_id = offer.get("id")
    product_id = offer.get("product_id")
    if not isinstance(offer_id, str) or not offer_id:
        raise ValueError("offer.id must be a non-empty string")
    if not isinstance(product_id, str) or not product_id:
        raise ValueError(f"offer {offer_id}.product_id must be a non-empty string")
    return offer_id, product_id


def score_offer(
    offer: dict[str, object],
    products: dict[str, dict[str, object]],
    needed_quantity: float,
    policy: dict[str, object],
) -> dict[str, object]:
    offer_id, product_id = offer_identity(offer)
    if product_id not in products:
        raise ValueError(f"offer {offer_id}.product_id must reference a product")
    pack_quantity = require_number(offer.get("pack_quantity"), f"offer {offer_id}.pack_quantity")
    packs_purchased = require_number(offer.get("packs_purchased"), f"offer {offer_id}.packs_purchased")
    if pack_quantity <= 0 or packs_purchased <= 0 or not packs_purchased.is_integer():
        raise ValueError(f"offer {offer_id} quantities must be positive and packs_purchased integral")
    received_quantity = pack_quantity * packs_purchased
    if received_quantity < needed_quantity:
        raise ValueError(f"offer {offer_id} does not meet needed_quantity")
    cost_low_nzd, cost_high_nzd, unknown_components = landed_cost(offer)
    region = offer.get("region")
    multipliers = require_mapping(policy.get("region_multiplier"), "policy.region_multiplier")
    if not isinstance(region, str) or region not in multipliers:
        raise ValueError(f"offer {offer_id}.region is invalid")
    region_multiplier = require_number(multipliers[region], f"policy.region_multiplier.{region}")
    product_factor = require_number(products[product_id]["product_factor"], "product_factor")
    seller_factor, seller_factor_high, seller_feedback_count = score_seller(offer, policy)
    product_factor_high = require_number(products[product_id]["quality_high"], "quality_high")
    decision_cost_best = region_multiplier * cost_low_nzd / (
        product_factor_high * seller_factor_high
    )
    denominator = product_factor * seller_factor
    decision_cost = (
        None
        if cost_high_nzd is None or denominator <= 0
        else region_multiplier * cost_high_nzd / denominator
    )
    sold_count = offer.get("sold_count")
    if sold_count is not None:
        sold_count = require_number(sold_count, f"offer {offer_id}.sold_count")
        if sold_count < 0 or not sold_count.is_integer():
            raise ValueError(f"offer {offer_id}.sold_count must be a non-negative integer")
    cost = require_mapping(offer.get("cost"), f"offer {offer_id}.cost")
    provenance_warnings: list[dict[str, str]] = []
    if not offer.get("url") and not offer.get("source_ref"):
        provenance_warnings.append(
            {
                "severity": "incomplete",
                "path": f"offers.{offer_id}.url_or_source_ref",
                "message": "offer requires a URL or screenshot/file reference",
            }
        )
    for field in ("retailer", "fulfilment_origin", "selected_variant"):
        if not isinstance(offer.get(field), str) or not offer.get(field):
            provenance_warnings.append(
                {
                    "severity": "incomplete",
                    "path": f"offers.{offer_id}.{field}",
                    "message": f"offer {field} is required",
                }
            )
    return {
        "offer_id": offer_id,
        "product_id": product_id,
        "url": offer.get("url"),
        "source_ref": offer.get("source_ref"),
        "retailer": offer.get("retailer"),
        "merchant_type": offer.get("merchant_type"),
        "region": region,
        "fulfilment_origin": offer.get("fulfilment_origin"),
        "selected_variant": offer.get("selected_variant"),
        "region_multiplier": region_multiplier,
        "currency": cost.get("currency"),
        "fx_to_nzd": cost.get("fx_to_nzd"),
        "fx_source": cost.get("fx_source"),
        "fx_as_of": cost.get("fx_as_of"),
        "landed_cost_low_nzd": cost_low_nzd,
        "landed_cost_high_nzd": cost_high_nzd,
        "useful_quantity": needed_quantity,
        "surplus_quantity": received_quantity - needed_quantity,
        "product_factor": product_factor,
        "seller_factor": seller_factor,
        "seller_factor_high": seller_factor_high,
        "seller_feedback_count": seller_feedback_count,
        "decision_cost": decision_cost,
        "decision_cost_best": decision_cost_best,
        "decision_cost_worst": decision_cost,
        "unknown_cost_components": unknown_components,
        "cost_unbounded": cost_high_nzd is None,
        "sold_count": sold_count,
        "provenance_warnings": provenance_warnings,
    }
