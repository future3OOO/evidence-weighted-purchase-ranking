import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RANKER = REPO / "skills" / "evidence-weighted-purchase-ranking" / "scripts" / "rank.py"


class RankingCliTests(unittest.TestCase):
    def run_ranker(self, comparison: dict) -> dict:
        completed = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-", "--format", "json"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_template_is_valid_normalized_input(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RANKER), "--template"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        template = json.loads(completed.stdout)
        self.assertIn("comparison", template)
        self.assertEqual(template["comparison"]["postcode"], "6011")
        self.assertIn("products", template)
        self.assertIn("offers", template)
        result = self.run_ranker(template)
        self.assertEqual(result["winner"], "example-nz-offer")
        self.assertEqual(result["products"][0]["review_source_decisions"][0]["status"], "used")
        self.assertEqual(
            result["products"][0]["review_source_decisions"][0]["url"],
            "https://example.nz/products/ex-100",
        )
        self.assertEqual(result["offers"][0]["merchant_type"], "first_party")
        self.assertEqual(result["offers"][0]["fx_source"], "native NZD")

    def test_markdown_output_contains_the_computed_winner_and_scores(self) -> None:
        comparison = json.loads((RANKER.parent / "input-template.json").read_text(encoding="utf-8"))
        result = self.run_ranker(comparison)
        completed = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-", "--format", "markdown"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Winner: `example-nz-offer`", completed.stdout)
        self.assertIn("Decision cost", completed.stdout)
        self.assertIn("Raw landed-cost status", completed.stdout)
        self.assertIn("Decision best", completed.stdout)
        self.assertIn("Review-source decisions", completed.stdout)
        self.assertIn("https://example.nz/products/ex-100", completed.stdout)
        self.assertIn("NZ-compatible", completed.stdout)
        self.assertIn(f"{result['products'][0]['product_factor']:.3f}", completed.stdout)

    def test_two_offer_markdown_is_safe_on_windows_cp1252(self) -> None:
        comparison = json.loads(
            (RANKER.parent / "input-template.json").read_text(encoding="utf-8")
        )
        second_offer = {**comparison["offers"][0], "id": "example-second-offer"}
        comparison["offers"].append(second_offer)
        environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}

        completed = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-", "--format", "markdown"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "`example-nz-offer` -> `example-second-offer`", completed.stdout
        )

    def test_sales_volume_cannot_turn_a_poor_rating_into_quality(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "popular-poor",
                    "name": "Popular poor product",
                    "hard_fit": True,
                    "review_sources": [
                        {
                            "id": "poor-reviews",
                            "corpus_id": "poor-native",
                            "identity_match": "exact",
                            "rating": {
                                "mean": 3.0,
                                "scale_min": 1,
                                "scale_max": 5,
                                "count": 10000,
                            },
                        }
                    ],
                },
                {
                    "id": "sparse-excellent",
                    "name": "Sparse excellent product",
                    "hard_fit": True,
                    "review_sources": [
                        {
                            "id": "excellent-reviews",
                            "corpus_id": "excellent-native",
                            "identity_match": "exact",
                            "rating": {
                                "mean": 5.0,
                                "scale_min": 1,
                                "scale_max": 5,
                                "count": 1,
                            },
                        }
                    ],
                },
            ],
            "offers": [
                self.offer("poor-offer", "popular-poor", sold_count=10000),
                self.offer("excellent-offer", "sparse-excellent", sold_count=1),
            ],
        }

        result = self.run_ranker(comparison)
        quality = {
            product["product_id"]: product["product_factor"]
            for product in result["products"]
        }
        self.assertGreater(quality["sparse-excellent"], quality["popular-poor"])

    def test_sparse_reviews_use_the_exact_beta_lower_quantile(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "six-perfect-reviews",
                    "name": "Six perfect reviews",
                    "hard_fit": True,
                    "review_sources": [
                        {
                            "id": "six-perfect-native",
                            "corpus_id": "six-perfect-native",
                            "identity_match": "exact",
                            "rating": {
                                "mean": 5.0,
                                "scale_min": 1,
                                "scale_max": 5,
                                "count": 6,
                            },
                        }
                    ],
                }
            ],
            "offers": [self.offer("six-perfect-offer", "six-perfect-reviews", sold_count=60)],
        }

        result = self.run_ranker(comparison)
        self.assertAlmostEqual(result["products"][0]["product_factor"], 0.723, delta=0.002)

    def test_regional_preference_has_an_explicit_overseas_hurdle(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "same-product",
                    "name": "Same exact product",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [
                self.offer("nz-100", "same-product", price=100, region="NZ"),
                self.offer("international-85", "same-product", price=85, region="international"),
                self.offer("international-75", "same-product", price=75, region="international"),
            ],
        }

        result = self.run_ranker(comparison)
        decisions = {
            offer["offer_id"]: offer["decision_cost"] for offer in result["offers"]
        }
        self.assertLess(decisions["nz-100"], decisions["international-85"])
        self.assertLess(decisions["international-75"], decisions["nz-100"])
        self.assertEqual(result["ranking"][0]["offer_id"], "international-75")
        self.assertEqual(result["raw_landed_winner"], "international-75")
        self.assertEqual(result["regional_alternative"]["offer_id"], "nz-100")
        self.assertEqual(result["regional_alternative"]["landed_premium_nzd"], 25.0)

    def test_first_party_retailer_has_no_marketplace_seller_penalty(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "same-product",
                    "name": "Same exact product",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [
                self.offer("direct", "same-product", merchant_type="first_party"),
                self.offer("marketplace", "same-product", merchant_type="third_party"),
            ],
        }

        result = self.run_ranker(comparison)
        offers = {offer["offer_id"]: offer for offer in result["offers"]}
        self.assertEqual(offers["direct"]["seller_factor"], 1.0)
        self.assertLess(offers["marketplace"]["seller_factor"], 1.0)
        self.assertLess(offers["direct"]["decision_cost"], offers["marketplace"]["decision_cost"])

    def test_unknown_shipping_produces_a_break_even_not_a_false_winner(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "same-product",
                    "name": "Same exact product",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [
                self.offer("known-delivered", "same-product", price=20),
                self.offer("unknown-freight", "same-product", price=10, shipping=None),
            ],
        }

        result = self.run_ranker(comparison)
        offers = {offer["offer_id"]: offer for offer in result["offers"]}
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["winner"], "known-delivered")
        self.assertIsNone(result["raw_landed_winner"])
        self.assertEqual(result["raw_landed_status"], "incomplete")
        self.assertEqual(result["raw_landed_leader"], "known-delivered")
        self.assertEqual(result["raw_landed_contenders"], ["unknown-freight"])
        self.assertIsNone(offers["unknown-freight"]["landed_cost_high_nzd"])
        self.assertAlmostEqual(
            offers["unknown-freight"]["unknown_charge_break_even_nzd"], 10.0
        )

    def test_bounded_cost_uses_a_conservative_headline_without_inventing_a_midpoint(self) -> None:
        offer = self.offer("bounded-shipping", "bounded-product", price=10)
        offer["cost"]["components"]["shipping"] = {
            "state": "ambiguous",
            "lower_amount": 5,
            "upper_amount": 15,
        }
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
                "observed_at": "2026-08-27T12:00:00+12:00",
            },
            "products": [self.rated_product("bounded-product", 4.8, 50)],
            "offers": [offer],
        }

        result = self.run_ranker(comparison)
        scored = result["offers"][0]
        self.assertEqual(scored["landed_cost_low_nzd"], 15.0)
        self.assertEqual(scored["landed_cost_high_nzd"], 25.0)
        self.assertNotIn("landed_cost_nzd", scored)
        self.assertEqual(scored["decision_cost"], scored["decision_cost_worst"])
        self.assertGreater(scored["decision_cost"], scored["decision_cost_best"])
        completed = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-", "--format", "markdown"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("landed range NZ$15.00-NZ$25.00", completed.stdout)
        self.assertNotIn("break-even NZ$unknown", completed.stdout)

    def test_exact_offer_tie_is_explicitly_provisional(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
                "observed_at": "2026-08-27T12:00:00+12:00",
            },
            "products": [self.rated_product("same-product", 4.8, 50)],
            "offers": [
                self.offer("offer-a", "same-product", price=10),
                self.offer("offer-b", "same-product", price=10),
            ],
        }

        result = self.run_ranker(comparison)
        self.assertEqual(result["winner"], "offer-a")
        self.assertEqual(result["status"], "provisional")

    def test_duplicate_product_and_offer_ids_are_rejected(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                self.rated_product("duplicate", 4.8, 50),
                self.rated_product("duplicate", 4.6, 20),
            ],
            "offers": [self.offer("offer", "duplicate")],
        }
        product_result = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(product_result.returncode, 0)
        self.assertIn("product duplicate is duplicated", product_result.stderr)

        comparison["products"] = [self.rated_product("duplicate", 4.8, 50)]
        comparison["offers"].append(self.offer("offer", "duplicate"))
        offer_result = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(offer_result.returncode, 0)
        self.assertIn("offer offer is duplicated", offer_result.stderr)

    def test_invalid_policy_ranges_are_rejected_before_scoring(self) -> None:
        comparison = json.loads(
            (RANKER.parent / "input-template.json").read_text(encoding="utf-8")
        )
        default_policy = json.loads(
            (RANKER.parent / "default-policy.json").read_text(encoding="utf-8")
        )
        cases = [
            (
                "inverted-interval",
                {"credible_interval": {"lower": 0.9, "upper": 0.1}},
                "policy.credible_interval.lower must be less than upper",
            ),
            (
                "zero-prior",
                {"product_prior": {"alpha": 0}},
                "policy.product_prior.alpha must be positive",
            ),
            (
                "null-prior-key",
                {"product_prior": {"beta": None}},
                "policy.product_prior.beta must be a number",
            ),
            (
                "zero-region",
                {"region_multiplier": {"NZ": 0}},
                "policy.region_multiplier.NZ must be positive",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for name, changes, expected in cases:
                with self.subTest(name=name):
                    policy = json.loads(json.dumps(default_policy))
                    for section, values in changes.items():
                        policy[section].update(values)
                    policy_path = Path(directory) / f"{name}.json"
                    policy_path.write_text(json.dumps(policy), encoding="utf-8")
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(RANKER),
                            "--input",
                            "-",
                            "--policy",
                            str(policy_path),
                        ],
                        input=json.dumps(comparison),
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn(expected, completed.stderr)

    def test_all_unbounded_offers_have_unknown_break_evens(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
                "observed_at": "2026-08-27T12:00:00+12:00",
            },
            "products": [self.rated_product("same-product", 4.8, 50)],
            "offers": [
                self.offer("unknown-a", "same-product", price=10, shipping=None),
                self.offer("unknown-b", "same-product", price=12, shipping=None),
            ],
        }

        result = self.run_ranker(comparison)
        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(
            all(
                offer["unknown_charge_break_even_nzd"] is None
                for offer in result["offers"]
            )
        )

    def test_star_histograms_are_used_and_syndicated_corpora_are_counted_once(self) -> None:
        histogram = {"1": 1, "2": 1, "3": 2, "4": 4, "5": 7}
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "syndicated-product",
                    "name": "Syndicated product",
                    "hard_fit": True,
                    "review_sources": [
                        {
                            "id": "retailer-a",
                            "corpus_id": "bazaarvoice-123",
                            "identity_match": "exact",
                            "rating": {
                                "scale_min": 1,
                                "scale_max": 5,
                                "histogram": histogram,
                            },
                        },
                        {
                            "id": "retailer-b-syndicated-copy",
                            "corpus_id": "bazaarvoice-123",
                            "identity_match": "exact",
                            "rating": {
                                "scale_min": 1,
                                "scale_max": 5,
                                "histogram": histogram,
                            },
                        },
                    ],
                }
            ],
            "offers": [self.offer("direct", "syndicated-product")],
        }

        result = self.run_ranker(comparison)
        product = result["products"][0]
        self.assertEqual(product["review_count_used"], 15)
        self.assertAlmostEqual(product["low_star_share"], 2 / 15)
        self.assertEqual(product["deduplicated_source_ids"], ["retailer-b-syndicated-copy"])

    def test_hard_fit_failure_is_excluded_before_ranking(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "same-product",
                    "name": "Same product family",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [
                self.offer("valid", "same-product", price=10),
                {
                    **self.offer("wrong-voltage", "same-product", price=1),
                    "hard_fit": False,
                    "hard_fit_reason": "Wrong voltage for New Zealand",
                },
            ],
        }

        result = self.run_ranker(comparison)
        self.assertEqual(result["winner"], "valid")
        self.assertNotIn("wrong-voltage", {offer["offer_id"] for offer in result["offers"]})
        self.assertEqual(
            result["excluded"],
            [{"offer_id": "wrong-voltage", "reason": "Wrong voltage for New Zealand"}],
        )

    def test_cleat_evidence_and_purchase_ranks_are_separate(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 4,
                "quantity_unit": "cleat",
            },
            "products": [
                self.rated_product("clear", 5.0, 6),
                self.rated_product("metal", 4.7, 15),
            ],
            "offers": [
                {
                    **self.offer("clear-12", "clear", price=7.07, sold_count=60),
                    "pack_quantity": 12,
                },
                {
                    **self.offer("metal-4", "metal", price=9.30, sold_count=162),
                    "pack_quantity": 4,
                },
            ],
        }

        result = self.run_ranker(comparison)
        quality = {product["product_id"]: product for product in result["products"]}
        self.assertGreater(quality["metal"]["product_factor"], quality["clear"]["product_factor"])
        self.assertEqual(
            [item["product_id"] for item in result["product_quality_ranking"]],
            ["metal", "clear"],
        )
        self.assertEqual(result["winner"], "clear-12")
        self.assertEqual(
            {product["product_id"]: product["review_count_used"] for product in result["products"]},
            {"clear": 6, "metal": 15},
        )

    def test_unwanted_surplus_does_not_manufacture_value(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "same-product",
                    "name": "Same product",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [
                self.offer("one-for-three", "same-product", price=3),
                {
                    **self.offer("hundred-for-fifty", "same-product", price=50),
                    "pack_quantity": 100,
                },
            ],
        }

        result = self.run_ranker(comparison)
        offers = {offer["offer_id"]: offer for offer in result["offers"]}
        self.assertEqual(result["winner"], "one-for-three")
        self.assertEqual(offers["hundred-for-fifty"]["surplus_quantity"], 99)
        self.assertEqual(offers["hundred-for-fifty"]["useful_quantity"], 1)

    def test_probable_cross_site_identity_is_cited_but_not_pooled(self) -> None:
        product = self.rated_product("model-a", 4.5, 10)
        product["review_sources"].append(
            {
                "id": "lookalike-model-b",
                "corpus_id": "model-b-native",
                "identity_match": "probable",
                "rating": {
                    "mean": 5.0,
                    "scale_min": 1,
                    "scale_max": 5,
                    "count": 10000,
                },
            }
        )
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [product],
            "offers": [self.offer("model-a-offer", "model-a")],
        }

        result = self.run_ranker(comparison)
        scored = result["products"][0]
        self.assertEqual(scored["review_count_used"], 10)
        self.assertEqual(scored["excluded_source_ids"], ["lookalike-model-b"])

    def test_overlapping_product_intervals_make_the_winner_provisional(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                self.rated_product("model-a", 4.6, 5),
                self.rated_product("model-b", 4.7, 5),
            ],
            "offers": [
                self.offer("model-a-offer", "model-a", price=10),
                self.offer("model-b-offer", "model-b", price=10),
            ],
        }

        result = self.run_ranker(comparison)
        self.assertEqual(result["status"], "provisional")

    def test_foreign_currency_requires_an_explicit_rate_source_and_date(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "product",
                    "name": "Product",
                    "hard_fit": True,
                    "review_sources": [],
                }
            ],
            "offers": [self.offer("aud-offer", "product")],
        }
        cost = comparison["offers"][0]["cost"]
        cost["currency"] = "AUD"
        cost["fx_to_nzd"] = 1.1
        completed = subprocess.run(
            [sys.executable, str(RANKER), "--input", "-", "--format", "json"],
            input=json.dumps(comparison),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("fx_source", completed.stderr)

        cost["fx_source"] = "Reserve Bank reference rate"
        cost["fx_as_of"] = "2026-08-27"
        self.assertEqual(self.run_ranker(comparison)["winner"], "aud-offer")

    def test_sold_counts_and_irrelevant_candidates_do_not_rescale_scores(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                self.rated_product("model-a", 4.8, 50),
                self.rated_product("model-b", 4.6, 50),
            ],
            "offers": [
                self.offer("offer-a", "model-a", price=20, sold_count=1),
                self.offer("offer-b", "model-b", price=18, sold_count=1000),
            ],
        }
        baseline = self.run_ranker(comparison)

        expanded = json.loads(json.dumps(comparison))
        expanded["offers"][0]["sold_count"] = 999999
        expanded["products"].append(self.rated_product("irrelevant", 1.0, 1))
        expanded["offers"].append(self.offer("irrelevant-offer", "irrelevant", price=1000))
        reranked = self.run_ranker(expanded)

        baseline_scores = {
            offer["offer_id"]: offer["decision_cost"] for offer in baseline["offers"]
        }
        reranked_scores = {
            offer["offer_id"]: offer["decision_cost"] for offer in reranked["offers"]
        }
        self.assertEqual(reranked_scores["offer-a"], baseline_scores["offer-a"])
        self.assertEqual(reranked_scores["offer-b"], baseline_scores["offer-b"])

    def test_missing_identity_and_provenance_are_explicitly_incomplete(self) -> None:
        comparison = {
            "comparison": {
                "destination": "NZ",
                "needed_quantity": 1,
                "quantity_unit": "item",
            },
            "products": [
                {
                    "id": "under-specified",
                    "name": "Under-specified product",
                    "hard_fit": True,
                    "review_sources": [
                        {
                            "id": "untraceable-reviews",
                            "corpus_id": "untraceable",
                            "identity_match": "exact",
                            "rating": {
                                "mean": 4.9,
                                "scale_min": 1,
                                "scale_max": 5,
                                "count": 100,
                            },
                        }
                    ],
                }
            ],
            "offers": [
                {
                    **self.offer("under-specified-offer", "under-specified"),
                    "url": None,
                    "retailer": None,
                    "fulfilment_origin": None,
                    "selected_variant": None,
                }
            ],
        }

        result = self.run_ranker(comparison)
        self.assertEqual(result["status"], "incomplete")
        warning_paths = {warning["path"] for warning in result["provenance_warnings"]}
        self.assertIn("products.under-specified.identity", warning_paths)
        self.assertIn(
            "products.under-specified.review_sources.untraceable-reviews.url_or_source_ref",
            warning_paths,
        )
        self.assertIn("offers.under-specified-offer.retailer", warning_paths)

    @staticmethod
    def rated_product(product_id: str, mean: float, count: int) -> dict:
        return {
            "id": product_id,
            "name": product_id,
            "identity": {
                "confidence": "exact",
                "brand": "Example",
                "mpn": product_id,
                "variant": "standard",
            },
            "hard_fit": True,
            "review_sources": [
                {
                    "id": f"{product_id}-reviews",
                    "corpus_id": f"{product_id}-native",
                    "identity_match": "exact",
                    "url": f"https://example.nz/{product_id}",
                    "observed_at": "2026-08-27T12:00:00+12:00",
                    "rating": {
                        "mean": mean,
                        "scale_min": 1,
                        "scale_max": 5,
                        "count": count,
                    },
                }
            ],
        }

    @staticmethod
    def offer(
        offer_id: str,
        product_id: str,
        sold_count: int | None = None,
        price: float = 10,
        region: str = "NZ",
        merchant_type: str = "first_party",
        shipping: float | None = 0,
    ) -> dict:
        return {
            "id": offer_id,
            "product_id": product_id,
            "retailer": "Example",
            "url": f"https://example.nz/{offer_id}",
            "merchant_type": merchant_type,
            "region": region,
            "fulfilment_origin": region,
            "selected_variant": "standard",
            "hard_fit": True,
            "pack_quantity": 1,
            "packs_purchased": 1,
            "sold_count": sold_count,
            "cost": {
                "currency": "NZD",
                "fx_to_nzd": 1,
                "components": {
                    "item": {"state": "observed", "amount": price},
                    "shipping": (
                        {"state": "unavailable"}
                        if shipping is None
                        else {"state": "observed", "amount": shipping}
                    ),
                    "tax": {"state": "not_applicable"},
                    "mandatory_fees": {"state": "not_applicable"},
                    "eligible_discount": {"state": "not_applicable"},
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
