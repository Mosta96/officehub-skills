# OfficeHub business profile

Load this before any workflow that analyzes or writes for officehub.sa. It replaces
industry detection and the "who is this for" questions. Treat every value here as a
default the user can override in the chat.

**Rules for blanks:** a field marked `TODO` is unknown. Ask the user for it once, in one
short message together with any other blanks the current workflow needs. Never invent a
value (address, phone, CR or VAT number, competitor, price) to fill a `TODO`. When the user
answers, tell them to add the value to this file so the next run has it.

**Filled on 2026-10-12** from officehub.sa, the LinkedIn company page and the Instagram
profile. Source tags: [site] = officehub.sa, [li] = LinkedIn, [ig] = Instagram,
[owner] = needs owner confirmation.

## Business

| Field | Value |
|---|---|
| Brand (Arabic) | اوفيس هب [owner] |
| Brand (English) | OfficeHub (written "Office Hub" on the site, Instagram and LinkedIn; LinkedIn page name is "Office Hub by NMG"). Pick one spelling and use it everywhere |
| Domain | https://officehub.sa (resolves, checked 2026-10-11/12) |
| Business type | Office furniture: online store plus one showroom in Riyadh (Al Olaya) [site, li, ig]. Also B2B space planning, 2D/3D drawings, turnkey design and fit-out [site] |
| Customers | B2B (government agencies, corporates, interior/architecture offices) and B2C (individuals, home workers) [site, owner]. Both matter equally unless told otherwise |
| Market | Saudi Arabia only: the site says it delivers exclusively across KSA [site]. No GCC shipping |
| Cities served / delivery | All of KSA [site]. Standard delivery about 5 business days; special-order colours up to 3 months; same-day on request for an extra charge [site]. TODO: which cities get free delivery and the fee for the rest [owner]. Note: the shipping policy page has no cities or fees and still contains UAE wording; fix it |
| Installation / assembly | Offered as a service ("hassle-free installation") [site, li]. TODO: free or paid, which cities [owner] |
| Platform | Shopify (confirmed from `/products.json`). See `references/platform-notes.md` |

## Languages and URLs

| Field | Value |
|---|---|
| Primary language | English is the default at the root; Arabic (`ar`, RTL) is the second language. This differs from the earlier default (Arabic primary) [site] |
| Second language | Arabic (`ar`, RTL) at `/ar` |
| URL pattern | English at `/`, Arabic at `/ar/...` [site] |
| hreflang | `en`, `ar`, `x-default` → English home (as the site has it now) [site]. See `workflows/seo-hreflang/WORKFLOW.md`. Decide whether the market wants `x-default` on Arabic instead [owner] |

## Catalogue

Main categories as in the store navigation [site]:

| Category (EN) | Category (AR) |
|---|---|
| Sofas | مجموعات الصوفا |
| Armchairs | كراسي بذراعين |
| Cafeteria and lounge chairs | كراسي الكافيتيريا |
| Training chairs | كراسي تدريب |
| Task and visitor chairs | كرسي مكتب |
| Executive chairs | كرسي تنفيذي |
| Stools | مقعد |
| Executive desks | المكاتب التنفيذية |
| Manager desks | مكاتب إدارية |
| Workstations | محطات العمل |
| Meeting tables | طاولات الاجتماعات |
| Training tables | طاولات التدريب |
| Coffee and side tables | طاولات القهوة |
| Credenzas | كريدينزا |
| Pedestals / drawer cabinets | خزانة مكتب بأدراج |
| Filing cabinets | خزائن ملفات |
| Wall storage | التخزين الجداري |
| Privacy solutions (phone booths: 2 products) | حلول الخصوصية |
| Healthy workspace | مساحة العمل الصحية |
| Accessories | الإكسسوارات |
| Pre-Loved | كما هي |
| Sale | تخفيضات |

Not in the store today: reception desks, height-adjustable desks as a category, lockers [site]. Acoustic pods / partitions: only the "Privacy solutions" category with 2 phone booths [site].

