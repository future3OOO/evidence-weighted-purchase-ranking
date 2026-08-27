# AliExpress via Parse.bot

Use `scripts/aliexpress.py` once per comparison. Its single search response is the complete AliExpress evidence set for that run.

## Command

```text
python scripts/aliexpress.py search "curtain cleat hook" --request-marker comparison.aliexpress-request --sort-by best_match
```

The marker blocks concurrent calls and remains after a successful response; provider failures release it. Do not retry automatically, paginate, wait for rate limits, change the query, or call details/reviews. `PARSE_API_KEY`, `--api-key`, and `--base-url` retain their existing overrides.

## Single-response contract

Select five matching products from the response. The search scraper should return:

| Evidence | Required treatment |
| --- | --- |
| Product | Exact variant, pack quantity, rating, actual review count, and URL. |
| Offer | Item price and currency; output exactly as returned. |
| Seller | Seller rating and feedback count; keep separate from product evidence. |

Set every AliExpress shipping component to observed zero. Describe the result as **normalized comparison cost**, not actual landed cost. Normalize this response and run `rank.py` immediately. Missing review counts stay missing: return the ranker's incomplete/unranked result and never substitute a practical pick.
