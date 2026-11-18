# Kit upgrades and dev pages

## wcgw upgrade

`wcgw.json` records the kit version and commit this site came from, and the answers that shaped it. Leave it as the kit wrote it. Every page carries the version in `<meta name="wcgw">`.

`wcgw upgrade`, run here on a clean git tree, brings in what the kit changed since. `wcgw upgrade --dry-run` lists it without writing.

- A file this site never changed takes the kit's version.
- A file both changed is merged line by line. Lines both changed keep both versions between `<<<<<<<` markers: resolve each one, keeping the site's intent and the kit's fix.
- A file the site deleted, an image both changed and `package-lock.json` stay as they are, and are listed.

Afterwards: resolve the markers, `npm install` when `package.json` changed, `npm run verify`, then show the human `git diff` before committing. `git checkout . && git clean -fd` undoes the whole upgrade.

Upgrades merge cleanly when site work stays out of kit files. Put new behaviour in new files (a component, a page, a script) and keep edits to `scripts/`, `functions/`, `astro.config.mjs` and `BaseLayout.astro` small.

## Dev pages

A page in `src/dev/` is served at `/dev/<name>/` under `npm run dev` only; a build never ships it. `src/dev/styleguide.astro` shows the tokens and type. Add each shared component to it as it appears, and check it there after changing one.
