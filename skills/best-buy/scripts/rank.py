#!/usr/bin/env python3
import argparse
import json
import math
import sys
from pathlib import Path

from model import (
    offer_identity,
    provenance_warning,
    require_mapping,
    require_number,
    require_sequence,
    score_offer,
    score_product,
    validate_policy,
)


DEFAULT_POLICY_PATH = Path(__file__).with_name("default-policy.json")
INPUT_TEMPLATE_PATH = Path(__file__).with_name("input-template.json")


def input_template() -> dict[str, object]:
    with open(INPUT_TEMPLATE_PATH, encoding="utf-8") as template_file:
        return require_mapping(json.load(template_file), "input template")


def upper_sort_value(value: object) -> float:
    return require_number(value, "sort value") if value is not None else math.inf


def rank_comparison(payload: object, policy: dict[str, object]) -> dict[str, object]:
    validate_policy(policy)
    comparison = require_mapping(payload, "input")
    settings = require_mapping(comparison.get("comparison"), "comparison")
    needed_quantity = require_number(
        settings.get("needed_quantity"), "comparison.needed_quantity"
    )
    if needed_quantity <= 0:
        raise ValueError("comparison.needed_quantity must be positive")

    products = [
        score_product(value, policy)
        for value in require_sequence(comparison.get("products"), "products")
    ]
    products.sort(key=lambda product: str(product["product_id"]))
    product_by_id: dict[str, dict[str, object]] = {}
    for product in products:
        product_id = str(product["product_id"])
        if product_id in product_by_id:
            raise ValueError(f"product {product_id} is duplicated")
        product_by_id[product_id] = product
    quality_ranking = sorted(
        products,
        key=lambda product: (
            -float(product["product_factor"]),
            -float(product["review_count_used"]),
            str(product["product_id"]),
        ),
    )

    offers: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    seen_offer_ids: set[str] = set()
    for offer_value in require_sequence(comparison.get("offers"), "offers"):
        offer = require_mapping(offer_value, "offer")
        offer_id, product_id = offer_identity(offer)
        if offer_id in seen_offer_ids:
            raise ValueError(f"offer {offer_id} is duplicated")
        seen_offer_ids.add(offer_id)
        if product_id not in product_by_id:
            raise ValueError(f"offer {offer_id}.product_id must reference a product")
        product = product_by_id[product_id]
        if offer.get("hard_fit") is not True or product.get("hard_fit") is not True:
            reason = offer.get("hard_fit_reason") or product.get("hard_fit_reason")
            if not isinstance(reason, str) or not reason:
                raise ValueError(f"excluded offer {offer_id} requires hard_fit_reason")
            excluded.append({"offer_id": offer_id, "reason": reason})
            continue
        offers.append(score_offer(offer, product_by_id, needed_quantity, policy))
    offers.sort(key=lambda offer: str(offer["offer_id"]))

    region_order = {"NZ": 0, "AU": 1, "international": 2}
    diagnostic_ranking = sorted(
        offers,
        key=lambda offer: (
            upper_sort_value(offer["decision_cost"]),
            float(offer["decision_cost_best"]),
            upper_sort_value(offer["landed_cost_high_nzd"]),
            float(offer["landed_cost_low_nzd"]),
            -float(offer["product_factor"]),
            region_order[str(offer["region"])],
            -float(product_by_id[str(offer["product_id"])]["review_count_used"]),
            -(
                float(offer["seller_feedback_count"])
                if offer["seller_feedback_count"] is not None
                else -1.0
            ),
            -(float(offer["sold_count"]) if offer["sold_count"] is not None else -1.0),
            str(offer["offer_id"]),
        ),
    )
    ranking = [offer for offer in diagnostic_ranking if offer["value_eligible"]]
    unverified_value_contenders = [
        offer for offer in diagnostic_ranking if not offer["value_eligible"]
    ]
    raw_ranking = sorted(
        offers,
        key=lambda offer: (
            upper_sort_value(offer["landed_cost_high_nzd"]),
            float(offer["landed_cost_low_nzd"]),
            str(offer["offer_id"]),
        ),
    )
    raw_leader = raw_ranking[0] if raw_ranking else None
    raw_contenders = raw_landed_contenders(raw_leader, raw_ranking, offers)
    raw_leader_unresolved = (
        raw_leader is not None
        and raw_leader["landed_cost_low_nzd"]
        != raw_leader["landed_cost_high_nzd"]
    )
    raw_status = (
        "incomplete"
        if raw_leader is None or raw_leader_unresolved or raw_contenders
        else "robust"
    )

    leader = ranking[0] if ranking else None
    set_unknown_cost_break_evens(leader, offers)
    status = ranking_status(leader, ranking)
    if (
        status == "robust"
        and leader is not None
        and leader.get("product_identity_confidence") != "exact"
    ):
        status = "provisional"

    provenance_warnings = [
        warning
        for item in [*products, *offers]
        for warning in require_sequence(
            item.get("provenance_warnings"), "provenance_warnings"
        )
    ]
    if not settings.get("observed_at"):
        provenance_warnings.append(provenance_warning(
            "comparison.observed_at", "comparison observation time is recommended", "warning"
        ))
    value_provenance_warnings = [
        warning
        for item in [
            *[product for product in products if product["value_eligible"]],
            *ranking,
        ]
        for warning in require_sequence(
            item.get("provenance_warnings"), "provenance_warnings"
        )
    ]
    if any(
        require_mapping(warning, "provenance warning").get("severity")
        == "incomplete"
        for warning in value_provenance_warnings
    ):
        status = "incomplete"

    return {
        "model_version": policy.get("model_version"),
        "products": products,
        "product_quality_ranking": [
            {
                "rank": index + 1,
                "product_id": product["product_id"],
                "product_factor": product["product_factor"],
            }
            for index, product in enumerate(quality_ranking)
        ],
        "offers": offers,
        "excluded": sorted(excluded, key=lambda item: item["offer_id"]),
        "ranking": [{"rank": index + 1, **offer} for index, offer in enumerate(ranking)],
        "price_ranking": [
            {"rank": index + 1, **offer} for index, offer in enumerate(raw_ranking)
        ],
        "unverified_value_contenders": [
            {"rank": index + 1, **offer}
            for index, offer in enumerate(unverified_value_contenders)
        ],
        "raw_landed_ranking": [offer["offer_id"] for offer in raw_ranking],
        "raw_landed_winner": (
            raw_leader["offer_id"]
            if raw_leader is not None and raw_status == "robust"
            else None
        ),
        "raw_landed_leader": raw_leader["offer_id"] if raw_leader else None,
        "raw_landed_status": raw_status,
        "raw_landed_contenders": sorted(raw_contenders),
        "best_price": {
            "status": raw_status,
            "winner": (
                raw_leader["offer_id"]
                if raw_leader is not None and raw_status == "robust"
                else None
            ),
            "leader": raw_leader["offer_id"] if raw_leader else None,
            "contenders": sorted(raw_contenders),
            "ranking": [offer["offer_id"] for offer in raw_ranking],
        },
        "evidence_backed_value": {
            "status": status,
            "winner": leader["offer_id"] if leader is not None and status == "robust" else None,
            "leader": leader["offer_id"] if leader else None,
            "ranking": [offer["offer_id"] for offer in ranking],
            "unverified_contenders": [
                {
                    "offer_id": offer["offer_id"],
                    "evidence_status": offer["evidence_status"],
                }
                for offer in unverified_value_contenders
            ],
        },
        "winner": leader["offer_id"] if leader is not None and status == "robust" else None,
        "leader": leader["offer_id"] if leader else None,
        "regional_alternative": regional_alternative(leader, ranking),
        "provenance_warnings": provenance_warnings,
        "status": status,
    }


