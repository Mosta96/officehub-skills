<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Category Page Rewrite (Arabic + English)"
description: "Make a category/collection page the ranking page for its keyword cluster"
tags:
  - prompts
  - optimize
---

# Category Page Rewrite (Arabic + English)

## Use This When

A category or collection page (e.g. office chairs) is the page that should rank for a
head keyword, but it is only a product grid, or a product or blog page outranks it.

## Inputs

- Category URL (Arabic and English) and its current title, H1, intro text and filters.
- Keyword cluster for the category (from `find/keyword-research-ar-en.md`).
- Subcategories, top products, price range in SAR, delivery and installation terms.

## Prompt

```text
Improve the category page [CATEGORY] on officehub.sa so it can rank for [MAIN KEYWORD AR]
and [MAIN KEYWORD EN]. Keep the product grid first on mobile. Text goes above (short)
and below (longer) the grid.

Return, per language:
1. Title tag (≤ 60 characters) and meta description (≤ 155 characters).
2. H1 (the plural form the SERP prefers, e.g. "كراسي مكتبية").
3. Intro above the grid: 40–60 words, what the range covers, price range in SAR,
   delivery/installation promise.
4. Subcategory links with descriptive anchors (e.g. "كراسي مكتب طبية", "كراسي مدراء").
5. Below-grid guide: 250–400 words (Arabic ~20% fewer) that answers how to choose, with
   a comparison table of the subcategories.
6. 3–5 buyer questions with short answers.
7. Filter and URL advice: which filters deserve an indexable page (real search demand),
   which must be noindex or canonical to the category (see references/platform-notes.md).
8. Internal links to add from the homepage, guides and related categories.

Flag cannibalization: other officehub.sa pages that target the same cluster, and what
to do with each (merge, re-target, link).
```

## Output

- Category copy blocks in both languages.
- Filter indexation rules and internal link plan.
- Cannibalization actions.

## See Also

- [Prompt Library](../README.md)
- `references/platform-notes.md`
