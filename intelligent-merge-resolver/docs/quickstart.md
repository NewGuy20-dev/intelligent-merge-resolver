## Quick Start

- Install in a Next.js project:

```bash
npm install intelligent-merge-resolver
```

- Start the local AI proxy server (reads `.env.local`):

```bash
npm run server
```

- Initialize and analyze:

```bash
npx merge-resolve init
npx merge-resolve analyze
```

- Resolve with reasoning:

```bash
npx merge-resolve resolve --auto --confidence-threshold 0.85
```

Notes:
- Ensure `.env.local` contains `GEMINI_API_KEY=...` in your project root.
- Set `IMR_SERVER_URL=http://127.0.0.1:3939` to route AI calls via the server.
