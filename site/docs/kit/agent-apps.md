# Agent apps

`.claude/settings.json` is in every site. Claude Code runs `npm run *` without asking, asks before `npm run deploy` and `npx wrangler *`, and is blocked from reading `.env` and `.dev.vars`. It applies once the folder is trusted in Claude Code.

The scaffold wrote these only for the apps picked at creation:

| File | App | For |
|---|---|---|
| `../.claude/launch.json` | Claude desktop | Starts `npm --prefix site run dev` for its preview pane |
| `.codex/environments/environment.toml` | Codex app | Setup (`npm install`) and Dev, Build, Preview actions |
| `.super.engineering/config.json` | super.engineering | Setup and the dev, build, preview run scripts |
| `../t3.json` | T3 Code | Install, Dev (opens the preview), Build, Preview actions; import them once in the app |
| `.zed/tasks.json` | Zed | dev, build, preview tasks |

Cursor needs no file. Every app reads this file (`CLAUDE.md` imports it), so all agent instructions live here.
