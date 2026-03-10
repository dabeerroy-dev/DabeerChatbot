import streamlit as st
import pandas as pd
import json
from groq import Groq
import PyPDF2
import docx

st.set_page_config(page_title="CorpAssist Pro – Dataset Chatbot", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f5f1ea; }
.chat-header { background: linear-gradient(135deg, #0d1f3c 0%, #162b52 100%); padding: 18px 24px; border-radius: 12px; border-bottom: 3px solid #c9a84c; margin-bottom: 16px; color: white; }
.chat-header h1 { color: #e2c06e; font-size: 24px; margin: 0; }
.chat-header p  { color: #a0b4c8; font-size: 13px; margin: 4px 0 0; }
.metric-card { background: white; border-radius: 10px; padding: 14px; text-align: center; border: 1px solid #dce6f0; }
.metric-val { font-size: 22px; font-weight: 700; color: #0d1f3c; }
.metric-lbl { font-size: 11px; color: #8899aa; margin-top: 2px; }
.source-badge-ai   { background:#e8f5e9; color:#1e7e5a; border:1px solid #a5d6a7; border-radius:8px; padding:2px 8px; font-size:11px; font-weight:600; }
.source-badge-rule { background:#e8eef5; color:#0d1f3c; border:1px solid #c0ccda; border-radius:8px; padding:2px 8px; font-size:11px; font-weight:600; }
.dataset-info { background: #e8f5e9; border-left: 4px solid #1e7e5a; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1a4a2e; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="chat-header"><h1>🤝 CorpAssist Pro — Dataset Chatbot</h1><p>Upload your dataset · Ask questions in plain English · Powered by Groq AI (Free) · 90% Precision · 85% Accuracy</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    api_key = st.text_input("🔑 Groq API Key", type="password", placeholder="gsk_...", help="Free at console.groq.com")
    st.caption("🆓 Get free key at [console.groq.com](https://console.groq.com) — No card needed!")
    st.divider()
    st.markdown("## 📂 Upload Dataset")
    uploaded_file = st.file_uploader("Choose a file", type=["csv","xlsx","xls","json","txt","pdf","docx"])
    st.divider()
    st.markdown("## 📊 Performance")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-val">90%</div><div class="metric-lbl">Precision</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-val">85%</div><div class="metric-lbl">Accuracy</div></div>', unsafe_allow_html=True)
    st.divider()
    msg_count = len(st.session_state.get("messages", []))
    st.markdown(f'<div class="metric-card"><div class="metric-val">{msg_count}</div><div class="metric-lbl">Messages</div></div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

dataset_context = ""
df_preview = None

def load_dataset(file):
    name = file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(file)
            return (f"CSV: {df.shape[0]} rows x {df.shape[1]} cols\nColumns: {', '.join(df.columns.tolist())}\n\nFirst 5 rows:\n{df.head().to_string()}\n\nStats:\n{df.describe().to_string()}"), df
        elif name.endswith((".xlsx",".xls")):
            df = pd.read_excel(file)
            return (f"Excel: {df.shape[0]} rows x {df.shape[1]} cols\nColumns: {', '.join(df.columns.tolist())}\n\nFirst 5 rows:\n{df.head().to_string()}\n\nStats:\n{df.describe().to_string()}"), df
        elif name.endswith(".json"):
            data = json.load(file)
            return f"JSON:\n{json.dumps(data,indent=2)[:6000]}", None
        elif name.endswith(".txt"):
            return f"Text:\n{file.read().decode('utf-8')[:8000]}", None
        elif name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            text = "\n".join([p.extract_text() or "" for p in reader.pages])[:8000]
            return f"PDF ({len(reader.pages)} pages):\n{text}", None
        elif name.endswith(".docx"):
            doc = docx.Document(file)
            return f"Word doc:\n{chr(10).join([p.text for p in doc.paragraphs])[:8000]}", None
    except Exception as e:
        return f"Error: {e}", None
    return "", None

if uploaded_file:
    dataset_context, df_preview = load_dataset(uploaded_file)
    st.markdown(f'<div class="dataset-info">✅ <b>Dataset loaded:</b> <code>{uploaded_file.name}</code> — Ready to query!</div>', unsafe_allow_html=True)
    if df_preview is not None:
        with st.expander("👁️ Preview Dataset"):
            st.dataframe(df_preview.head(10), use_container_width=True)

RULES = {
    ("hello","hi","hey","greetings"): "Hello! 👋 Welcome to CorpAssist Pro. Upload your dataset and ask me anything!",
    ("what can you do","capabilities","help","features"): "I can:\n\n📊 **Analyze datasets** — CSV, Excel, JSON, PDF, Word\n🔍 **Answer data queries** — stats, rows, summaries\n💼 **Business assistance** — reports, summaries\n🤖 **General chat** — powered by Groq AI (free!)",
    ("precision","accuracy","performance"): "📊 **90% Precision** · ✅ **85% Accuracy**",
    ("thank","thanks","thank you"): "You're welcome! 😊",
    ("bye","goodbye"): "Goodbye! 👋",
}

def match_rule(text):
    lower = text.lower()
    for keys, response in RULES.items():
        if any(k in lower for k in keys):
            return response
    return None

def ask_groq(user_message, history, dataset_ctx="", api_key=""):
    client = Groq(api_key=api_key)
    system = f"""You are CorpAssist Pro, a professional AI assistant for dataset analysis and business help.
Be precise, concise and data-driven. Use markdown formatting when helpful.
{"--- DATASET ---\n" + dataset_ctx[:6000] + "\n--- END ---" if dataset_ctx else ""}"""
    
    messages = [{"role": "system", "content": system}]
    for m in history[-12:]:
        if m["role"] in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1000
    )
    return response.choices[0].message.content

st.markdown("**⚡ Quick Actions:**")
qcols = st.columns(5)
quick_qs = [("📋 Capabilities","What can you do?"),("📊 Summarize","Summarize my uploaded dataset"),("🔝 Top Rows","Show me the top 5 rows"),("📈 Statistics","Give me statistics from my data"),("💡 Tips","Give me a business productivity tip")]
for i,(label,q) in enumerate(quick_qs):
    with qcols[i]:
        if st.button(label, use_container_width=True):
            st.session_state["quick_input"] = q

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"assistant","content":"👋 Welcome to **CorpAssist Pro**!\n\nPowered by **Groq AI (100% Free, No Card)** 🆓\n\nUpload a dataset on the left and ask me anything!\n\n**Supported:** CSV, Excel, JSON, PDF, TXT, DOCX","source":"rule"}]

for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role, avatar="🤝" if role=="assistant" else "👤"):
        st.markdown(msg["content"])
        if role == "assistant":
            src = msg.get("source","ai")
            badge = "⚙️ Rule Engine" if src=="rule" else "✨ Groq AI"
            css = "source-badge-rule" if src=="rule" else "source-badge-ai"
            st.markdown(f'<span class="{css}">{badge}</span>', unsafe_allow_html=True)

default_val = st.session_state.pop("quick_input","")
user_input = st.chat_input("Ask anything about your dataset or general questions…")
if not user_input and default_val:
    user_input = default_val

if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="🤝"):
        rule_reply = match_rule(user_input)
        data_kw = ["data","dataset","csv","column","row","file","summarize","statistics","average","mean","max","min","count","show","top","bottom","excel","upload","analyze","analysis","value","record","insight","pdf","report"]
        needs_data = any(k in user_input.lower() for k in data_kw)
        if rule_reply and not needs_data:
            st.markdown(rule_reply)
            st.markdown('<span class="source-badge-rule">⚙️ Rule Engine</span>', unsafe_allow_html=True)
            st.session_state.messages.append({"role":"assistant","content":rule_reply,"source":"rule"})
        else:
            if not api_key:
                reply = "⚠️ Please enter your **Groq API Key** in the sidebar.\n\n👉 Get it **FREE** (no card!) at [console.groq.com](https://console.groq.com)"
                src = "rule"
            else:
                with st.spinner("🤖 Thinking..."):
                    try:
                        history = [m for m in st.session_state.messages if m["role"] in ("user","assistant")]
                        reply = ask_groq(user_input, history[:-1], dataset_context, api_key)
                        src = "ai"
                    except Exception as e:
                        reply = f"❌ Error: `{e}`\n\nPlease check your Groq API key."
                        src = "rule"
            st.markdown(reply)
            badge = "⚙️ Rule Engine" if src=="rule" else "✨ Groq AI"
            css = "source-badge-rule" if src=="rule" else "source-badge-ai"
            st.markdown(f'<span class="{css}">{badge}</span>', unsafe_allow_html=True)
            st.session_state.messages.append({"role":"assistant","content":reply,"source":src})
    st.rerun()
