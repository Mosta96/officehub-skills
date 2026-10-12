# E-commerce SEO Analysis

> Chat edition: follow the "Chat adaptation rules" in the top-level SKILL.md for fetching, scripts, subagents, output files and API-keyed steps.

Product and category page optimization, Saudi market comparison and Product
schema for an online store. Everything here runs on free sources (web fetch, web
search, pasted exports). The upstream DataForSEO Merchant/Amazon modules were
removed from this edition.

For officehub.sa, load `references/officehub-profile.md`,
`references/saudi-market.md` and `references/platform-notes.md` first.

## Asks

| Ask | Purpose |
|-----|---------|
| ecommerce `<url>` | Full analysis of a product or category page, or the store |
| ecommerce market `<product or keyword>` | Saudi market comparison: who ranks and sells, at what price, with what content (section 2) |
| ecommerce schema `<url>` | Product schema validation and enhancement (section 5) |

---

## 1. Product Page Analysis

Fetch and parse any product page for on-page SEO quality.

### Workflow

```
1. python3 scripts/fetch_page.py <url> --output page.html --json --max-text 2000
   → saves the full HTML, prints status, headers and a JSON-LD summary
   (or use the user's pasted page source, per SKILL.md)
2. python3 scripts/parse_html.py page.html --url <url> --json → SEO elements
3. Analyze product-specific signals (below), in each language version
```

### Product SEO Checklist

#### Title Tag
- [ ] Contains primary product keyword
- [ ] Includes brand name
- [ ] Under 60 characters (no truncation in SERPs)
- [ ] Format: `[Product Name] - [Key Feature] | [Brand]`

#### Meta Description
- [ ] Contains product keyword + benefit
- [ ] Includes price ("from 1,150 SAR" / "ابتداءً من 1,150 ريال") when competitive
- [ ] Call-to-action present (اطلب الآن, free delivery and installation, WhatsApp)
- [ ] Under 155 characters

#### Heading Structure
- [ ] Single H1 matching primary product name
- [ ] H2s for: Features, Specifications, Reviews, Related Products
- [ ] No duplicate H1 tags across product variants

#### Product Images
- [ ] Alt text includes product name + distinguishing feature
- [ ] File names are descriptive (not `IMG_001.jpg`)
- [ ] WebP format served (with JPEG fallback)
- [ ] At least 3 images per product (hero, detail, lifestyle)
- [ ] High-resolution images: Google recommends at least 50K pixels (width x height) for merchant listings; larger (for example 800px+) is common practice, not a rule
- [ ] Lazy loading on below-fold images only

#### Internal Linking
- [ ] Breadcrumb navigation: Home > Category > Subcategory > Product
- [ ] Related products section (cross-sell / upsell)
- [ ] Link back to category page with keyword-rich anchor
- [ ] Reviews section links to full review page (if separate)

#### Content Quality
- [ ] Unique product description (not manufacturer copy-paste)
- [ ] Word count >= 200 for product description body (about 160 for Arabic, see `workflows/seo-content-brief/references/keyword-density.md`)
- [ ] Specs table present (not just prose): W × D × H cm, weight capacity, materials, mechanism, warranty
- [ ] User reviews on-page (UGC signals)

#### Saudi store signals (officehub.sa)
- [ ] Price in SAR, VAT-inclusive, with the VAT note
- [ ] Delivery cities and time, installation/assembly included or not
- [ ] Warranty and return policy linked from the product page
- [ ] WhatsApp / phone CTA; for B2B items, "request a quote" and bulk pricing
- [ ] Arabic and English versions both complete and linked (hreflang)

### Scoring

| Category | Weight | Criteria |
|----------|--------|----------|
| Schema completeness | 25% | Required + recommended Product fields |
| Title & meta | 15% | Keyword placement, length, format |
| Image optimization | 20% | Alt text, format, sizing, count |
| Content quality | 20% | Unique description, specs, reviews |
| Internal linking | 10% | Breadcrumbs, related products, categories |
| Technical | 10% | Page speed, mobile rendering, canonical |

---

## 2. Saudi Market Comparison (free)

Replaces upstream's paid Google Shopping, Amazon and keyword-gap modules. Use web
search (results for Saudi Arabia, Arabic and English) and web fetch. Mark every
number that came from a sample as "sampled", not as market data.

