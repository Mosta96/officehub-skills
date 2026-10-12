<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Product Page Rewrite (Arabic + English)"
description: "Rewrite one office-furniture product page so it ranks, gets cited and converts"
tags:
  - prompts
  - optimize
---

# Product Page Rewrite (Arabic + English)

## Use This When

A product page has manufacturer copy, thin text, a missing spec table, or ranks below
competitors with similar products.

## Inputs

- Product URL (Arabic and English versions) or pasted page text.
- Real product data: name, model, brand, dimensions (W × D × H cm), seat height range,
  weight capacity, materials, colours, mechanism, warranty, price in SAR (VAT incl.),
  delivery and installation terms.
- Target keyword cluster (from `find/keyword-research-ar-en.md`), if available.

## Prompt

```text
Rewrite the product page for [PRODUCT] on officehub.sa. Arabic page first, then the
English page. Use only the product data supplied; mark any missing fact as [CONFIRM].

For each language return:
1. Title tag (≤ 60 characters): product type + key differentiator + brand/OfficeHub.
2. Meta description (≤ 155 characters): benefit, price or delivery/installation promise,
   CTA.
3. H1: the product name buyers use (from the keyword cluster), not the internal code.
4. Opening 2–3 sentences: who it is for and the main reason to choose it.
5. Key benefits: 4–6 bullets, each tied to a spec (e.g. "مسند قطني قابل للتعديل لساعات
   العمل الطويلة").
6. Spec table: dimensions in cm, weight capacity, materials, mechanism, colours,
   warranty, assembly included, delivery time per city.
7. "Who it suits / not suits" in 2–3 lines (helps AI answers and reduces returns).
8. 3–5 short buyer questions with direct answers (delivery, installation, warranty,
   returns, bulk orders).
9. Image alt text for each image (product type + colour/angle), in that language.
10. Product schema fields to fill (template "Product (Saudi store, OfficeHub)" in
    schema/templates.json).

Rules: Modern Standard Arabic, short sentences, no clichés (see the Arabic phrase lists
in scripts/content_quality.py). Western digits. Prices in SAR with the VAT note. The
English page is written for English searchers, not translated word for word.
```

## Output

- Ready-to-paste Arabic and English page copy.
- Alt text per image and schema fields.
- List of [CONFIRM] facts for the team.

## See Also

- [Prompt Library](../README.md)
- `workflows/seo-ecommerce/WORKFLOW.md`
