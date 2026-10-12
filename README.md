# OfficeHub skills

Shared Claude skills for the OfficeHub team, published as a plugin marketplace.
Each skill is its own plugin, so you pick only the ones you want.

| Plugin | What it does |
|---|---|
| `officehub-product-angles` | Give it one photo of an office-furniture item plus its dimensions (W x D x H). Claude writes one ready-to-paste prompt per angle (front, 3/4, sides, back, top, detail), with defaults for chairs, desks, workstations and storage. You generate each image in Gemini (or ChatGPT) with the original photo attached, then upload the results back so Claude can check them. It then prepares file names, Arabic/English alt text and the AI label for upload. No API key needed. |
| `officehub-seo` | SEO toolkit for officehub.sa: site and page audits, technical SEO, schema, product and category pages, Arabic and English keywords and content, AI search (GEO), local SEO, hreflang, content briefs and SEO plans. Knows the Saudi market and Shopify/WooCommerce. Adapted from the MIT-licensed claude-seo project (see `plugins/officehub-seo/skills/officehub-seo/LICENSE.txt`). No API key needed. |
| `officehub-png2svg` | Turns a PNG (or JPG/WebP) logo, icon or illustration into a high-detail SVG. Finds and removes any solid background automatically, keeps same-coloured details inside the artwork, removes edge halos, snaps flat artwork to its real colours (or to brand colours you give it) and checks the SVG against the original with a side-by-side preview. Needs code execution and `pip install vtracer resvg-py`. Adapted from the MIT-licensed lovstudio/png2svg-skill. |

### Fill in the OfficeHub profile

`plugins/officehub-seo/skills/officehub-seo/references/officehub-profile.md` holds the business
facts the SEO skill uses on every run: platform, URL pattern, cities, delivery and installation,
NAP, CR and VAT numbers, competitors, brand voice. Fields marked `TODO` are unknown; Claude will
ask for them instead of guessing. Fill them in (and bump the plugin version) so every run starts
with the right facts.

## Install in claude.ai, the desktop app or Cowork

1. Go to **Customize > Plugins** (claude.ai/customize/plugins).
2. Choose **Add > Add marketplace** and enter `Mosta96/officehub-skills`.
   The repo is private: when asked, connect your GitHub account and give the Claude GitHub App access to it.
3. The OfficeHub plugins now show up. Open one and choose **Add**. Repeat for the other if you want it.
4. Optional: turn on **Sync automatically** for the marketplace to get updates.

Plugins added this way also sync to Claude Code when you're signed in with the same account.

## Install in Claude Code

```
/plugin marketplace add Mosta96/officehub-skills
/plugin install officehub-product-angles@officehub-skills
/plugin install officehub-seo@officehub-skills
/plugin install officehub-png2svg@officehub-skills
```

Or run `/plugin` and pick them from the **Discover** tab. Your git must already be signed in to GitHub (for example with `gh auth login`), because the repo is private.

## Manual install (fallback)

Zip the skill folder `plugins/<plugin>/skills/<plugin>/` (the zip must contain that folder) and upload it in
**Settings > Capabilities > Skills > Upload skill**.

## Layout and rules for adding skills

```
.claude-plugin/marketplace.json        lists every plugin
plugins/<name>/.claude-plugin/plugin.json
plugins/<name>/skills/<name>/SKILL.md  the skill itself
```

- Add a new skill as a new plugin folder, plus an entry in `marketplace.json`.
- Names are kebab-case and must not contain "claude". The plugin name, folder name and SKILL.md `name:` match.
- Bump `version` in the plugin's `plugin.json` when you change it, so users get the update.
- Never commit API keys, `.env` files or zips (see `.gitignore`).
