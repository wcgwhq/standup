#!/usr/bin/env bash
# Build and upload dist/ to Cloudflare Pages (Direct Upload, static, no SSR adapter).
# Needs `npx wrangler@4.158.0 login` once, or CLOUDFLARE_API_TOKEN with Pages: Edit plus CLOUDFLARE_ACCOUNT_ID.
# Refuses a localhost SITE_URL and a build that still has the placeholder sentence, and creates
# the Pages project on first deploy (name from wrangler.toml, or CLOUDFLARE_PAGES_PROJECT).
#
#   npm run deploy -- https://example.com           # SITE_URL for this build, branch main
#   npm run deploy -- https://example.com preview   # any other branch is a preview deploy
#   CLOUDFLARE_PAGES_PROJECT=my-pages npm run deploy
#
# pages.dev hosts are noindexed unless the canonical is the pages.dev host.
set -euo pipefail

WRANGLER=wrangler@4.158.0
PLACEHOLDER='fill the one-sentence intent'

cd "$(dirname "$0")/.."

if [[ -n "${1:-}" ]]; then export SITE_URL="$1"; fi
BRANCH="${2:-main}"
PROJECT="${CLOUDFLARE_PAGES_PROJECT:-$(sed -n 's/^name *= *"\([^"]*\)".*/\1/p' wrangler.toml | head -1)}"

HOST="$(node --input-type=module -e "
  import('./site.config.mjs').then(
    (m) => console.log(new URL(m.siteUrl).hostname),
    (e) => { console.error(e.message); process.exit(1); },
  );")"
case "$HOST" in
  localhost | *.localhost | 127.* | 0.0.0.0)
    echo "SITE_URL is $HOST. Pass the real origin: npm run deploy -- https://your-domain"
    exit 1
    ;;
esac

# Listing the projects is the login check: a token limited to Pages can do it, and `whoami` refuses that token.
if ! PROJECTS="$(npx --yes "$WRANGLER" pages project list --json 2>/dev/null)"; then
  echo "Not logged in to Cloudflare. Run: npx $WRANGLER login (or set CLOUDFLARE_API_TOKEN with Pages: Edit, and CLOUDFLARE_ACCOUNT_ID)"
  exit 1
fi

npm run build

if grep -rqsF "$PLACEHOLDER" dist; then
  echo "dist/ still has the placeholder intent. Find it with: grep -rlF '$PLACEHOLDER' src public"
  exit 1
fi

{
  printf '\nhttps://:version.:project.pages.dev/*\n  X-Robots-Tag: noindex\n'
  if [[ "$HOST" != *.pages.dev ]]; then printf 'https://:project.pages.dev/*\n  X-Robots-Tag: noindex\n'; fi
} >>dist/_headers

# --force keeps a new project on Pages when an agent runs this (wrangler would create a Worker).
if ! PROJECT="$PROJECT" node -e '
  const list = JSON.parse(require("node:fs").readFileSync(0, "utf8"));
  process.exit(list.some((p) => p["Project Name"] === process.env.PROJECT) ? 0 : 1);
' <<<"$PROJECTS"; then
  npx --yes "$WRANGLER" pages project create "$PROJECT" --production-branch=main --force
fi

npx --yes "$WRANGLER" pages deploy dist --project-name="$PROJECT" --branch="$BRANCH" --commit-dirty=true
