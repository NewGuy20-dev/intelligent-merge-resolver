## Architecture Overview

- Node.js package wraps a Python core engine
- Python CLI (`src/python/cli/main.py`) orchestrates analysis and resolution
- Reasoning layers (`src/python/reasoning/*`) build multi-layer context
- Context system (`src/python/context/*`) selects and compresses data
- Visual analysis via JS bridge (Puppeteer) and OCR, aggregated in VisualReasoning
- Local server (`server.js`) proxies Gemini calls with 100-credit limit
- Configuration via `.merge-resolver.yaml` and `.env.local`