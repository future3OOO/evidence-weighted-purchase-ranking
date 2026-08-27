# AliExpress via Parse.bot

Use `scripts/aliexpress.py` when direct AliExpress pages cannot be inspected. The script uses the Parse.bot AliExpress scraper, includes the approved free-plan key, and emits the provider JSON unchanged after validating a successful object response.

## Commands

```text
python scripts/aliexpress.py search "curtain cleat hook" --page 1 --sort-by best_match
python scripts/aliexpress.py details 3256808639899986
python scripts/aliexpress.py reviews 3256808639899986 --page 1 --limit 50
```

`PARSE_API_KEY` or `--api-key` overrides the bundled key. `--base-url` overrides the scraper endpoint. The free plan allows 200 credits per month and five requests per minute; search costs two credits and details or reviews costs one credit.

## Evidence mapping

Keep the returned populations separate:

| Endpoint field | Scope and treatment |
| --- | --- |
| `search_products.data.products[].product_id`, `title`, `product_url` | Listing identity; confirm the selected material/pack variant before pooling evidence. |
| `search_products.data.products[].price`, `original_price` | Output the prices exactly as returned. |
| `search_products.data.products[].rating` | Listing/product aggregate rating, not seller feedback. |
| `search_products.data.products[].orders_desc` | Listing sales maturity only; never use it as the review count or product quality. |
| `search_products.data.products[].seller_name` | Merchant identity when present. |
| `get_product_reviews.data.total_reviews` | Exact supporting review count when the review corpus and selected material variant pass the identity gate. |
| `get_product_reviews.data.average_rating` | Rating mean for that returned review corpus. Pair it with `total_reviews`. |
| `get_product_reviews.data.reviews[].sku_info` | Variant context for each review; use it to accept, split, or reject evidence for the selected variant. |
| `get_product_details` | Canonical title, URL, and images where returned. Other fields are conditional and must not be assumed. |

Treat absent fields as missing only from that response, not unsupported by the scraper. Assume AliExpress listings are NZ-delivery eligible; do not investigate or discuss delivery eligibility. Preserve undisclosed shipping or tax as missing or unavailable without further delivery research.
