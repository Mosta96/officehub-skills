<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Buying Guide Brief (Arabic first)"
description: "Brief for an informational buying guide that feeds a category page"
tags:
  - prompts
  - find
---

# Buying Guide Brief (Arabic first)

## Use This When

A "learn" cluster from the keyword map ("كيف أختار كرسي مكتب", "مقاس مكتب الموظف
المناسب", "best standing desk height") deserves a guide that links to a category page.

## Inputs

- The guide's main question in Arabic (and English if an English version is planned).
- The category page it supports and 3–6 products to feature.
- Real product data: dimensions, materials, mechanisms, warranty, prices in SAR.
- Optional: questions customers ask on WhatsApp or by phone.

## Prompt

```text
Write a content brief for an Arabic buying guide on officehub.sa answering:
[MAIN QUESTION AR]. It must send readers to [CATEGORY URL].

1. Check the current Saudi SERP for the question (Arabic). List what the top 5 results
   cover and what they miss.
2. Outline: H1 in Arabic, 5–8 H2s that each answer one buyer decision (size, posture,
   materials, budget in SAR, use case: home office vs company), and a short spec
   checklist table.
3. For each section, name the product data or office-furniture expertise that proves
   the point (measurements, tests, installation experience). No generic claims.
4. Place 3–6 product links and one category link where they answer a decision, not in a
   block at the end.
5. Add a short Arabic Q&A section with real buyer questions (no FAQPage schema for
   rich results; see SKILL.md quality gates).
6. Give a title (≤ 60 characters) and meta description (≤ 155 characters) in Arabic.
7. If an English version is planned, list the English keyword to use. Do not translate
   the Arabic title word for word.

Return the brief as a working document. Flag every fact the store must confirm.
```

## Output

- Arabic outline with section goals and required proof.
- Internal link plan to products and the category page.
- Title and meta description; English keyword if needed.

## See Also

- [Prompt Library](../README.md)
- `workflows/seo-content-brief/WORKFLOW.md`
