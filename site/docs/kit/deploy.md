# Deploy to Cloudflare Pages

```sh
npm run deploy -- https://your-domain           # production branch main
npm run deploy -- https://your-domain preview   # any other branch is a preview
```

The header of `scripts/deploy.sh` lists what it refuses, how to log in, and how pages.dev hosts are noindexed. 
**A push to `main` that changes `site/` deploys by itself:** `../.github/workflows/deploy.yml` runs the same script for `https://standup.wcgw.fun`, with the Cloudflare token and account ID from the repository's secrets. Run it by hand only for a preview. Treat a push to `main` as a deploy: ask the human first.
