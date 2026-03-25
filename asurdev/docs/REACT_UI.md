# React UI — Развёртывание

## 1. Локальная разработка

```bash
cd ~/asurdevSentinel/ui_react

# Установка
npm install

# Запуск dev сервера
npm run dev
# http://localhost:5173

# Запуск API proxy
uvicorn api.main:app --reload --port 8000
```

## 2. Структура

```
ui_react/
├── src/
│   ├── components/
│   │   ├── AgentCard.tsx      # Карточка агента
│   │   ├── SignalPanel.tsx     # Панель сигналов
│   │   ├── ChartView.tsx       # График
│   │   ├── FeedbackForm.tsx    # Обратная связь
│   │   └── MemorySearch.tsx    # RAG поиск
│   ├── hooks/
│   │   ├── useAnalysis.ts      # Hook анализа
│   │   └── useFeedback.ts      # Hook обратной связи
│   ├── services/
│   │   └── api.ts              # API клиент
│   └── stores/
│       └── analysisStore.ts    # Zustand store
├── package.json
└── vite.config.ts
```

## 3. Ключевые компоненты

### AgentCard.tsx
```tsx
interface AgentCardProps {
  agent: {
    name: string;
    signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    confidence: number;
    summary: string;
  };
}

export function AgentCard({ agent }: AgentCardProps) {
  const color = {
    BULLISH: 'text-green-500 border-green-500',
    BEARISH: 'text-red-500 border-red-500',
    NEUTRAL: 'text-yellow-500 border-yellow-500'
  }[agent.signal];

  return (
    <div className={`border-l-4 ${color} p-4 rounded`}>
      <h3>{agent.name}</h3>
      <p>{agent.signal} ({agent.confidence}%)</p>
      <p>{agent.summary}</p>
    </div>
  );
}
```

### useAnalysis.ts
```tsx
import { useState, useCallback } from 'react';
import { api } from '../services/api';

export function useAnalysis() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  const analyze = useCallback(async (symbol: string) => {
    setLoading(true);
    try {
      const result = await api.analyze(symbol);
      setData(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  return { analyze, loading, data };
}
```

## 4. Production build

```bash
# Build
npm run build
# Выход в dist/

# Docker
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
EXPOSE 80
```

## 5. Nginx конфиг

```nginx
# /etc/nginx/sites-available/asurdev
server {
    listen 80;
    server_name asurdev.local;
    
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```
