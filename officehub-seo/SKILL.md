---
name: officehub-seo
description: Full SEO toolkit - site and page audits, technical SEO, schema, E-E-A-T content, AI search (GEO), local, e-commerce, hreflang, keyword clusters, content briefs and SEO plans.
license: MIT (adapted from AgriciDaniel/claude-seo v2.4.2, see LICENSE.txt)
---

# OfficeHub SEO (chat edition of claude-seo)

A Claude chat adaptation of the open-source **claude-seo** plugin by AgriciDaniel
(MIT). The original is a Claude Code plugin with slash commands, parallel
subagents and Python tooling. This edition keeps its methodology, checklists,
scoring and reference material, and runs everything inside a normal chat:
no API keys, no setup.

## How to use this skill

1. Work out which workflow the user wants from the table below. The user can
   say it in plain words ("audit example.com", "check the schema on this page")
   or with the original command style (`/seo audit example.com`); treat both
   the same. If the domain is clearly SEO but the workflow is unclear, ask one
   short question or default to **page** for a single URL and **audit** for a
   bare domain.
2. Open that workflow's file (`workflows/<name>/WORKFLOW.md`) and follow it,
   applying the **Chat adaptation rules** below wherever it mentions Claude
   Code features.
3. Load reference files only when the workflow says to. Never load them all.
4. Report using the **Output standard** at the bottom.

All paths in this skill are relative to this skill's folder.

## Workflows

| Ask / original command | Workflow file | What it does |
|---|---|---|
| audit `<url>` | `workflows/seo-audit/WORKFLOW.md` | Full-site audit, SEO Health Score 0-100, prioritized plan |
| page `<url>` | `workflows/seo-page/WORKFLOW.md` | Deep single-page analysis |
| technical `<url>` | `workflows/seo-technical/WORKFLOW.md` | Technical SEO (crawlability, indexability, CWV, security, 9 categories) |
| content `<url>` | `workflows/seo-content/WORKFLOW.md` | E-E-A-T and content quality |
| content-brief `<topic or url>` | `workflows/seo-content-brief/WORKFLOW.md` | Content brief: keywords, outline, internal links |
| schema `<url>` | `workflows/seo-schema/WORKFLOW.md` | Detect, validate and generate Schema.org JSON-LD |
| images `<url>` | `workflows/seo-images/WORKFLOW.md` | Image SEO audit and optimization advice |
| sitemap `<url or generate>` | `workflows/seo-sitemap/WORKFLOW.md` | Analyze or generate XML sitemaps |
| geo `<url>` | `workflows/seo-geo/WORKFLOW.md` | AI Overviews / ChatGPT / Perplexity optimization (GEO) |
| agentic `<url>` | `workflows/seo-agentic/WORKFLOW.md` | AI-agent readiness: llms.txt, Markdown, agent access, WebMCP |
| plan `<business type>` | `workflows/seo-plan/WORKFLOW.md` | Strategic SEO plan (templates in `workflows/seo-plan/assets/`) |
| programmatic `<url or plan>` | `workflows/seo-programmatic/WORKFLOW.md` | Programmatic SEO analysis and planning |
| competitor-pages | `workflows/seo-competitor-pages/WORKFLOW.md` | "X vs Y" and "alternatives" page generation |
| local `<url>` | `workflows/seo-local/WORKFLOW.md` | Local SEO: GBP, NAP, citations, reviews, local schema |
| maps `<business> <location>` | `workflows/seo-maps/WORKFLOW.md` | Maps presence (free tier only, see rules) |
| hreflang `<url>` | `workflows/seo-hreflang/WORKFLOW.md` | International SEO / hreflang audit and generation |
| backlinks `<url>` | `workflows/seo-backlinks/WORKFLOW.md` | Backlink profile from free sources only (see rules) |
| cluster `<seed keyword>` | `workflows/seo-cluster/WORKFLOW.md` | SERP-based keyword clustering and hub/spoke architecture |
| sxo `<url>` | `workflows/seo-sxo/WORKFLOW.md` | Search experience: page-type fit, user stories, personas |
| ecommerce `<url>` | `workflows/seo-ecommerce/WORKFLOW.md` | Product schema and e-commerce SEO |
| flow `<stage>` | `workflows/seo-flow/WORKFLOW.md` | FLOW framework prompts (Find, Leverage, Optimize, Win, Local) |

Google algorithm update questions ("is the spam update finished?"): use
`data/google-updates.json` (run `python3 scripts/seo_updates.py --json` if code
execution is on), then confirm recency with web search, because the bundled
ledger is a snapshot.

## Chat adaptation rules

The workflow files were written for Claude Code. Translate as follows.

**Fetching pages.** Use the web fetch tool to read pages and web search for
SERPs, competitors and brand mentions. Fetch `robots.txt`, `sitemap.xml`,
`llms.txt` and similar files directly by URL. Web fetch usually returns
readable text rather than raw HTML, so for checks that need raw markup
(JSON-LD, meta tags, canonicals, hreflang, headers) either:
- run the bundled scripts in code execution if the sandbox can reach the site
  (try `python3 scripts/fetch_page.py <url> --render never --json` once; if it
  fails with a network error, do not retry), or
- ask the user to paste the page source (Ctrl+U / "View page source") or
  upload the saved `.html` file, then run `python3 scripts/parse_html.py
  <file> --url <url> --json`, or read it directly.
If neither is possible, analyze what is visible and mark raw-HTML checks as
"not verified".

**Script commands.** Workflows reference `python3 scripts/<name>.py`. Only the
scripts listed below are bundled. If a workflow names a script that is not in
`scripts/`, do that step by reasoning over fetched content, or skip it and say
which check was skipped. Never `pip install` anything to make a script work.

