# Marketplace playbook

How to get Standup listed in each vendor's public directory, under a WCGW identity.

Installing by repository address already works everywhere and needs none of this (see `publishing.md`). This file is about being **listed**.

Researched on 16 November 2026 by a web research pass; every claim comes from the page linked next to it. "Not found" means the pages opened did not say. Vendors change these processes: re-open the link before acting on a row.

## What only Radu can do

Accounts and agreements. An agent must not create these.

| # | Account | Needed for | Notes |
| --- | --- | --- | --- |
| 1 | A GitHub organisation | Everything. Gemini, Grok, skills.sh and Cursor show the repository owner as the publisher. | `wcgw` is taken. `wcgwfun` and `wcgw-fun` were free on 12 November. |
| 2 | A paid claude.ai plan with the organisation's GitHub connected | Anthropic's directory | Pro, Max, Ultra, Team or Enterprise; Owner role on Team or Enterprise. The first organisation to submit a repository folder holds the listing. |
| 3 | An OpenAI Platform organisation, verified as an individual or a business | The ChatGPT and Codex catalog | Verification is what lets the listing carry a personal or company name. |
| 4 | A Cursor account | Cursor's marketplace | What kind of account, and whether a studio can be the publisher: not found. |

Everything else is a file in this repository or a pull request, and can be prepared here.

## The order to do it in

1. Create the GitHub organisation and push this repository to it, public.
2. Add the GitHub topic `gemini-cli-extension`. Gemini's gallery lists it by itself.
3. Run `npx skills add <owner>/<repo>` once. skills.sh lists a repository the first time someone installs from it.
4. Submit to Anthropic's directory.
5. Submit to Cursor's marketplace.
6. Open the pull request to xAI's catalog.
7. Submit to OpenAI's catalog. It asks for the most: more manifest fields, icons and a privacy-policy URL.
8. opencode's community list, once the repository is 30 days old and has 25 stars.

## Vendor by vendor

### Anthropic: Claude Code, claude.ai, Cowork

