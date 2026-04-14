"""Streamlit UI — all business logic lives in the other modules."""

import time

import streamlit as st

from analyst import DataAnalyst
from charts import auto_chart_from_query, chart_from_spec, distribution_histogram
from exporter import to_pdf_bytes
from loader import load_dataset
from profiler import profile_dataset
from suggester import suggest_questions

st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0f0f14; color: #e0e0f0; }
    .chat-user { background: #1e1e30; border-left: 3px solid #7c6dfa;
                 padding: 12px; border-radius: 4px; margin: 8px 0; }
    .chat-ai   { background: #1a2620; border-left: 3px solid #6dfabd;
                 padding: 12px; border-radius: 4px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# Session defaults
for key, default in [("chat_history", []), ("dataset", None), ("analyst", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.selectbox("Ollama Model", ["llama3", "mistral", "phi3", "qwen3:1.7b", "qwen2.5:1.5b"])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

    st.divider()
    uploaded = st.file_uploader("📁 Upload Dataset", type=["csv", "xlsx", "json"])

    if uploaded:
        try:
            dataset = load_dataset(uploaded, uploaded.name)
            if st.session_state.dataset is None or st.session_state.dataset.filename != uploaded.name:
                st.session_state.dataset = dataset
                st.session_state.chat_history = []
                st.session_state.analyst = DataAnalyst(df=dataset.df, model=model, temperature=temperature)
            st.success(f"✅ {dataset.row_count:,} rows × {dataset.col_count} cols")
        except Exception as exc:
            st.error(f"Error loading file: {exc}")

# --- Main area ---
st.title("📊 AI Data Analyst Agent")
st.caption("Upload any dataset · Ask in plain English · Get charts + insights · Export report")

if st.session_state.dataset is None:
    st.info("👈 Upload a CSV, Excel, or JSON file in the sidebar to get started.")
    st.markdown(
        "- Ask any question about your data in plain English\n"
        "- Auto-generate bar, line, pie, and scatter charts\n"
        "- Profile data quality column-by-column\n"
        "- Export the full analysis session as a PDF\n"
        "- 100% local — no data leaves your machine"
    )
    st.stop()

dataset = st.session_state.dataset
analyst = st.session_state.analyst

tab_chat, tab_profile, tab_export = st.tabs(["💬 Chat", "🔍 Data Profile", "📤 Export"])

# --- Tab 1: Chat ---
with tab_chat:
    with st.expander("📋 Data Preview", expanded=False):
        st.dataframe(dataset.df.head(20), width="stretch")

    # Suggested questions
    st.subheader("💡 Suggested Questions")
    suggestions = suggest_questions(dataset)
    cols = st.columns(3)
    for i, s in enumerate(suggestions):
        if cols[i % 3].button(s, key=f"sug_{i}", width="stretch"):
            st.session_state["prefill"] = s
            st.session_state["auto_run"] = True
            st.rerun()

    st.divider()

    # Chat history
    for msg in st.session_state.chat_history:
        cls = "chat-user" if msg["role"] == "user" else "chat-ai"
        icon = "🧑" if msg["role"] == "user" else "🤖"
        st.markdown(f'<div class="{cls}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("chart"):
            st.plotly_chart(msg["chart"], width="stretch", key=f"fig_{id(msg)}")

    # Input
    prefill = st.session_state.pop("prefill", None)
    if prefill is not None:
        st.session_state["query_input"] = prefill

    query = st.text_input(
        "Ask anything about your data",
        key="query_input",
        placeholder="e.g. What are the top 5 products by revenue? Show me a bar chart.",
    )

    col_run, col_clear = st.columns([1, 5])
    run_btn = col_run.button("🔍 Analyse", type="primary")
    clear_btn = col_clear.button("🗑️ Clear") if st.session_state.chat_history else False
    auto_run = st.session_state.pop("auto_run", False)

    if clear_btn:
        st.session_state.chat_history = []
        st.rerun()

    if (run_btn or auto_run) and query.strip():
        st.session_state.chat_history.append({"role": "user", "content": query})

        status = st.status("Analysing…", expanded=True)
        with status:
            st.write(f"Sending to **{model}** — this can take a while on CPU.")
            start = time.time()
            result = analyst.query(query)
            elapsed = time.time() - start
            if result.success:
                status.update(label=f"Done in {elapsed:.1f}s", state="complete", expanded=False)
            else:
                status.update(label=f"Failed after {elapsed:.1f}s", state="error", expanded=True)

        if not result.success:
            st.error(f"Agent error: {result.error}")
        else:
            chart_fig = None
            if result.has_chart_spec:
                chart_fig = chart_from_spec(dataset.df, result.chart_spec)
            if chart_fig is None:
                chart_fig = auto_chart_from_query(query, dataset)

            msg = {"role": "assistant", "content": result.answer}
            if chart_fig:
                msg["chart"] = chart_fig
            st.session_state.chat_history.append(msg)

        st.rerun()

# --- Tab 2: Data Profile ---
with tab_profile:
    st.subheader("Data Quality Profile")
    dp = profile_dataset(dataset.df)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Rows", f"{dp.rows:,}")
    k2.metric("Columns", dp.cols)
    k3.metric("Missing", f"{dp.total_missing:,}", f"{dp.missing_pct:.1f}%")
    k4.metric("Duplicates", dp.duplicates)
    k5.metric("Quality", f"{dp.quality_score:.0f}/100")

    st.divider()
    st.dataframe(dp.to_display_df(), width="stretch", hide_index=True)

    if dataset.numeric_cols:
        st.divider()
        st.subheader("Column Distribution")
        col_pick = st.selectbox("Select a numeric column", dataset.numeric_cols)
        st.plotly_chart(distribution_histogram(dataset.df, col_pick), width="stretch")

# --- Tab 3: Export ---
with tab_export:
    st.subheader("Export Session Report")

    if not st.session_state.chat_history:
        st.info("Run some analyses in the Chat tab first, then export here.")
    else:
        st.caption(f"{len(st.session_state.chat_history) // 2} Q&A exchanges ready to export.")
        if st.button("📄 Generate PDF Report"):
            with st.spinner("Building report…"):
                pdf_bytes = to_pdf_bytes(
                    chat_history=st.session_state.chat_history,
                    dataset_name=dataset.filename,
                    row_count=dataset.row_count,
                )
            st.download_button(
                "📥 Download PDF",
                data=pdf_bytes,
                file_name=f"analysis_{dataset.filename.rsplit('.', 1)[0]}.pdf",
                mime="application/pdf",
            )
            st.success("Report ready!")
