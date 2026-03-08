# GyroFinance

Financial analysis engine with a **deterministic core** and an **isolated LLM layer**.

## Architecture

```
Frontend
   ↓
API Gateway (FastAPI)
   ↓
Control Engine (deterministico)  ←→  DB Persistente (SQLite / PostgreSQL)
   ↓ (solo se ambiguo)
LLM Layer (Claude)
   ↓
Report Generator
```

### Regola d'oro
- **LLM NON:** decide categorie finali, cambia numeri, ricalcola KPI
- **LLM SOLO:** suggerisce (transazioni ambigue), commenta, spiega (report narrativi)

---

## Struttura progetto

```
gyrofinance/
├── core/
│   ├── parser.py        # Parsing CSV, normalizzazione, deduplicazione
│   ├── categorizer.py   # Categorizzazione rule-based (deterministico)
│   └── kpi.py           # Calcolo KPI, aggregazioni, delta MoM
├── memory/
│   ├── models.py        # SQLAlchemy models (vendors, transactions, mappings)
│   └── ledger.py        # CRUD + mapping persistente + override manuale
├── llm/
│   ├── client.py        # Claude API client
│   ├── classifier.py    # Classificazione transazioni ambigue (prompt chiuso)
│   └── reporter.py      # Report narrativi e analisi comparativa
├── api/
│   ├── routes.py        # Tutti gli endpoint FastAPI
│   ├── schemas.py       # Pydantic schemas
│   └── deps.py          # Dependency injection (DB session)
├── data/
│   └── sample_estratto.csv
├── main.py
├── requirements.txt
└── Dockerfile
```

---

## Avvio rapido

### Prerequisiti
- Python 3.12+
- Una API key Anthropic

### Installazione locale

```bash
cd gyrofinance
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload
```

API disponibile su: `http://localhost:8000`
Docs interattive: `http://localhost:8000/docs`

### Docker

```bash
cp .env.example .env
# Inserisci la tua ANTHROPIC_API_KEY in .env
docker compose up --build
```

---

## Endpoint principali

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/v1/upload` | Carica CSV estratto bancario |
| `GET` | `/api/v1/transactions` | Lista transazioni (filtro mese/categoria) |
| `GET` | `/api/v1/kpis` | KPI del periodo (opzionale: ?month=YYYY-MM) |
| `GET` | `/api/v1/kpis/monthly` | KPI per ogni mese + delta MoM |
| `GET` | `/api/v1/generate-report?month=YYYY-MM` | Report narrativo mensile (LLM) |
| `GET` | `/api/v1/generate-report/comparative` | Analisi comparativa MoM (LLM) |
| `POST` | `/api/v1/classify-unknown` | Classifica transazione ambigua (LLM) |
| `POST` | `/api/v1/override-category` | Override manuale categoria |

---

## Categorie predefinite (placeholder)

- Marketing
- Software & SaaS
- Personale
- Affitto & Ufficio
- Utilities
- Banche & Finanza
- Fornitori
- Entrate
- Rimborsi & Crediti
- Altro

Le categorie sono configurabili in `core/categorizer.py`.

---

## Memory Ledger

Il sistema ricorda ogni associazione vendor→categoria:
- Se "Meta" = Marketing una volta → sempre Marketing
- Gli override manuali hanno priorità e vengono persistiti
- Ogni mapping è versionato nel DB

---

## Evoluzione MVP

| Step | Tecnologia |
|------|------------|
| MVP | SQLite + FastAPI locale |
| Prod | PostgreSQL + Docker |
| Scale | Frontend React/Vue + auth |
