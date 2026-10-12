<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Arabic + English Keyword Research"
description: "Keyword map for one category or product type in Arabic and English, for a Saudi store"
tags:
  - prompts
  - find
---

# Arabic + English Keyword Research

## Use This When

You need the keywords for one category or product type on officehub.sa (for example
office chairs) before writing or rewriting its pages. Run once per category.

## Inputs

- Category or product type, in Arabic and English.
- The store's current URL for it (if any) and its current title and H1.
- `references/officehub-profile.md` (cities, delivery, B2B/B2C mix).
- Optional: Search Console query export, customer WhatsApp/phone questions.

## Prompt

```text
Build a keyword map for the category [CATEGORY AR / CATEGORY EN] on officehub.sa, a
Saudi office-furniture store. Follow references/saudi-market.md §2.

1. Seed: list 10–15 Arabic and 10–15 English seed phrases buyers in Saudi Arabia would
   type, including singular/plural, with/without ال, Gulf vs MSA words, and
   Arabic-English mixes.
2. Expand with web search (Saudi results): autocomplete, related searches and
   "People also ask", in both languages. Note Noon/Amazon.sa naming.
3. Group variants of the same intent into one keyword cluster. Name each cluster by the
   form most top-10 titles use.
4. For each cluster give: intent (buy / compare / learn / local), the page type that
   wins on Google (category, product, guide), the stores that rank, and whether
   Shopping units or ads appear.
5. Map each cluster to one officehub.sa URL (existing or new). Flag clusters two pages
   compete for.
6. Do not give search volumes. Rank clusters by SERP evidence of commercial value and by
   fit with what the store sells. Mark anything inferred as an assumption.

Return: a table (cluster AR | cluster EN | intent | winning page type | target URL |
priority), the top 5 to act on first, and the questions to answer on the page.
```

## Output

- Keyword cluster table in both languages.
- Target URL per cluster, with cannibalization flags.
- Top 5 priorities and the buyer questions for each page.

## See Also

- [Prompt Library](../README.md)
- `workflows/seo-cluster/WORKFLOW.md` for SERP-overlap clustering
- `workflows/seo-content-brief/references/keyword-density.md` (Arabic rules)
