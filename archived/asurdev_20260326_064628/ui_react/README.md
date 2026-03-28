# asurdev Sentinel — Modern React UI

## Architecture

```
ui_react/
├── src/
│   ├── components/
│   │   ├── AgentCard.tsx
│   │   ├── SignalGauge.tsx
│   │   ├── PriceChart.tsx
│   │   ├── AstroWidget.tsx
│   │   ├── FeedbackPanel.tsx
│   │   └── PerformanceChart.tsx
│   ├── hooks/
│   │   ├── useAnalysis.ts
│   │   ├── useFeedback.ts
│   │   └── useAgents.ts
│   ├── services/
│   │   └── api.ts
│   ├── stores/
│   │   └── analysisStore.ts
│   └── App.tsx
├── package.json
└── vite.config.ts
```

## Run

```bash
cd ui_react
npm install
npm run dev
```

## API Endpoints

- `POST /api/analyze` — Run analysis
- `GET /api/agents/status` — Agent status
- `POST /api/feedback` — Submit feedback
- `GET /api/performance` — Agent performance
