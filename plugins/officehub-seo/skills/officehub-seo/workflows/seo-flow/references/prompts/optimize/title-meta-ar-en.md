<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Titles and Meta Descriptions in Bulk (Arabic + English)"
description: "Rewrite titles and meta descriptions for a list of URLs, CTR-focused"
tags:
  - prompts
  - optimize
---

# Titles and Meta Descriptions in Bulk (Arabic + English)

## Use This When

Search Console shows pages with impressions but a low click-through rate, or titles
are duplicated, truncated or in the wrong language.

## Inputs

- List of URLs with current title, meta description and page language.
- Optional: Search Console export (query, page, clicks, impressions, CTR, position).
- Main keyword per URL, if known.

## Prompt

```text
Rewrite titles and meta descriptions for these officehub.sa URLs. Write each in the
page's own language (Arabic pages in Arabic, English pages in English).

Rules:
- Title ≤ 60 characters: main keyword first, then a differentiator (price from X SAR,
  free installation, warranty years, delivery city), then "OfficeHub" / "أوفيس هب" only
  if space allows. No ALL CAPS, no keyword repetition.
- Meta description ≤ 155 characters: answer the searcher's need, one proof point, one
  CTA. Arabic: Modern Standard Arabic, Western digits.
- Every title on the site must be unique. Flag duplicates in the input.
- If Search Console data is given, prioritize pages ranking 3–15 with CTR below the
  site's median for that position, and use the top queries' wording.

Return a table: URL | language | current title | new title (chars) | current
description | new description (chars) | reason.
```

## Output

- Ready-to-paste table, with character counts.
- Priority order when Search Console data is supplied.

## See Also

- [Prompt Library](../README.md)
- `references/platform-notes.md` (where to edit titles on Shopify/WooCommerce)
