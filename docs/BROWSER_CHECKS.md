# Repeatable browser checks

These tests use Playwright 1.63.0 / Chromium with fictional local data. They are not real-user studies or hosted production tests. Screenshots are written to `tests/screenshots/` (ignored). Set `REVIEW_OUTPUT` to another folder if desired.

Use a separate tooling folder to avoid adding production dependencies:

```sh
npm install --prefix /tmp/project-browser-tools playwright@1.63.0
/tmp/project-browser-tools/node_modules/.bin/playwright install chromium
PLAYWRIGHT_PATH=/tmp/project-browser-tools/node_modules/playwright node tests/browser.cjs
```

On Linux CI the browser install also uses `--with-deps`. Existing GitHub workflows prepare the browser and a local fixture server. New GitHub checks have not run remotely until a push is approved.

Start the API from the repository root with `AI_PROVIDER=mock ZABUM_REVIEW_FIXTURE=1 ZABUM_STORAGE_DIR=/tmp/zabum-browser-fixture PORT=5091 python backend/app.py`. Tests refuse a server without the explicit review flag, mock provider, and temporary storage. **They clear the fixture server's documents, chats and memories. Never use private data in that directory.**

See `docs/RELEASE_REVIEW.md` for architecture and limitations. Hardware/device checks beyond Chromium viewport emulation remain manual follow-up work.
