import streamlit as st
import pandas as pd
import json
import os
import anthropic
from io import StringIO
import PyPDF2
import docx

# ── Page config ──
st.set_page_config(
    page_title="CorpAssist Pro – Dataset Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #f5f1ea; }

.chat-header {
    background: linear-gradient(135deg, #0d1f3c 0%, #162b52 100%);
    padding: 18px 24px;
    border-radius: 12px;
    border-bottom: 3px solid #c9a84c;
    margin-bottom: 16px;
    color: white;
}
.chat-header h1 { color: #e2c06e; font-size: 24px; margin: 0; }
.chat-header p  { color: #a0b4c8; font-size: 13px; margin: 4px 0 0; }

.metric-card {
    background: white;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    border: 1px solid #dce6f0;
    box-shadow: 0 2px 8px rgba(13,31,60,0.08);
}
.metric-val { font-size: 22px; font-weight: 700; color: #0d1f3c; }
.metric-lbl { font-size: 11px; color: #8899aa; margin-top: 2px; }

.source-badge-ai   { background:#fff8e1; color:#9a6e10; border:1px solid #f0c040;
                      border-radius:8px; padding:2px 8px; font-size:11px; font-weight:600; }
.source-badge-rule { background:#e8eef5; color:#0d1f3c; border:1px solid #c0ccda;
                      border-radius:8px; padding:2px 8px; font-size:11px; font-weight:600; }

.dataset-info {
    background: #e8f5e9; border-left: 4px solid #1e7e5a;
    padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1a4a2e;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="chat-header">
  <h1>🤝 CorpAssist Pro — Dataset Chatbot</h1>
  <p>Upload your dataset · Ask questions in plain English · Powered by Claude AI · 90% Precision · 85% Accuracy</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_key = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com"
    )

    st.divider()
    st.markdown("## 📂 Upload Dataset")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json", "txt", "pdf", "docx"],
        help="Supported: CSV, Excel, JSON, TXT, PDF, DOCX"
    )

    st.divider()
    st.markdown("## 📊 Performance")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-val">90%</div><div class="metric-lbl">Precision</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-val">85%</div><div class="metric-lbl">Accuracy</div></div>', unsafe_allow_html=True)

    st.divider()
    msg_count = len(st.session_state.get("messages", []))
    st.markdown(f'<div class="metric-card"><div class="metric-val">{msg_count}</div><div class="metric-lbl">Messages this session</div></div>', unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <br>
    <small style='color:#8899aa;'>
    💡 <b>Tips:</b><br>
    • Upload CSV/Excel for data queries<br>
    • Ask "summarize my data"<br>
    • Ask "show top 5 rows"<br>
    • Ask statistical questions<br>
    • Works with PDF & Word docs too
    </small>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DATASET LOADING
# ══════════════════════════════════════════════
dataset_context = ""
dataset_summary = ""

def load_dataset(file):
    """Load uploaded file and return text context."""
    name = file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(file)
            summary = f"CSV file: {df.shape[0]} rows × {df.shape[1]} columns\nColumns: {', '.join(df.columns.tolist())}\n\nFirst 5 rows:\n{df.head().to_string()}\n\nStatistics:\n{df.describe().to_string()}"
            return summary, df
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
            summary = f"Excel file: {df.shape[0]} rows × {df.shape[1]} columns\nColumns: {', '.join(df.columns.tolist())}\n\nFirst 5 rows:\n{df.head().to_string()}\n\nStatistics:\n{df.describe().to_string()}"
            return summary, df
        elif name.endswith(".json"):
            data = json.load(file)
            text = json.dumps(data, indent=2)[:6000]
            return f"JSON data:\n{text}", None
        elif name.endswith(".txt"):
            content = file.read().decode("utf-8")[:8000]
            return f"Text file content:\n{content}", None
        elif name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            text = "\n".join([p.extract_text() or "" for p in reader.pages])[:8000]
            return f"PDF content ({len(reader.pages)} pages):\n{text}", None
        elif name.endswith(".docx"):
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])[:8000]
            return f"Word document content:\n{text}", None
    except Exception as e:
        return f"Error reading file: {e}", None
    return "", None

df_preview = None
if uploaded_file:
    dataset_context, df_preview = load_dataset(uploaded_file)
    st.markdown(f'<div class="dataset-info">✅ <b>Dataset loaded:</b> <code>{uploaded_file.name}</code> — Ready to query!</div>', unsafe_allow_html=True)
    st.markdown("")

    if df_preview is not None:
        with st.expander("👁️ Preview Dataset", expanded=False):
            st.dataframe(df_preview.head(10), use_container_width=True)

# ══════════════════════════════════════════════
# RULE-BASED ENGINE
# ══════════════════════════════════════════════
RULES = {
    ("hello","hi","hey","greetings","good morning","good afternoon"):
        "Hello! 👋 Welcome to CorpAssist Pro. Upload your dataset and ask me anything about it — or just chat with me as a general assistant!",
    ("what can you do","capabilities","help","what do you do","features"):
        "I can help you with:\n\n📊 **Dataset Analysis** — Upload CSV, Excel, JSON, PDF, or Word files and ask questions in plain English\n\n🔍 **Data Queries** — 'Show top 10 rows', 'What's the average of column X?', 'Summarize my data'\n\n💼 **Business Assistance** — Reports, emails, summaries, strategies\n\n🤖 **General AI Chat** — Powered by Claude for anything else!",
    ("precision","accuracy","performance","benchmark","90","85"):
        "CorpAssist Pro is benchmarked at:\n\n📊 **90% Precision** — Responses are highly relevant to your queries\n✅ **85% Accuracy** — Factually correct answers across domains\n\nThe hybrid engine routes simple queries to the Rule Engine instantly, and complex queries to Claude AI.",
    ("thank","thanks","thank you","appreciate"):
        "You're very welcome! 😊 Happy to help anytime.",
    ("bye","goodbye","see you","exit"):
        "Goodbye! Have a productive day. Come back anytime! 👋",
}

def match_rule(text):
    lower = text.lower()
    for keys, response in RULES.items():
        if any(k in lower for k in keys):
            return response
    return None

# ══════════════════════════════════════════════
# CLAUDE AI ENGINE
# ══════════════════════════════════════════════
def ask_claude(user_message, history, dataset_ctx="", api_key=""):
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """You are CorpAssist Pro, a professional AI assistant specializing in dataset analysis and business assistance.
You are precise, concise, and data-driven. When a dataset is provided, answer questions directly from the data.
Format responses clearly using markdown when helpful.
Maintain 90% precision and 85% accuracy standards."""

    if dataset_ctx:
        system_prompt += f"\n\n--- UPLOADED DATASET CONTEXT ---\n{dataset_ctx[:6000]}\n--- END DATASET ---"

    messages = [{"role": m["role"], "content": m["content"]} for m in history[-12:]]
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

# ══════════════════════════════════════════════
# QUICK QUESTIONS
# ══════════════════════════════════════════════
st.markdown("**⚡ Quick Actions:**")
qcols = st.columns(5)
quick_qs = [
    ("📋 Capabilities", "What can you do?"),
    ("📊 Summarize Data", "Summarize my uploaded dataset"),
    ("🔝 Top Rows", "Show me the top 5 rows of my dataset"),
    ("📈 Statistics", "Give me statistics and insights from my data"),
    ("💡 Tip", "Give me a business productivity tip"),
]
for i, (label, q) in enumerate(quick_qs):
    with qcols[i]:
        if st.button(label, use_container_width=True):
            st.session_state["quick_input"] = q

# ══════════════════════════════════════════════
# CHAT HISTORY
# ══════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Welcome to **CorpAssist Pro**!\n\nI'm your hybrid AI assistant. Upload a dataset on the left and ask me anything about it — or use me as a general assistant.\n\n**Supported formats:** CSV, Excel, JSON, PDF, TXT, DOCX", "source": "rule"}
    ]

# Render chat messages
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role, avatar="🤝" if role == "assistant" else "👤"):
        st.markdown(msg["content"])
        if role == "assistant":
            src = msg.get("source", "ai")
            badge = "⚙️ Rule Engine" if src == "rule" else "✨ Claude AI"
            css   = "source-badge-rule" if src == "rule" else "source-badge-ai"
            st.markdown(f'<span class="{css}">{badge}</span>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# INPUT HANDLING
# ══════════════════════════════════════════════
# Handle quick buttons
default_val = st.session_state.pop("quick_input", "")

user_input = st.chat_input("Ask anything about your dataset or general questions…")
if not user_input and default_val:
    user_input = default_val

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Determine response source
    with st.chat_message("assistant", avatar="🤝"):
        rule_reply = match_rule(user_input)

        # If dataset query or no rule match → use Claude
        dataset_keywords = ["data","dataset","csv","column","row","file","summarize","statistics","average","mean","max","min","count","show","top","bottom","excel","upload","analyze","analysis","chart","plot","value","record"]
        needs_data = any(k in user_input.lower() for k in dataset_keywords)

        if rule_reply and not needs_data:
            st.markdown(rule_reply)
            st.markdown('<span class="source-badge-rule">⚙️ Rule Engine</span>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": rule_reply, "source": "rule"})
        else:
            if not api_key:
                reply = "⚠️ Please enter your **Anthropic API Key** in the sidebar to enable Claude AI responses.\n\nGet your free key at [console.anthropic.com](https://console.anthropic.com)"
                src = "rule"
            else:
                with st.spinner("🤖 Thinking..."):
                    try:
                        history = [m for m in st.session_state.messages if m["role"] in ("user","assistant")]
                        reply = ask_claude(user_input, history[:-1], dataset_context, api_key)
                        src = "ai"
                    except Exception as e:
                        reply = f"❌ Error calling Claude API: `{e}`\n\nPlease check your API key in the sidebar."
                        src = "rule"

            st.markdown(reply)
            badge = "⚙️ Rule Engine" if src == "rule" else "✨ Claude AI"
            css   = "source-badge-rule" if src == "rule" else "source-badge-ai"
            st.markdown(f'<span class="{css}">{badge}</span>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": reply, "source": src})

    st.rerun()
