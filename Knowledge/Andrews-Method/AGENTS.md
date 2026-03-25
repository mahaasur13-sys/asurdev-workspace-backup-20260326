# Andrews-Method Knowledge Base

## Структура

```
Andrews-Method/
├── atomic/           # Атомарные заметки (один концепт)
│   ├── 001-median-line.md
│   ├── 002-pitchfork.md
│   ├── 031-ar1-linea-centro.md
│   ├── 041-ar2-action-line.md
│   ├── 054-new-forks-rule1.md
│   ├── 080-median-pivot-zone.md
│   ├── 092-ar3-horizontal.md
│   └── 095-super-pitchforks.md
│
├── synthetic/        # Синтетические заметки (объединение концептов)
│   ├── philosophy-and-methods.md
│   ├── momentum-swing.md
│   └── high-low-lines.md
│
├── indexes/          # Индексы и навигация
│   ├── 📅-timeline.md
│   └── 🏷️-tags.md
│
└── examples/         # Примеры на реальных активах
    └── (файлы примеров)
```

## Zettelkasten принципы

1. **Атомарность** — одна идея на заметку
2. **Связи** — ссылки на связанные заметки
3. **Теги** — для навигации и RAG
4. **Автономность** — заметка читается без контекста

## RAG Integration

Для использования в AstroFin Sentinel:
```
knowledge_base = "/home/workspace/Knowledge/Andrews-Method"
index_name = "andrews-method"
chunk_size = 512
```

## Источники

- Патрик Микула "Лучшие методы линий тренда Алана Эндрюса плюс пять новых техник"
- Материалы Google Drive папки "ТРЕЙД"
