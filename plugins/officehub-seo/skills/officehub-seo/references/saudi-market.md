# Saudi market and Arabic SEO layer

Load this with `references/officehub-profile.md` for any officehub.sa work. It overrides
the US/English defaults in the workflows: where a workflow names Yelp, BBB, USD, US
holidays or English-only rules, use the Saudi equivalent below.

Facts that change (programmes, dates, platform names) are marked **verify**: confirm them
with a web search before putting them in a deliverable.

## 1. Search landscape

- Google is the main search engine. Run SERP checks as google.com.sa, Arabic interface,
  location Saudi Arabia. Results differ from google.com in English.
- Buyers search in Arabic, in English and in mixed form ("كرسي gaming", "office chair
  riyadh"). Research each language separately (see §2).
- Most traffic is mobile. Check the mobile page first, in RTL.
- Product discovery also happens on Instagram, Snapchat, TikTok and YouTube. Social
  profiles belong in `sameAs` and in GBP.
- B2B buyers (companies, government, fit-out contractors) search for quotes, bulk
  pricing, delivery to site and tax invoices more than for single items.

## 2. Arabic keyword research (free method)

1. **Seed list** from the store's categories in both languages
   (`references/officehub-profile.md`).
2. **Expand** with Google autocomplete and "People also ask" / related searches in
   Arabic. Also use Noon and Amazon.sa search suggestions as a product-naming check, and
   Google Trends (region: Saudi Arabia) to compare variants.
3. **Group variants into one keyword** before counting or clustering:

   | Variant type | Example |
   |---|---|
   | Singular / plural | كرسي مكتب · كراسي مكاتب · كراسي مكتبية |
   | With and without ال | المكاتب الخشبية · مكاتب خشبية |
   | Spelling | طاولة / طاوله · أثاث / اثاث · مكتبي / مكتبى |
   | MSA vs Gulf word | أريكة / كنب · خزانة / دولاب |
   | Arabic vs English | كرسي طبي · ergonomic chair |
   | Modifiers | رخيص · بالرياض · للموظفين · مع توصيل وتركيب |

4. **Pick the page's main form from the SERP:** the form most top results use in their
   titles. Category pages usually win on the plural ("كراسي مكتبية"), product pages on a
   specific singular ("كرسي مكتب شبكي بمسند رأس").
5. **City modifiers** ("الرياض", "جدة", "الدمام") only get a page when the store really
   serves that city differently (stock, delivery time, showroom, installation). Otherwise
   mention cities on the delivery page and in GBP, not in thin city pages.
6. **Mark search volume "not verified".** Without a keyword tool there are no reliable
   Arabic volumes. Rank by SERP evidence (ads, shopping units, number of shop results)
   and by what customers ask on WhatsApp and phone.

## 3. Seasonality (plan content 6–8 weeks ahead)

| Moment | When | Angle |
|---|---|---|
| Founding Day (يوم التأسيس) | 22 February | Offers, national-theme campaigns |
| Ramadan and Eid al-Fitr | Moves ~11 days earlier each year (Hijri). **Verify** dates | Evening shopping peak, gifting, offers before Eid |
| Eid al-Adha | Hijri. **Verify** dates | Offers; delivery cut-off notices |
| Back to work after summer | Late August–September | Home office, office refresh |
| National Day (اليوم الوطني) | 23 September | Biggest national sale moment |
| November sales (White/Black Friday) | November | Price-led category pages, bundles |
| Year-end budgets / new offices | Q4 and Q1 | B2B: fit-out bundles, quotes, bulk pricing |

The weekend is Friday–Saturday; the working week is Sunday–Thursday. Use this for opening
hours, B2B follow-ups and posting times.

## 4. Trust and conversion signals (check on every audit)

Show these on product pages and in the footer, in Arabic and English:
- Price in SAR, VAT-inclusive, with "شامل ضريبة القيمة المضافة" next to it.
- VAT number and Commercial Registration (CR) number, legal name, National Address.
  Saudi rules require online stores to identify the seller. Buyers and B2B procurement
  check these.
- Store verification badge, if available. Maroof was replaced by a Saudi Business Center
  service. **Verify** the current programme before recommending.
- Payment methods: mada, Apple Pay, Visa/Mastercard, and instalments (Tabby, Tamara) if
  offered. **Verify** which ones the store offers.
- Delivery: cities, time in working days, cost, and whether **installation/assembly** is
  included. For office furniture this is a deciding factor.
- Warranty (years, what it covers), return and exchange policy in Arabic.
- WhatsApp click-to-chat and phone in `+966` format. For B2B: a "request a quote" form,
  tax-invoice note, bulk/project pricing, and project references (logos and photos of
  real offices fitted).
- Arabic reviews on product pages and on Google Maps.

## 5. Local SEO (replaces the US citation lists)

- **Core profiles:** Google Business Profile (category e.g. "Office furniture store"),
  Apple Business Connect, Bing Places. Skip Yelp, BBB, Nextdoor and US YellowPages: they
  carry little or no weight in Saudi Arabia.
- **NAP:** one Arabic version and one English version, each used the same way everywhere.
  Address in National Address order: building no., street, district, city, postal code,
  additional no. The short address code (4 letters + 4 digits) is optional extra.
- **Phone:** `+966 11 XXX XXXX` (Riyadh landline), `+966 5X XXX XXXX` (mobile), or a
  unified `9200XXXXX` number. Write it the same way in the site, schema and GBP.
- **Saudi directories:** find current ones with web search ("دليل الشركات السعودية",
  "دليل الأثاث المكتبي"). Keep only ones that are indexed, editable and free; check each with
  `site:` before listing it. Do not invent directory names.
- **Reviews:** ask B2B clients for Google reviews after installation. Reply in the
  reviewer's language.
- **Multiple cities:** one GBP per real address (showroom/warehouse open to customers),
  never for a city with only delivery.

## 6. E-commerce specifics

- **Benchmarks:** Noon and Amazon.sa product titles show how Saudi buyers name products.
  Compare competitor category pages on google.com.sa for structure and filters.
- **Google Merchant Center:** free listings and Shopping ads. **Verify** current Saudi
  availability and feed rules. The feed needs SAR prices including VAT, Arabic or English
  titles matching the landing page language, and GTIN where it exists.
- **Product data that wins for office furniture:** dimensions (W × D × H cm), seat height
  range, weight capacity, materials, mechanism type, warranty, assembly included, delivery
  time per city. Put it in a spec table in both languages.

## 7. Arabic technical checks

- `<html lang="ar" dir="rtl">` on Arabic pages, `lang="en" dir="ltr"` on English pages.
  Check that the mobile menu, breadcrumbs, sliders and price blocks mirror correctly.
- **Slugs:** pick one approach and keep it. Either short English/Latin slugs for both
  languages (clean when shared), or Arabic slugs (percent-encoded in links). Never change
  live URLs without 301 redirects.
- **Arabic web fonts** are large. Subset them, use `font-display: swap` and preload only
  the main weight. They often cause LCP and CLS problems.
- **Digits:** Western digits (0–9) are the norm in Saudi e-commerce. Use them the same way
  in prices, sizes and schema (schema values must be Western digits).
- **Structured data:** one language per page. Arabic text in the Arabic page's JSON-LD,
  English in the English page's. Use `inLanguage` on `WebPage`/`WebSite` (`ar-SA` / `en-SA`).
  Templates: `schema/templates.json` → "Product (Saudi store, OfficeHub)" and
  "FurnitureStore (Saudi showroom, OfficeHub)".

## 8. AI search (GEO) in Arabic

AI Overviews, ChatGPT, Gemini and Perplexity answer Arabic shopping questions. To be cited:
- Put specs in tables with units, and answer real buyer questions in short Arabic
  paragraphs ("ما الفرق بين الكرسي الطبي والكرسي العادي؟").
- Keep brand facts consistent across the site, GBP and social profiles (name, cities,
  delivery, warranty), so models get one story.
- Check visibility by asking the assistants the buyer's question in Arabic and in English.
  Record which stores are named.
