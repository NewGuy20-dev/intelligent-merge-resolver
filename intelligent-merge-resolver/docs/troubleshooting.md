## Troubleshooting

- Python not found: Ensure Python 3.8+ is installed and available as `python3` or `python`.
- Gemini key missing: Add `GEMINI_API_KEY=...` to `.env.local` in the project root.
- Puppeteer not installed: Install `puppeteer` in your project to enable screenshots.
- Server not responding: Run `npm run server` and check `IMR_SERVER_PORT` and `/status` endpoint.
- Permission errors on hooks: Ensure git hooks are executable and repo path is correct.