### Workflow

1. **Pick 3–5 money keywords** for the product or category, in Arabic and English
   (method: `references/saudi-market.md` §2).
2. **SERP snapshot** per keyword: which stores rank in the top 10, whether there are
   Shopping/product units, ads, maps, AI Overviews, and which page types win
   (category vs product vs blog).
3. **Competitor pages:** fetch the top 3 ranking store pages. Record title pattern,
   H1, price (SAR, VAT incl.?), delivery and installation promise, warranty, spec
   table, review count, image count, schema types (from the JSON-LD summary).
4. **Marketplaces:** search Noon and Amazon.sa for the same product type. Note the
   naming buyers see, price range and the attributes in titles (size, material,
   colour, "طبي"). Use them as benchmarks, not as competitors to copy.
5. **Merchant Center:** if the user can share a Merchant Center or Search Console
   export, analyze it. Otherwise list what the feed needs (SAR prices incl. VAT,
   GTIN where available, title in the landing page's language, `shipping` for SA).

### Analysis Outputs

#### Price position
- Sampled price range and median for the product type, in SAR
- Where officehub.sa sits; whether competitors show VAT-inclusive prices

#### Offer comparison
- Delivery time, free delivery threshold, installation, warranty, returns:
  officehub.sa vs each sampled competitor (table)

#### Content gaps
- Attributes and questions competitors answer that officehub.sa does not
- Page types that rank but are missing on officehub.sa (e.g. a "كراسي مكتبية طبية"
  category, a buying guide)

#### Gap table

| Keyword (AR / EN) | Who ranks | Page type that wins | officehub.sa page | Gap / action |
|---|---|---|---|---|

---

## 5. Product Schema Enhancement

Validate and generate Product schema following Google's current requirements.

### Confirmed Required Properties (Google Merchant)

Confirmed required fields are `name`, `image`, and `offers`; use `Offer`, not `AggregateOffer`, for merchant listings. Merchant listings require a `price` greater than zero, and `priceCurrency` whenever `price` is set.

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "",
  "image": [""],
  "offers": {
    "@type": "Offer",
    "url": "",
    "priceCurrency": "USD",
    "price": "49.00",
    "availability": "https://schema.org/InStock"
  }
}
```

### Recommended Properties (Enhance Rich Results)

- `sku` -- product identifier
- `description`, `brand`, `offers.seller` -- recommended context fields
- `gtin13` / `gtin14` / `mpn` -- global trade identifiers
- `aggregateRating` -- star rating + review count
- `review` -- individual reviews (minimum 1)
- `color`, `material`, `size` -- variant attributes
- `shippingDetails` -- ShippingDetails with rate and delivery time (merchant-level shipping via `ShippingService` is also supported; shipping/returns can be set in Search Console without a Merchant Center account)
- `hasMerchantReturnPolicy` -- MerchantReturnPolicy with type and days
- `hasAdultConsideration` -- **required for adult-oriented products** (added 2026-05-20 to Product variant / Merchant listing); Google Search supports only the value `https://schema.org/SexualContentConsideration`
- `category` -- `Text`, `CategoryCode`, or an array mixing both. Use custom
  text for merchant-defined product types and `CategoryCode` with Google's
  taxonomy URL plus `codeValue` for Google Product Categories.

### Validation Rules

1. `price` must be a number string, not "$29.99" (no currency symbol)
2. `availability` must use full Schema.org URL enum
3. `image` should be array with >= 1 high-res image URL
4. `priceCurrency` must be ISO 4217 (USD, EUR, GBP)
5. If `brand` is present, `brand.name` must not be empty or "N/A"
6. Sale periods use `validFrom` plus either `validThrough` or
   `priceValidUntil`, in ISO 8601 format. Include time and timezone when known.
7. If `aggregateRating` present: `ratingValue` and `reviewCount` required (the merchant-listing docs list `reviewCount`; the review-snippet docs also accept `ratingCount`)
8. Do not include fake reviews or undisclosed incentivized reviews in visible
   content or structured data. Clearly and prominently disclose incentives.

### Schema Scoring

| Completeness | Score |
|-------------|-------|
| All required fields | 50/100 |
| + aggregateRating | 65/100 |
| + sku/gtin/mpn | 75/100 |
| + shippingDetails | 85/100 |
| + merchantReturnPolicy | 90/100 |
| + reviews (3+) | 100/100 |

