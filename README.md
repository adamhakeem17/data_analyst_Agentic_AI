# AI Data Analyst Agent

Ask any question about your data in plain English. Get charts, insights, and a PDF report — all running locally with Ollama (no API keys needed).

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What it does

Upload a CSV, Excel, or JSON file → ask questions in natural language → get answers with auto-generated charts. Everything runs on your machine via [Ollama](https://ollama.ai).

- Natural language Q&A over any tabular dataset
- Auto chart generation (bar, line, pie, scatter) driven by the LLM or keyword fallback
- Per-column data quality profiler with a quality score
- Smart question suggestions based on your columns
- PDF export of the full conversation
- Conversation memory within a session
- Model selector in the sidebar (llama3, mistral, phi3, etc.)

---

## Architecture

```
app.py              Streamlit UI — no business logic
analyst.py          LangChain Pandas Agent + Ollama + chart spec parsing
charts.py           Plotly figure builders (spec-driven + keyword auto-detect)
profiler.py         Per-column quality stats + dataset summary
suggester.py        Question generation from column names/types
exporter.py         PDF session export (fpdf2)
loader.py           File loading + column type detection
```

All modules are single-responsibility. The UI layer (`app.py`) imports everything and wires it together.

---

## Quick Start

### Local

```bash
# 1. Install Ollama (https://ollama.ai) and pull a model
ollama pull llama3

# 2. Clone and install deps
git clone https://github.com/adamhakeem17/data_analyst_Agentic_AI
cd data_analyst_agentic_AI
pip install -r requirements.txt

# 3. (Optional) Generate a demo dataset
python generate_sample_data.py

# 4. Run
streamlit run app.py
```

Then open http://localhost:8501

### Docker

```bash
docker-compose up --build
```

This starts both Ollama and the Streamlit app. No local Python setup needed.

---

## Tests

```bash
pytest tests/ -v
```

29 tests covering profiling, suggestion logic, and LLM response parsing. No LLM calls required.

---

## Example Questions

Upload `sample_data/sales_sample.csv` and try:

- What are the top 5 products by total revenue? Show me a bar chart.
- Is there a correlation between discount and quantity sold?
- Show me monthly revenue trends as a line chart.
- Which region has the highest average order value?
- Summarise this dataset in one paragraph for my manager.

---

## Project Structure

```
├── app.py
├── analyst.py
├── charts.py
├── profiler.py
├── suggester.py
├── exporter.py
├── loader.py
├── generate_sample_data.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── tests/
│   ├── test_profiler.py
│   └── test_suggester.py
└── sample_data/
    └── sales_sample.csv
```

---

## Roadmap

- [ ] SQL database connections (SQLite, PostgreSQL)
- [ ] Multi-file upload with JOIN suggestions
- [ ] Voice input via whisper.cpp
- [ ] Scheduled report emails

---

## License

MIT
