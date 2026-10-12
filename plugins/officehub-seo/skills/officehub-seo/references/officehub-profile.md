# OfficeHub business profile

Load this before any workflow that analyzes or writes for officehub.sa. It replaces
industry detection and the "who is this for" questions. Treat every value here as a
default the user can override in the chat.

**Rules for blanks:** a field marked `TODO` is unknown. Ask the user for it once, in one
short message together with any other blanks the current workflow needs. Never invent a
value (address, phone, CR or VAT number, competitor, price) to fill a `TODO`. When the user
answers, tell them to add the value to this file so the next run has it.

## Business

| Field | Value |
|---|---|
| Brand (Arabic) | TODO (e.g. أوفيس هب) |
| Brand (English) | OfficeHub |
| Domain | https://officehub.sa (check it resolves before auditing; it did not on 2026-10-12) |
| Business type | E-commerce: office furniture. Possibly a showroom too (TODO: yes/no, cities) |
| Customers | B2B (companies, government, fit-out contractors) and B2C (home office). TODO: split |
| Market | Saudi Arabia only. TODO: ship to other GCC countries? |
| Cities served / delivery | TODO (e.g. Riyadh, Jeddah, Dammam with free delivery; rest of KSA paid) |
| Installation / assembly | TODO (free? which cities?) |
| Platform | Shopify or WooCommerce. TODO: which one. See `references/platform-notes.md` |

## Languages and URLs

| Field | Value |
|---|---|
| Primary language | Arabic (`ar`, RTL) |
| Second language | English (`en`) |
| URL pattern | TODO (e.g. `/` = Arabic and `/en/` = English, or `/ar/` + `/en/`) |
| hreflang | `ar` (or `ar-SA`), `en` (or `en-SA`), `x-default` → Arabic home. See `workflows/seo-hreflang/WORKFLOW.md` |

## Catalogue

Main categories (TODO: confirm and add the store's real category names in both languages):

| Category (EN) | Category (AR) |
|---|---|
| Office chairs | كراسي مكتبية |
| Executive desks | مكاتب مدراء |
| Staff desks / workstations | مكاتب موظفين / محطات عمل |
| Height-adjustable desks | مكاتب كهربائية قابلة لتعديل الارتفاع |
| Meeting tables | طاولات اجتماعات |
| Storage: pedestals, filing cabinets, lockers | خزائن ملفات / أدراج / لوكرات |
| Reception desks | مكاتب استقبال |
| Office sofas and waiting chairs | كنب مكتبي / كراسي انتظار |
| Acoustic pods / partitions | TODO |

Price range: TODO. Top brands carried: TODO. Own brand or reseller: TODO.

## Trust and NAP (must match Google Business Profile exactly)

| Field | Value |
|---|---|
| Legal name | TODO |
| Commercial Registration (CR) | TODO |
| VAT number (15 digits) | TODO |
| Phone | TODO (format `+966 11 XXX XXXX` or unified `9200 XXXXX`) |
| WhatsApp | TODO |
| Address (National Address) | TODO (building no., street, district, city, postal code, additional no.) |
| Opening hours | TODO |
| Google Business Profile URL | TODO |
| Social profiles | TODO (Instagram, X, Snapchat, TikTok, LinkedIn) |

## Competitors

TODO: list 3–5 Saudi office-furniture stores you lose sales to, with domains. Until then,
find competitors per query with web search on google.com.sa and say they were found that way.

Name clash: "Office Hub" (office-hub.com/sa) is a coworking marketplace that ranks in Saudi
Arabia for "office hub". Branded queries need the Arabic brand name and a clear category
word ("OfficeHub office furniture" / "أوفيس هب أثاث مكتبي"). Watch it in brand-SERP checks.

## Brand voice

TODO. Defaults until set:
- Arabic: clear Modern Standard Arabic, short sentences, no heavy marketing clichés (see the
  Arabic phrase lists in `scripts/content_quality.py`). Gulf terms are fine where buyers use
  them (e.g. "كنب").
- English: plain, practical, metric units (cm, kg).
- Prices always in SAR (ريال), VAT-inclusive, with the VAT note shown.

## Product images

| Field | Value |
|---|---|
| Product grid aspect ratio | 1:1 (TODO: confirm the theme's ratio) |
| Size | 2048 × 2048 px master, WebP for the site |
| Background | Pure white for the main image |
| AI-generated angles | Allowed, labelled with IPTC `trainedAlgorithmicMedia` (see `workflows/seo-images/WORKFLOW.md`) |
