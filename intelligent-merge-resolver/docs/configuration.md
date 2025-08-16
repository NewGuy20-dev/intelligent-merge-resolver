## Configuration

- `.merge-resolver.yaml`

```yaml
project:
  type: "nextjs" # or react, vue, python, etc.
preferences:
  ui_style: "modern"
  code_style: "functional"
  accessibility: "high"
reasoning:
  enable_visual_analysis: true
  enable_context_analysis: true
  confidence_threshold: 0.85
  max_context_size: 50000
build:
  dev_command: "npm run dev"
  build_command: "npm run build"
  test_routes: ["/", "/dashboard", "/settings"]
```

- Environment variables
  - `GEMINI_API_KEY`: Gemini key (alternatively in `.env.local`)
  - `IMR_SERVER_URL`: If set, Python routes AI calls via server
  - `IMR_SERVER_PORT`: Port for `server.js` (default 3939)
