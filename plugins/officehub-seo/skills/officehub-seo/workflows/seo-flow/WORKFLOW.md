# FLOW Framework: Find · Leverage · Optimize · Win

> Chat edition: follow the "Chat adaptation rules" in the top-level SKILL.md for fetching, scripts, subagents, output files and API-keyed steps.

FLOW is an evidence-led SEO operating model built for the AI-search era. This edition
keeps the FLOW stages and framework, with a prompt library of 10 prompts: the 3
upstream Win prompts plus 7 prompts written for OfficeHub (Arabic + English, Saudi
market). The upstream library's other 38 prompts shared one generic body and were
removed.

> Framework and Win prompts © Daniel Agrici, CC BY 4.0: github.com/AgriciDaniel/flow

**Runtime context:** Load `workflows/seo-flow/references/flow-framework.md` whenever this
workflow is used. For officehub.sa, also load `references/officehub-profile.md` and
`references/saudi-market.md`. Load prompt files on demand, only for the stage requested.

---

## Asks

| Ask | What it does |
|---------|-------------|
| flow | Show FLOW overview + stage menu |
| flow find `[url\|topic]` | Keyword research in Arabic and English, buying-guide briefs (2 prompts) |
| flow leverage `[url]` | Earned links and mentions in Saudi Arabia (1 prompt) |
| flow optimize `[url]` | Product page, category page, titles/meta (3 prompts; pick by page type) |
| flow win `[url]` | BOFU brief, conversion audit, dual-surface scorecard (3 prompts) |
| flow local `[url]` | Google Business Profile for a showroom/warehouse (1 prompt) |
| flow prompts | Index of all 10 prompts |

---

## Orchestration Logic

### flow (no stage)
1. Read `workflows/seo-flow/references/flow-framework.md`
2. Show the FLOW stage overview with a one-line description of each stage
3. Ask: which stage matches the user's current situation?

### flow find
1. Read the prompts in `workflows/seo-flow/references/prompts/find/`
2. Run `keyword-research-ar-en.md` first; use `buying-guide-brief.md` for "learn" clusters
3. For deeper SERP clustering, point to the cluster workflow

### flow leverage
1. Read `workflows/seo-flow/references/prompts/leverage/saudi-link-opportunities.md`
2. Apply it; for backlink data, point to the backlinks workflow

### flow optimize
1. Pick by page type: product page → `product-page-rewrite.md`; category/collection →
   `category-page-rewrite.md`; many URLs or a CTR problem → `title-meta-ar-en.md`
2. Load only the chosen prompt(s) and say which and why
3. For full content quality analysis, point to the content and geo workflows

### flow win
1. Read all files in `workflows/seo-flow/references/prompts/win/`
2. Apply each prompt to the URL's conversion and bottom-funnel context
3. For persona scoring, point to the sxo workflow

### flow local
1. Read `workflows/seo-flow/references/prompts/local/gbp-profile.md`
2. Apply to the showroom or warehouse; for the full local audit, point to the local workflow

### flow prompts
1. Read `workflows/seo-flow/references/prompts/README.md` and show the index

---

## Running a prompt

The prompts are templates. Fill the `[PLACEHOLDERS]` from the conversation,
`references/officehub-profile.md` and fetched pages, then do the work yourself and
return the output the prompt asks for. Ask once for required inputs that are missing.

---

## Reference Files

Load on-demand, do NOT load all at startup:
- `workflows/seo-flow/references/flow-framework.md`: FLOW operating model (load on every use)
- `workflows/seo-flow/references/bibliography.md`: Evidence sources; load when citing studies or statistics
- `workflows/seo-flow/references/prompts/README.md`: Prompt index
- `workflows/seo-flow/references/prompts/find/`: 2 prompts
- `workflows/seo-flow/references/prompts/leverage/`: 1 prompt
- `workflows/seo-flow/references/prompts/optimize/`: 3 prompts
- `workflows/seo-flow/references/prompts/win/`: 3 prompts
- `workflows/seo-flow/references/prompts/local/`: 1 prompt

---

## Attribution

When a FLOW stage is used, output before the analysis:

```
Framework and Win prompts © Daniel Agrici, CC BY 4.0: github.com/AgriciDaniel/flow
```

Do not omit or modify the attribution.
