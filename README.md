# OfficeHub skills

Shared Claude skills for the OfficeHub team. Each folder below is one skill.

| Skill | What it does |
|---|---|
| `officehub-product-angles` | Give it one photo of a furniture item plus its dimensions (W x D x H). Claude writes one ready-to-paste prompt per angle (front, 3/4, sides, back, top, detail). You generate each image in Gemini (or ChatGPT) with the original photo attached, then upload the results back so Claude can check them. No API key needed. |
| `officehub-seo` | Full SEO toolkit: site and page audits, technical SEO, schema, E-E-A-T content, AI search (GEO), local, e-commerce, hreflang, keyword clusters, content briefs and SEO plans. Adapted from the MIT-licensed claude-seo project (see `officehub-seo/LICENSE.txt`). No API key needed. |

## Install a skill (claude.ai)

1. Zip the skill folder itself, so the zip contains the folder (for example `officehub-seo/SKILL.md`).
   On Windows: right-click the folder, then **Send to > Compressed (zipped) folder**.
2. In Claude, open **Settings > Capabilities > Skills** and choose **Upload skill**.
3. Pick the zip. The skill now loads automatically when a chat matches its description.

## Rules for adding skills

- One folder per skill, with a `SKILL.md` whose `name:` matches the folder name.
- Names are kebab-case and must not contain "claude".
- Never commit API keys, `.env` files or zips (see `.gitignore`).