Bundled scripts (standard library plus requests / beautifulsoup4 / lxml):
`fetch_page.py`, `parse_html.py`, `content_quality.py`, `content_humanize.py`,
`content_verify.py`, `metadata_template.py`, `schema_generate.py`,
`sitemap_discovery.py`, `agentic_check.py`, `agentic_fix.py`,
`preload_check.py`, `parasite_risk.py`, `gbp_deprecation_lint.py`,
`ucp_check.py`, `pagespeed_check.py`, `lighthouse_agentic.py`,
`commoncrawl_graph.py`, `verify_backlinks.py`, `seo_updates.py`, with helpers
`url_safety.py` and `google_auth.py`. Scripts that analyze text or a file work
offline; scripts that take a URL need the sandbox to have internet access.
`pagespeed_check.py` and `lighthouse_agentic.py` call Google PageSpeed
Insights without a key (low shared quota); if they fail, give the user the
https://pagespeed.web.dev link to run and paste results.

**Subagents.** Where a workflow says to spawn or delegate to subagents, run
those analyses yourself, one after another, in the same order, and keep each
one short. For a full audit on a large site, sample: homepage, 1-2 key
category/service pages, 1-2 articles or products, plus robots.txt and the
sitemap. State the sample in the report. Do not claim a 500-page crawl.

**Files and output folders.** Instructions to write `{domain}-audit/` folders,
baselines or findings files mean: put the result in the reply, or create a
downloadable file (Markdown, or a document if the user asks) when code
execution and file creation are on.

**API keys and paid data are out of scope.** Skip any step that needs Google
Search Console, GA4, CrUX, Indexing API, Keyword Planner, DataForSEO, Moz,
Bing Webmaster, Ahrefs, SE Ranking, Matomo, Firecrawl, Gemini or other keyed
services. Say once which data was not available. Offer the free alternative:
the user can paste or upload exports (GSC Performance CSV, GA4 report, Ahrefs
or Semrush exports, PageSpeed results), and you analyze those using the same
methodology.

**MCP tools.** If a workflow mentions an MCP tool (DataForSEO, Firecrawl), use
it only if that tool is actually connected in this chat; otherwise follow the
free path.

**PDF/Excel reports.** The original's `google_report.py` is not included. If
the user wants a polished report, produce a well-structured Markdown report,
or a .docx/.pdf if those file skills are available.

## Core methodology (applies to every workflow)

**Industry detection** from homepage signals:
- SaaS: pricing page, /features, /integrations, /docs, "free trial", "sign up"
- Local service: phone, address, service area, "serving [city]", map embed; suggest the local workflow
- E-commerce: /products, /collections, /cart, "add to cart", Product schema
- Publisher: /blog, /articles, author pages, dates, Article schema
- Agency: /case-studies, /portfolio, "our work", client logos
If ambiguous, present the top two with their signals and ask.

**SEO Health Score (0-100)**, weighted:
Technical 22%, Content quality 23%, On-page 20%, Schema 10%, Performance
(CWV) 10%, AI search readiness 10%, Images 5%.

**Priority levels:** Critical (blocks indexing or risks penalties), High
(significant ranking impact, fix within a week), Medium (opportunity, within a
month), Low (backlog).

**Synthesis framework.** Full audits and page analyses walk four phases before
writing the action plan: PERCEIVE (observe external and internal signals,
listen to the user's goal), ANALYZE (think from first principles, connect
laterally and systemically), VALIDATE (feel the user impact, accept what could
prove the finding wrong), ACT (create the fix, grow with a leading indicator).
Narrow workflows apply at least THINK and ACCEPT. Details:
`references/thinking-framework.md` and
`references/thinking-framework-validate-act.md`.

Every recommendation carries:
- the first-principle observation it rests on
- what it depends on or unblocks
- a "how would we know this failed?" check
- a leading indicator the user can watch without re-running the audit

**Hard quality gates** (see `references/quality-gates.md` for thresholds):
- Warn at 30+ location pages (need 60%+ unique content); hard stop at 50+ unless the user justifies it
- Never recommend HowTo schema (deprecated Sept 2023)
- FAQ rich results are retired for all sites (May 7, 2026): flag existing FAQPage as Info only, do not recommend removing it, do not recommend new FAQPage for Google SERP benefit, and do not claim AI-citation benefit; use QAPage for genuine user Q&A
- Core Web Vitals use INP, never FID

## Shared references (load on demand)

- `references/cwv-thresholds.md`: Core Web Vitals thresholds
- `references/schema-types.md`: schema types and deprecation status
- `references/eeat-framework.md`, `references/eeat-scoring-guide.md`: E-E-A-T criteria and scoring
- `references/quality-gates.md`: content length and uniqueness thresholds
- `references/local-seo-signals.md`, `references/local-search-behavior.md`, `references/local-schema-types.md`, `references/local-schema-multilocation.md`: local SEO
- `references/maps-free-apis.md`, `references/maps-gbp-checklist.md`, `references/maps-geo-grid.md`: maps
- `references/backlink-quality.md`, `references/free-backlink-sources.md`: backlinks
- `schema/templates.json`: ready-made JSON-LD templates

Workflow-specific references live next to each workflow in
`workflows/<name>/references/`.

## Output standard

- Open with the score (when the workflow scores) and the 3-5 most important findings.
- Group findings as Critical / High / Medium / Low, each with evidence (the URL, element or value you saw) and the fix.
- Mark anything you could not verify (raw HTML unavailable, data needs a key) as "not verified" rather than guessing.
- End with a short, ordered action plan.
- If a URL cannot be reached, say so and ask the user to check it. Never invent site content.
