<!-- Updated: 2026-04-17 -->
# Keyword Density and Placement Rules

Internal readability and stuffing heuristic. This is not a Google percentage rule.

## Primary Keyword Density

**Use check:** Confirm the primary keyword appears naturally in important locations and does not read as forced repetition.

| Pattern | Assessment |
|---------|-----------|
| Missing from key locations | Review placement. The topic may be unclear. |
| Natural recurring use | Accept if it reads cleanly for users. |
| Noticeable repetition | Review required. May read unnaturally. |
| Forced repetition | Keyword stuffing risk. Rewrite for clarity and usefulness. |

**Practical example:** For a 1,000-word article, do not target a quota. Use the primary keyword where it helps users understand the page topic, including headings, body text, and image alt text when relevant.

**Diminishing returns:** Early mentions help establish topic context. After that, prioritise placement quality over quantity.

## Required Placement Locations

The primary keyword MUST appear in all of these:

1. **Title tag** (near the front, not buried at the end)
2. **H1 tag** (near the front)
3. **URL slug** (lowercase, hyphenated)
4. **Meta description** (naturally integrated)
5. **First paragraph / first 100 words** (establishes topic immediately)
6. **At least one image alt text** (reinforces topic for image search)

## Locations Where It Is NOT Required

- Every H2 or H3 (if the H1 covers the keyword, subheadings carry context naturally through semantic relationship)
- Every paragraph or section (clustering looks unnatural)
- Anchor text of every internal link (vary the anchor text)

## Secondary and Semantic Keywords

| Type | Count | Usage |
|------|-------|-------|
| Closely related terms | 5-8 | Distribute through body content and H2-H6 headings |
| Broader semantic terms | 10-15 | Cover related concepts and user intent variations |
| Synonyms | As natural | Improve readability. Do NOT count toward primary density. |

## Distribution Rules

- **Spread evenly** throughout the content. Do not front-load all mentions into the introduction or cluster in one section.
- **Per-section guidance in briefs:** For each section in a content brief, specify:
  - Which keyword (primary or secondary) should appear in the heading
  - Whether the section body should include the primary keyword or a variation
  - Format: "Use secondary keyword '[term]' in H2. Body: mention primary keyword once."

## Common Mistakes

1. **Exact-match obsession:** Using the exact phrase every time instead of natural variations. Google understands synonyms and related terms.
2. **Heading stuffing:** Putting the primary keyword in every H2 and H3. One H1 mention plus 1-2 H2 mentions is sufficient.
3. **Ignoring first 100 words:** The opening paragraph is the highest-value placement after the title and H1.
4. **Forgetting image alt text:** A free placement opportunity that also helps image search rankings.
5. **Counting synonyms as density:** "Web design", "website design", and "site design" are different strings. Only count exact-match appearances toward density.

## Arabic Keywords (OfficeHub edition)

The rules above assume English. For Arabic pages, apply these changes:

- **Count variants as one keyword.** Arabic attaches the article and prepositions to the word
  (كرسي، الكرسي، بالكرسي، وكراسي). Treat singular, plural and attached forms of the same
  phrase as one keyword when counting density: "كرسي مكتب" = "كراسي مكتب" = "كراسي مكتبية"
  = "الكراسي المكتبية".
- **Pick the exact-match form from the SERP**, not from a dictionary. Search the phrase on
  google.com.sa and use the form the top results use in their titles. Plural forms
  ("كراسي مكتبية") are often the head term for category pages, singular ("كرسي مكتب طبي")
  for product pages.
- **Lower the word-count expectations by about 20%.** Arabic needs fewer words than English to
  say the same thing, because of the attached forms. A 400-word English minimum is roughly
  320 Arabic words.
- **Spelling variants are separate strings for search.** ة/ه, أ/ا and ى/ي are often typed
  without care ("طاولة" vs "طاوله"). Use the correct spelling on the page. Do not stuff
  misspellings, but you can cover one common variant in alt text or the FAQ.
- **English and Latin-script queries are real.** Saudi buyers also search in English
  ("office chair riyadh") and by brand or model. Put English product names, model numbers
  and dimensions in the Arabic page too, and keep the English page as its own optimized
  page (see `workflows/seo-hreflang/WORKFLOW.md`).
- **Do not translate keywords.** Research Arabic and English keywords separately. The Arabic
  search for a product is often not a translation of the English one ("مكتب مدير" vs
  "executive desk").

See `references/saudi-market.md` for the full Arabic keyword method.
