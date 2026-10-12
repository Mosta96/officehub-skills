<!-- Source: OfficeHub edition, written for this repo (not part of the upstream FLOW library) -->
---
title: "Google Business Profile Setup and Review (Saudi)"
description: "Categories, services, description and posts for a Saudi office-furniture business"
tags:
  - prompts
  - local
---

# Google Business Profile Setup and Review (Saudi)

## Use This When

OfficeHub has (or is creating) a Google Business Profile for a showroom or warehouse that
customers can visit.

## Inputs

- Current GBP data, or the planned name, address, phone, hours and website URL.
- `references/officehub-profile.md` (NAP, cities, categories sold, delivery, installation).
- 3 competing profiles that appear in the map pack for "أثاث مكتبي [city]" and
  "office furniture [city]".

## Prompt

```text
Review or draft the Google Business Profile for OfficeHub [BRANCH/CITY].

1. Categories: one primary category and up to 9 secondary categories that match what
   this location really sells (e.g. "Office furniture store"). Compare with the 3
   competing profiles. Do not add categories for products the branch does not sell.
2. NAP: check name, National Address and phone match the website footer and the
   FurnitureStore schema character for character. Name = real business name, no
   keywords stuffed in.
3. Services/products: list the main categories with a short Arabic description and,
   where the store publishes them, a price "from X SAR".
4. Description (≤ 750 characters), Arabic first, plus an English version: what the
   branch sells, who for (companies and home offices), delivery and installation
   area, warranty. No URLs, no promotions, no ALL CAPS.
5. Attributes and links: website (the city/branch landing page or home), WhatsApp,
   appointment/quote link if available.
6. Photos to add: exterior, interior, showroom zones, team installing at a client office.
7. A 4-week post plan (offers, new arrivals, installation projects), Arabic.
8. A review request message (Arabic and English) for B2B clients after installation.

Flag anything that would break Google's guidelines (keywords in name, virtual office,
fake reviews) as Critical.
```

## Output

- Category set, NAP check, services, description in both languages.
- Photo list, post plan, review request message.

## See Also

- [Prompt Library](../README.md)
- `workflows/seo-local/WORKFLOW.md`, `references/saudi-market.md` §5