---

## Cross-Skill Integration

| Skill | Integration Point |
|-------|------------------|
| **seo-schema** | Delegates Product schema generation; reuses validation logic |
| **seo-images** | Product image audit (alt text, format, dimensions), plus `DigitalSourceType: TrainedAlgorithmicMedia` IPTC label for AI-generated product images (Merchant Center requirement) |
| **seo-content** | Product description E-E-A-T and uniqueness analysis |
| **seo-technical** | Core Web Vitals for product pages (LCP on hero image) |
| **seo-hreflang** | Region-specific result units: in the EEA, product and (since 2026-09-18) local business queries can show aggregator and supplier units; the EEA, South Africa and Türkiye also have structured data carousels, each with its own eligibility rules (documented 2026-09-08) |
| **seo-hreflang** (ar/en) | Arabic and English product pages linked and complete |
| Search Console export (pasted) | Indexation + Performance data for product URLs (Merchant Center feed validation happens in Merchant Center itself) |

## UCP: Universal Commerce Protocol (live)

Google-initiated open standard (co-developed with Shopify, Etsy, Wayfair,
Target, Walmart; payment partners Visa/Mastercard/Stripe/Adyen/Amex) for
letting AI agents discover, negotiate, and transact with merchants without
one-off integrations. Google confirms a first reference implementation for
conversational buying in AI Mode in Search. Broader Universal Cart rollout
details are reported from Google I/O 2026 keynote coverage; not confirmed on a
Google-owned source. ucp.dev lists **2026-08-25** as the latest spec release (Google's merchant
guide still documents 2026-04-08) in its **date-based versioning** scheme, not `1.0`; two integration paths: **Native**
(default) and **Embedded** (approved merchants). Pairs with **AP2** (reportedly
moving toward FIDO governance). Canonical: developers.google.com/merchant/ucp
and ucp.dev.

Merchants already on **Google Merchant Center** with clean Product schema can
declare a UCP profile at `/.well-known/ucp` listing capabilities
(`dev.ucp.shopping.checkout`, `.fulfillment`, `.discount`). See
`workflows/seo-ecommerce/references/ucp-universal-commerce-protocol.md` for audit criteria,
capability examples, and the relationship to AP2 (Agent Payments Protocol).

### Audit command

```bash
# Discover and validate the UCP profile
python3 scripts/ucp_check.py https://store.example.com --json

# With endpoint reachability probes (HEAD each declared capability)
python3 scripts/ucp_check.py https://store.example.com --probe-endpoints --json
```

The script returns: profile presence, version, declared capabilities,
structural issues (missing fields, unknown capability IDs), and (with
`--probe-endpoints`) per-endpoint reachability. SSRF-blocked endpoints are
reported explicitly. Missing profile is reported as opportunity, not failure.
UCP itself is live; what's early is broad merchant adoption. Flag a literal
`"version": "1.0"` as invalid (UCP versions are date-based, e.g. `2026-04-08`).

---

## Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| No Product schema found | Page lacks JSON-LD | Analyze page content, generate recommended schema |
| Search results not Saudi | Web search ignores location | Add "السعودية" / city to the query, prefer .sa and Saudi store results, note the limitation |
| Competitor page blocks fetch | Bot protection | Use the search snippet and say the page was not fetched |
| Invalid URL | Malformed input | Show the error and ask for the full URL |
| Non-product page | URL is category/homepage | Run the store-level checks (UCP profile, category structure, feeds) and ask for a product URL for the product-level checks |

---

## Output Template

```
## E-commerce SEO Report: [URL or Keyword]

### Overall Score: XX/100

### Product Page SEO
- Schema Completeness: XX/100
- Title & Meta: XX/100
- Image Optimization: XX/100
- Content Quality: XX/100
- Internal Linking: XX/100

### Saudi Market Comparison (sampled)
- Keywords checked: [AR / EN list]
- Sampled price range: XX – XX SAR (median XX SAR); officehub.sa: XX SAR
- Offer gaps vs competitors: [delivery / installation / warranty]
- Noon / Amazon.sa naming benchmark: [notes]

### Top Recommendations
1. [Critical] ...
2. [High] ...
3. [Medium] ...

Offer a downloadable Markdown or .docx report if the user wants one.
```