- **Directory:** <https://claude.ai/directory>. One listing reaches all three; in Claude Code it loads as `standup@synced`. ([publish](https://code.claude.com/docs/en/plugins/publish.md))
- **Submit:** the developer portal, <https://claude.ai/directory/manage>, then Submit new, then Plugin bundle. The `claude-plugins-official` repository takes no submissions and its pull requests are not monitored. ([publish](https://code.claude.com/docs/en/plugins/publish.md), [repo](https://github.com/anthropics/claude-plugins-official))
- **Publisher name:** `author.name` in `plugin.json`. A name that looks like another publisher or brand is held for a reviewer. ([checklist](https://claude.com/docs/plugins/pre-submission-checklist))
- **Requirements** ([checklist](https://claude.com/docs/plugins/pre-submission-checklist), [submit](https://claude.com/docs/plugins/submit)):
  - a GitHub repository, public before it goes live, and push access from the connected account;
  - `.claude-plugin/plugin.json` with a unique lowercase, hyphenated `name` of at most 64 characters;
  - a README of at least 40 words, and a `LICENSE` file or a `license` field (both blocking);
  - `description`, `author` and `version` (warnings when missing);
  - non-image files under 256 KiB, at most 512 files, no binaries, no secrets;
  - data-handling questions, four acknowledgements, and the Software Directory Terms and Policy.
- **Review:** an automated validation and security scan on every version, and a person reviews each new listing. "Review time isn't fixed." ([publish](https://claude.com/docs/directory/publish))
- **Cost:** none stated beyond the paid plan. Icon size: not found.
- **Where Standup stands:** the plugin passes `claude plugin validate`. A script that `SKILL.md` only tells Claude to run is not held for review, and that is how the engine is called. Our own check also asked for a square PNG icon of 512 to 2048 px, set once at first submission; `plugin/.claude-plugin/icon.png` is 512 px.

### OpenAI: ChatGPT and Codex

- **Directory:** ChatGPT and Codex use the same public plugin catalog; Codex shows it under `/plugins`. ([plugins](https://learn.chatgpt.com/docs/plugins))
- **Submit:** <https://platform.openai.com/plugins>, then "Upload new or existing plugin". ([submission](https://developers.openai.com/plugins/deploy/submission))
- **Publisher name:** the `developerName` field, backed by the organisation's individual or business verification.
- **Requirements** ([build](https://developers.openai.com/codex/plugins/build)):
  - a root `plugin.json` with `name`, `version`, `description`;
  - `displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `composerIcon`, `logo`;
  - icons square, at least 48 px, PNG, JPEG, WebP or SVG, at most 5 MiB;
  - an HTTPS privacy-policy URL;
  - no lifecycle hooks.
- **Review:** policy attestations, one active review per plugin, feedback by email. Timing and cost: not found.
- **Open question:** the build page says public submission "still requires a remote HTTPS MCP endpoint"; the submission page says a skills-only plugin can be submitted without one. Standup is skills only. Settle this before spending time on the listing.
- **Where Standup stands (18 November 2026):** Codex already installs it from our Claude-format marketplace file. For the listing, `plugin/plugin.json` is written in the Agent Plugins format with the listing under `extensions.com.openai.interface`, its icon is `plugin/assets/icon.png`, and the privacy page is at https://standup.wcgw.fun/privacy/. The open question above is settled by the submission page read that day: a skills-only package is uploaded as a ZIP and needs no MCP endpoint, review cases or demo recording. What remains is Radu's: the verified OpenAI organisation and the upload. See `submissions.md`.

### Cursor

- **Directory:** cursor.com/marketplace.
- **Submit:** the repository link at <https://cursor.com/marketplace/publish>. The form could not be read by the research pass. ([plugins](https://cursor.com/docs/plugins), [reference](https://cursor.com/docs/reference/plugins))
- **Publisher name:** `author.name` in the plugin manifest and `owner.name` in the marketplace file.
- **Requirements:** a public Git repository ("All plugins must be open source", in the FAQ only), `.cursor-plugin/plugin.json` with a unique kebab-case `name`, a clear `description`, a `README.md`, relative paths only, and a logo by relative path if there is one.
- **Review:** every plugin and every update is reviewed by hand. Timing and cost: not found.
- **Where Standup stands:** the manifests exist and follow the docs. Cursor has never loaded them; test with `cursor-agent --plugin-dir plugin` before submitting.

### Gemini CLI

- **Directory:** geminicli.com/extensions.
- **Listing:** automatic. Add the GitHub topic `gemini-cli-extension`; the gallery crawls tagged repositories daily and lists one "if it passes validation". No form. ([releasing](https://geminicli.com/docs/extensions/releasing/))
- **Publisher name:** the repository owner.
- **Requirements:** a public GitHub repository with `gemini-extension.json` at its absolute root.
- **Where Standup stands:** done. The manifest is at the root and `skills` links to `plugin/skills`; Gemini loads it and finds both skills.
- **Worth knowing:** the site says that for unpaid and Google One users "Gemini CLI was replaced by Antigravity CLI on June 18th, 2026". ([about](https://geminicli.com/extensions/about/))

### xAI: Grok

- **Directory:** the catalog repository <https://github.com/xai-org/plugin-marketplace>, browsed from Grok's Marketplace tab.
- **Listing:** a pull request adding an entry to `.grok-plugin/marketplace.json` with `name` and `source`, a remote source pinned to a full 40-character commit `sha`, then `python3 scripts/generate-plugin-index.py` and `python3 scripts/validate-catalog.py`.
- **Review:** by the code owners. xAI does not verify plugins. Timing: not found.
- **Where Standup stands:** Grok reads Claude Code marketplaces and plugins as they are ([docs](https://docs.x.ai/build/features/skills-plugins-marketplaces)), and `grok plugin validate plugin` passes. The pull request needs a public commit to pin, so it waits for the push.

### opencode

- **Directory:** none central. The official ecosystem page has a community table and points to awesome-opencode. ([ecosystem](https://opencode.ai/docs/ecosystem/))
- **awesome-opencode:** a pull request adding `data/plugins/<name>.yaml` with `name`, `repo`, a `tagline` of at most 120 characters, and `description`. The repository must be public, at least 30 days old, with 25 stars and a commit in the last 90 days, and must document opencode as a target. ([contributing](https://raw.githubusercontent.com/awesome-opencode/awesome-opencode/main/contributing.md))
- **Worth knowing:** opencode reads skills from `.claude/skills` and `.agents/skills`. ([skills](https://opencode.ai/docs/skills/)) That may make our copy command simpler; not tested.

### Cross-agent directories

- **skills.sh (Vercel):** automatic. A repository appears when someone runs `npx skills add <owner>/<repo>`, ranked by installs; the owner shown is the GitHub owner. ([FAQ](https://skills.sh/docs/faq))
- **claudemarketplaces.com:** third party, "not officially affiliated with Anthropic". It crawls skills.sh and GitHub repositories with valid marketplace files, and has a Submit page that was not opened. ([about](https://claudemarketplaces.com/about))

## What "a WCGW identity" comes to

Only OpenAI verifies a publisher name. Anthropic ties a listing to the organisation that submits it and screens `author.name`. Everywhere else the publisher is the GitHub owner or the name in the manifest.

So the identity is three things: the GitHub organisation's name, `author.name` and `owner.name` in the manifests ("What Could Go Wrong" since 16 November), and the verified name on the OpenAI organisation. Make them the same string.