def raw_landed_contenders(
    leader: dict[str, object] | None,
    raw_ranking: list[dict[str, object]],
    offers: list[dict[str, object]],
) -> list[str]:
    if leader is None:
        return []
    leader_high = leader["landed_cost_high_nzd"]
    if leader_high is None:
        return [str(offer["offer_id"]) for offer in raw_ranking[1:]]
    return [
        str(offer["offer_id"])
        for offer in offers
        if offer is not leader
        and offer["landed_cost_low_nzd"] != offer["landed_cost_high_nzd"]
        and require_number(offer["landed_cost_low_nzd"], "landed_cost_low_nzd")
        <= require_number(leader_high, "raw leader cost")
    ]


def set_unknown_cost_break_evens(
    winner: dict[str, object] | None, offers: list[dict[str, object]]
) -> None:
    for offer in offers:
        offer["unknown_charge_break_even_nzd"] = None
    if winner is None:
        return
    winner_decision = winner["decision_cost"]
    if winner_decision is None:
        return
    winner_cost = require_number(winner_decision, "winner decision cost")
    for offer in offers:
        if not offer["cost_unbounded"]:
            continue
        threshold = (
            winner_cost
            * require_number(offer["product_factor"], "product_factor")
            * require_number(offer["seller_factor"], "seller_factor")
            / require_number(offer["region_multiplier"], "region_multiplier")
        )
        offer["unknown_charge_break_even_nzd"] = max(
            0.0,
            threshold
            - require_number(offer["landed_cost_low_nzd"], "landed_cost_low_nzd"),
        )


