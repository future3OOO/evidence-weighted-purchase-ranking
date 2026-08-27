# New Zealand and Australian Purchase Policy

The policy is for a New Zealand operator. Apply it to offers, never to product quality.

## Discovery and qualification

Search in this order:

1. NZ businesses and qualifying NZ marketplace offers;
2. Australian retailers/offers that actually ship the selected order to New Zealand;
3. global marketplaces and other international retailers.

Always retain a credible NZ/AU option when one exists. `.co.nz`, an NZD display, or `ships from NZ` does not prove NZ business jurisdiction. Record merchant jurisdiction/type separately from fulfilment origin. For Trade Me-style offers, distinguish in-trade businesses from private sellers.

An AU offer is invalid if it is AU pickup-only or will not deliver the selected product to the NZ destination. Check plug/voltage compatibility, warranty geography, and return freight.

## Landed NZD cost

Use the order that meets required quantity:

```text
landed cost = item total + destination shipping + GST/tax/duty + mandatory fees - eligible discount
```

For non-NZD prices, FX is an explicit input with source and timestamp; the scorer never performs a live lookup. Resolve low-value GST collection and any higher-value Customs/duty process from current authoritative rules. Record card/payment FX fees when mandatory or material.

## Transparent preference hurdle

`default-policy.json` declares these operator preference/friction multipliers:

| Region | Multiplier | Practical implication versus identical NZ offer |
| --- | ---: | --- |
| NZ | 1.00 | baseline |
| AU | 1.10 | must be about 9.1% cheaper to offset the preference |
| International | 1.25 | must be more than 20% cheaper to offset the preference |

These are not predicted taxes or empirical failure probabilities. They make legal recourse, return friction, warranty geography, delivery uncertainty, and convenience preference visible. Override them only for an explicit user preference and disclose the custom policy.

When an international offer wins, report the best qualifying NZ/AU alternative, its landed-cost premium, and the practical protection/delivery/return differences. Also report the raw landed-cost winner so regional policy never hides the cheapest checkout price.