Price range: SAR 160 to 55,600; median about SAR 3,200 (272 products) [site].
Top brands carried: mostly Italian designs by Claudio Bellini made by Kano [site]; Kano's logo appears on Instagram posts [ig].
Own brand or reseller: OfficeHub owns its brand [owner]; products are Italian designs by Claudio Bellini made by Kano [site]. The Shopify vendor field is "HANGZHOU KENUO IMPORT & EXPORT CO.,LTD" on 260 products, "Kano" on 5, "Office Hub" on 7; the site says it "integrates with" Kano but not who owns the brand.

## Trust and NAP (must match Google Business Profile exactly)

| Field | Value |
|---|---|
| Legal name | Office Hub is a company created by NMG [owner]. TODO: the full registered name as on the CR (the site shows the CR number but no name) |
| Commercial Registration (CR) | 4030299011 [site] |
| VAT number (15 digits) | 300917066200003 [site] |
| Phone | +966 11 279 0065 (shown as 00966112790065) [site] |
| WhatsApp | +966 11 279 0065 (same number, per the FAQ) [site] |
| Email | hello@officehub.sa [site, li] |
| Address (National Address) | 7204 King Fahd Rd, Al Olaya, Riyadh 12331 [site]. LinkedIn also lists "Arcade Center, King Fahad Road, Olaya District, Riyadh 12331" [li]. TODO: additional no. and the exact National Address wording [owner] |
| Opening hours | Sun–Thu 9 AM–9 PM; Fri closed; Sat 12 PM–9 PM [site FAQ] |
| Google Business Profile URL | https://maps.app.goo.gl/MYNSyrfW3PzCCKFx9 [owner]. The site links two different Maps short links (contact page KHwWEw4nzvgUfWnu8, FAQ mP8692H97s4yTdQo8); make them all point to this one. TODO: check the listing name and NAP match this file |
| Social profiles | Instagram https://www.instagram.com/officehub.ksa/ (verified, 13.6K followers) [ig]; LinkedIn https://www.linkedin.com/company/officehubsa (2,868 followers, 11–50 employees, founded 2023) [li]; Facebook https://www.facebook.com/officehubsa [site]; X https://twitter.com/OfficeHubsa [site]. No Snapchat or TikTok found |
| Payment / policies | Cash, Mada, Visa, Tabby, bank transfer. Refund within 7 days (uninstalled, original packaging); exchange within 14 days; special orders need 50% down payment; 5-year warranty on manufacturing defects [site] |

## Competitors

Named by the owner (B2B and B2C office-furniture sellers in KSA):
- LOFT, loftstore.com (English pages at /en) [owner]
- Alrugaib (الرقيب), alrugaibfurniture.com (domain seen in a web search; confirm)
- Others: TODO. Add 1–3 more with domains.

For any other query, find competitors with web search on google.com.sa and say they were found that way.

Name clash: "Office Hub" (office-hub.com/sa) is a coworking marketplace that ranks in Saudi
Arabia for "office hub". Branded queries need the Arabic brand name and a clear category
word ("OfficeHub office furniture" / "أوفيس هب أثاث مكتبي"). Watch it in brand-SERP checks.

## Brand voice

TODO [owner]. Observed: Instagram bio "Elevate your workspace. Big or small — we deliver it all. Shop in-store, online, or through our expert team." [ig]. Defaults until set:
- Arabic: clear Modern Standard Arabic, short sentences, no heavy marketing clichés (see the
  Arabic phrase lists in `scripts/content_quality.py`). Gulf terms are fine where buyers use
  them (e.g. "كنب").
- English: plain, practical, metric units (cm, kg).
- Prices always in SAR (ريال), VAT-inclusive, with the VAT note shown.

## Product images

| Field | Value |
|---|---|
| Product grid aspect ratio | 1:1 (master images on the store are 2048 × 2048) [site] |
| Size | 2048 × 2048 px master, WebP for the site |
| Background | Pure white for the main image |
| AI-generated angles | Allowed, labelled with IPTC `trainedAlgorithmicMedia` (see `workflows/seo-images/WORKFLOW.md`) |