def ranking_status(
    winner: dict[str, object] | None, offers: list[dict[str, object]]
) -> str:
    if winner is None:
        return "incomplete"
    if winner["decision_cost"] is None:
        return "incomplete"
    provisional = (
        winner["landed_cost_low_nzd"] != winner["landed_cost_high_nzd"]
    )
    for rival in offers:
        if rival is winner:
            continue
        if rival["product_id"] == winner["product_id"]:
            winner_worst = (
                require_number(winner["region_multiplier"], "region_multiplier")
                * require_number(winner["landed_cost_high_nzd"], "landed_cost_high_nzd")
                / require_number(winner["seller_factor"], "seller_factor")
            )
            rival_best = (
                require_number(rival["region_multiplier"], "region_multiplier")
                * require_number(rival["landed_cost_low_nzd"], "landed_cost_low_nzd")
                / require_number(rival["seller_factor_high"], "seller_factor_high")
            )
        else:
            winner_worst = require_number(
                winner["decision_cost"], "winner decision cost"
            )
            rival_best = require_number(rival["decision_cost_best"], "decision_cost_best")
        if rival["cost_unbounded"] and rival_best < winner_worst:
            return "incomplete"
        if winner_worst >= rival_best:
            provisional = True
    return "provisional" if provisional else "robust"


def regional_alternative(
    winner: dict[str, object] | None, ranking: list[dict[str, object]]
) -> dict[str, object] | None:
    if winner is None or winner.get("region") == "NZ":
        return None
    preferred_regions = {"NZ"} if winner.get("region") == "AU" else {"NZ", "AU"}
    alternative = next(
        (offer for offer in ranking if offer.get("region") in preferred_regions), None
    )
    if alternative is None:
        return None
    winner_cost = winner.get("landed_cost_high_nzd")
    alternative_cost = alternative.get("landed_cost_high_nzd")
    premium = None
    if winner_cost is not None and alternative_cost is not None:
        premium = require_number(alternative_cost, "alternative cost") - require_number(
            winner_cost, "winner cost"
        )
    return {
        "offer_id": alternative["offer_id"],
        "region": alternative["region"],
        "landed_cost_nzd": alternative_cost,
        "landed_premium_nzd": premium,
    }


def display_number(value: object, digits: int = 2) -> str:
    if value is None:
        return "unknown"
    return f"{require_number(value, 'display value'):.{digits}f}"


def result_rows(result: dict[str, object], key: str) -> list[dict[str, object]]:
    return [
        require_mapping(value, f"{key} item")
        for value in require_sequence(result.get(key), key)
    ]


def markdown_row(*values: object) -> str:
    return "| " + " | ".join(
        str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
        for value in values
    ) + " |"


def start_table(lines: list[str], title: str, header: str, separator: str) -> None:
    lines.extend(["", f"## {title}", "", header, separator])


def cost_uncertainty_line(offer: dict[str, object]) -> str:
    components = ", ".join(
        str(value)
        for value in require_sequence(
            offer.get("unknown_cost_components"), "unknown_cost_components"
        )
    )
    if offer.get("cost_unbounded"):
        detail = (
            "combined break-even NZ$"
            + display_number(offer.get("unknown_charge_break_even_nzd"))
        )
    else:
        detail = (
            f"landed range NZ${display_number(offer.get('landed_cost_low_nzd'))}-"
            f"NZ${display_number(offer.get('landed_cost_high_nzd'))}"
        )
    return f"- `{offer.get('offer_id')}`: {components}; {detail}."


def render_markdown(result: dict[str, object]) -> str:
    products = result_rows(result, "products")
    quality_ranking = result_rows(result, "product_quality_ranking")
    quality_rank_by_id = {
        str(item["product_id"]): item["rank"] for item in quality_ranking
    }
    offers = result_rows(result, "offers")
    ranking = result_rows(result, "ranking")
    price_ranking = result_rows(result, "price_ranking")
    unverified = result_rows(result, "unverified_value_contenders")
    best_price = require_mapping(result.get("best_price"), "best_price")
    best_value = require_mapping(
        result.get("evidence_backed_value"), "evidence_backed_value"
    )
    price_winner = best_price.get("winner")
    value_winner = best_value.get("winner")
    value_leader = best_value.get("leader")
    lines = [
        "# Purchase ranking",
        "",
        (
            f"Evidence-backed value winner: `{value_winner}`"
            if value_winner is not None
            else f"Evidence-backed value leader: `{value_leader}`"
            if value_leader is not None
            else "Evidence-backed best value: incomplete - no eligible product"
        ),
        f"Evidence-backed value status: `{best_value.get('status')}`",
        (
            f"Best-price winner: `{price_winner}`"
            if price_winner is not None
            else "Best-price winner: unresolved; leader "
            f"`{best_price.get('leader')}`"
            if best_price.get("leader") is not None
            else "Best price: incomplete - no qualifying offer"
        ),
        f"Best-price status: `{best_price.get('status')}`",
        f"Model: `{result.get('model_version')}`",
        "",
        "## Evidence-backed best value",
        "",
        "Only evidence-backed products are eligible. Decision cost is lower-is-better.",
        "",
        "| Rank | Offer | Product | Region | Landed NZD low-high | Useful qty | Region factor | Product factor | Seller factor | Decision best | Decision worst |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in ranking:
        lines.append(markdown_row(
            item.get("rank"), item.get("offer_id"), item.get("product_id"),
            item.get("region"),
            f"{display_number(item.get('landed_cost_low_nzd'))}-{display_number(item.get('landed_cost_high_nzd'))}",
            display_number(item.get("useful_quantity")),
            display_number(item.get("region_multiplier"), 3),
            display_number(item.get("product_factor"), 3),
            display_number(item.get("seller_factor"), 3),
            display_number(item.get("decision_cost_best")),
            display_number(item.get("decision_cost_worst")),
        ))

    if unverified:
        start_table(
            lines, "Unverified value contenders",
            "| Diagnostic rank | Offer | Product | Evidence status | Landed NZD low-high | Product factor |",
            "| ---: | --- | --- | --- | ---: | ---: |",
        )
        for item in unverified:
            lines.append(markdown_row(
                item.get("rank"), item.get("offer_id"), item.get("product_id"),
                item.get("evidence_status"),
                f"{display_number(item.get('landed_cost_low_nzd'))}-{display_number(item.get('landed_cost_high_nzd'))}",
                display_number(item.get("product_factor"), 3),
            ))

    lines.extend([
        "",
        "## Best price",
        "",
        "Resolved landed cost only; product evidence does not affect this order.",
        "",
        "| Rank | Offer | Product | Landed NZD low-high | Evidence status |",
        "| ---: | --- | --- | ---: | --- |",
    ])
    for item in price_ranking:
        lines.append(markdown_row(
            item.get("rank"), item.get("offer_id"), item.get("product_id"),
            f"{display_number(item.get('landed_cost_low_nzd'))}-{display_number(item.get('landed_cost_high_nzd'))}",
            item.get("evidence_status"),
        ))

    start_table(
        lines, "Offer details",
        "| Offer | Retailer / merchant type | Fulfilment | Selected variant | URL | Currency / FX source / date |",
        "| --- | --- | --- | --- | --- | --- |",
    )
    for offer in offers:
        lines.append(markdown_row(
            offer.get("offer_id"),
            f"{offer.get('retailer')} / {offer.get('merchant_type')}",
            offer.get("fulfilment_origin"), offer.get("selected_variant"),
            offer.get("url") or offer.get("source_ref"),
            f"{offer.get('currency')} x {offer.get('fx_to_nzd')} / {offer.get('fx_source')} / {offer.get('fx_as_of')}",
        ))

    start_table(
        lines, "Product evidence",
        "| Rank | Product | Evidence status | Identity | Exact consumer reviews | Expert tests | Product factor | Quality low | Quality mean | Quality high | Low-star share |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    )
    for product in products:
        lines.append(markdown_row(
            quality_rank_by_id[str(product.get("product_id"))], product.get("product_id"),
            product.get("evidence_status"),
            json.dumps(product.get("identity"), sort_keys=True),
            display_number(product.get("exact_consumer_review_count"), 0),
            display_number(product.get("independent_expert_test_count"), 0),
            display_number(product.get("product_factor"), 3),
            display_number(product.get("quality_low"), 3),
            display_number(product.get("quality_mean"), 3),
            display_number(product.get("quality_high"), 3),
            display_number(product.get("low_star_share"), 3),
        ))

    start_table(
        lines, "Review-source decisions",
        "| Product | Source | Status | Evidence type | Corpus | Identity match | URL | Observed | Labels |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    )
    for product in products:
        for source_value in require_sequence(
            product.get("review_source_decisions"), "review_source_decisions"
        ):
            source = require_mapping(source_value, "review source decision")
            labels = ", ".join(
                str(value)
                for value in require_sequence(source.get("labels"), "source labels")
            )
            lines.append(markdown_row(
                product.get("product_id"), source.get("id"), source.get("status"),
                source.get("evidence_type"),
                source.get("corpus_id"), source.get("identity_match"),
                source.get("url") or source.get("source_ref"),
                source.get("observed_at"), labels,
            ))

    unknown = [offer for offer in offers if offer.get("unknown_cost_components")]
    if unknown:
        lines.extend(["", "## Cost uncertainty", ""])
        lines.extend(cost_uncertainty_line(offer) for offer in unknown)

    excluded = result_rows(result, "excluded")
    if excluded:
        lines.extend(["", "## Excluded offers", ""])
        lines.extend(f"- `{item.get('offer_id')}`: {item.get('reason')}" for item in excluded)

    warnings = result_rows(result, "provenance_warnings")
    if warnings:
        lines.extend(["", "## Provenance warnings", ""])
        lines.extend(
            f"- `{warning.get('severity')}` `{warning.get('path')}`: {warning.get('message')}"
            for warning in warnings
        )

    alternative_value = result.get("regional_alternative")
    if alternative_value is not None:
        alternative = require_mapping(alternative_value, "regional_alternative")
        lines.extend(
            [
                "",
                "## Preferred-region alternative",
                "",
                f"`{alternative.get('offer_id')}` ({alternative.get('region')}), landed premium "
                f"NZ${display_number(alternative.get('landed_premium_nzd'))}.",
            ]
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank retail and marketplace purchase offers")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="JSON input path, or - for stdin")
    source.add_argument("--template", action="store_true", help="print a normalized input template")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH), help="policy JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.template:
        json.dump(input_template(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    with open(args.policy, encoding="utf-8") as policy_file:
        policy = require_mapping(json.load(policy_file), "policy")
    if args.input == "-":
        payload = json.load(sys.stdin)
    else:
        with open(args.input, encoding="utf-8") as input_file:
            payload = json.load(input_file)
    result = rank_comparison(payload, policy)
    if args.format == "markdown":
        sys.stdout.write(render_markdown(result))
    else:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
