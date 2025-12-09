import streamlit as st
import json
import re
import pandas as pd
from groq import Groq
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Prompt Architect ELITE", 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- SECURITY LOCK ---
# To let friends use it, give them this password.
APP_PASSWORD = "password123" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == APP_PASSWORD:
        st.session_state.authenticated = True
    else:
        st.error("Wrong password")

if not st.session_state.authenticated:
    st.markdown("### 🔒 Login Required")
    st.text_input("Enter Access Password:", type="password", key="password_input", on_change=check_password)
    st.caption("Contact the admin for access.")
    st.stop()

# --- SESSION STATE INITIALIZATION ---
if "master_prompt" not in st.session_state: st.session_state.master_prompt = ""
if "vault" not in st.session_state: st.session_state.vault = []
if "critic_feedback" not in st.session_state: st.session_state.critic_feedback = ""
if "voice_text" not in st.session_state: st.session_state.voice_text = "" # New for voice

# --- LOCAL DATABASE FUNCTIONS ---
DB_FILE = "prompt_vault.json"

def load_vault():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_to_vault(prompt, tags, score="N/A"):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prompt": prompt,
        "tags": tags,
        "score": score
    }
    vault = load_vault()
    vault.insert(0, entry)
    with open(DB_FILE, "w") as f: json.dump(vault, f, indent=4)
    return vault

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .stTextArea>div>div>textarea {
        background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 15px; font-family: 'Inter', sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.2em; font-weight: 600;
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        color: white; border: none; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); color: #00e5ff; }
    .critic-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .feature-card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Architect ELITE")
    api_key = st.text_input("Groq API Key:", type="password", placeholder="gsk_...")
    
    st.divider()
    mode = st.radio("Navigation", [
        "🏗️ Master Architect", 
        "⚔️ Battle Arena", 
        "🔄 Reverse Engineer", 
        "💾 Prompt Vault",
        "📘 Documentation"
    ])
    
    st.divider()
    model = st.selectbox("Architect Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])

# ==========================================
# TOOL 1: THE MASTER ARCHITECT
# ==========================================
if mode == "🏗️ Master Architect":
    st.title("🏗️ The Master Architect")
    
    # ADVANCED INPUTS
    with st.expander("📂 Advanced Inputs (Voice / CSV Examples)"):
        tab_voice, tab_csv = st.tabs(["🎤 Voice Input", "📚 Few-Shot CSV"])
        
        # --- REAL VOICE TRANSCRIPTION LOGIC ---
        with tab_voice:
            audio_val = st.audio_input("Record your idea:")
            if audio_val and api_key:
                client = Groq(api_key=api_key)
                with st.spinner("Transcribing audio via Whisper..."):
                    try:
                        # Groq needs a filename to process the buffer
                        audio_val.name = "input.wav" 
                        transcription = client.audio.transcriptions.create(
                            file=(audio_val.name, audio_val.read()), 
                            model="whisper-large-v3-turbo", # The fast audio model
                            response_format="text"
                        )
                        st.session_state.voice_text = transcription
                        st.success("Transcribed! Check the 'Core Task' box below.")
                    except Exception as e:
                        st.error(f"Audio Error: {e}")

        with tab_csv:
            uploaded_file = st.file_uploader("Upload CSV (Columns: 'Input', 'Output')", type=["csv"])
            few_shot_data = ""
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'Input' in df.columns and 'Output' in df.columns:
                        for index, row in df.iterrows():
                            few_shot_data += f"<example>\nUSER: {row['Input']}\nAI: {row['Output']}\n</example>\n"
                        st.success(f"Loaded {len(df)} examples!")
                except: st.error("CSV Error. Ensure columns are 'Input' and 'Output'.")

    # MAIN INPUTS
    col1, col2 = st.columns([2, 1])
    with col1:
        # If voice text exists, use it as default value
        default_val = st.session_state.voice_text if st.session_state.voice_text else ""
        raw_prompt = st.text_area("Core Task:", height=150, value=default_val, placeholder="e.g., 'Write a python script to scrape prices'")
    with col2:
        context_data = st.text_area("Context / Constraints:", height=150, placeholder="e.g., 'Audience is beginners. Output JSON.'")
        
    domain_mode = st.selectbox("Domain Strategy", ["General", "👨‍💻 Coding", "✍️ Creative Writing", "📊 Data Analysis"], index=0)
    target_ai = st.radio("Target AI Structure", ["Gemini (XML)", "GPT-5 (Markdown)"], horizontal=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: run_critic = st.checkbox("⚖️ Run Critic Agent", value=True)
    with c2: run_diet = st.checkbox("📉 Token Diet (Compress)", value=False)
    with c3: extract_vars = st.checkbox("🧩 Variable Wizard", value=True)

    if st.button("⚡ Architect Master Prompt", type="primary"):
        if not api_key:
            st.error("Need Groq API Key")
        else:
            client = Groq(api_key=api_key)
            
            # SYSTEM PROMPT BUILDER
            domain_instructions = ""
            if "Coding" in domain_mode: domain_instructions = "Include error handling, comments, and efficiency checks."
            if "Creative" in domain_mode: domain_instructions = "Use 'Show Don't Tell', avoid AI clichés, ensure unique voice."
            
            struct_instr = ""
            if "Gemini" in target_ai:
                struct_instr = "Use XML tags (<role>, <task>, <constraints>)."
            else:
                struct_instr = "Use Markdown headers (# Identity, # Steps)."

            full_system = f"""
            You are an Elite Prompt Engineer.
            Goal: Rewrite user request into a Master Prompt.
            Domain: {domain_mode}. Rules: {domain_instructions}
            Structure: {struct_instr}
            If CSV examples provided: {few_shot_data}
            """
            
            with st.spinner("Architecting..."):
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role":"system", "content": full_system}, {"role":"user", "content": f"Task: {raw_prompt} Context: {context_data}"}],
                    temperature=0.6
                )
                draft_prompt = resp.choices[0].message.content

            # CRITIC LOOP
            if run_critic:
                with st.spinner("⚖️ Critic is reviewing..."):
                    critic_resp = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role":"system", "content": "Critique this prompt. Rate 0-10. If < 9, improve it. Output ONLY the improved version."},
                            {"role":"user", "content": draft_prompt}
                        ]
                    )
                    st.session_state.master_prompt = critic_resp.choices[0].message.content
                    st.session_state.critic_feedback = "Critic improved clarity & constraints."
            else:
                st.session_state.master_prompt = draft_prompt

            # TOKEN DIET
            if run_diet:
                with st.spinner("📉 Compressing tokens..."):
                    diet_resp = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role":"system", "content": "Compress this prompt by 30% without losing meaning. Remove fluff."},
                            {"role":"user", "content": st.session_state.master_prompt}
                        ]
                    )
                    st.session_state.master_prompt = diet_resp.choices[0].message.content

    # DISPLAY RESULTS
    if st.session_state.master_prompt:
        st.divider()
        if st.session_state.critic_feedback:
            st.markdown(f"<div class='critic-box'><b>⚖️ Critic Report:</b> {st.session_state.critic_feedback}</div>", unsafe_allow_html=True)
        
        col_res, col_acts = st.columns([2, 1])
        with col_res:
            st.subheader("💎 Final Master Prompt")
            st.text_area("Copy this:", value=st.session_state.master_prompt, height=500)
        with col_acts:
            st.subheader("🛠️ Tools")
            py_code = f"""from groq import Groq\nclient = Groq(api_key="KEY")\nprompt = \"\"\"{st.session_state.master_prompt}\"\"\"\nprint(client.chat.completions.create(model="{model}", messages=[{{"role":"user", "content":prompt}}]).choices[0].message.content)"""
            st.download_button("🐍 Export Python Script", py_code, file_name="agent.py")
            if st.button("💾 Save to Vault"):
                save_to_vault(st.session_state.master_prompt, domain_mode)
                st.success("Saved!")
            if extract_vars:
                vars = re.findall(r'\{\{(.*?)\}\}', st.session_state.master_prompt)
                if vars:
                    st.markdown("### 🧩 Variable Wizard")
                    for v in vars: st.text_input(f"Value for {v}", key=f"var_{v}")

# ==========================================
# TOOL 2: BATTLE ARENA
# ==========================================
elif mode == "⚔️ Battle Arena":
    st.title("⚔️ Model Battle Arena")
    st.caption("Test your prompt against two models simultaneously to check robustness.")
    
    arena_prompt = st.text_area("Enter Prompt to Test:", height=150, value=st.session_state.master_prompt)
    
    col_a, col_b = st.columns(2)
    with col_a: model_a = st.selectbox("Fighter A", ["llama-3.3-70b-versatile"], index=0)
    with col_b: model_b = st.selectbox("Fighter B", ["mixtral-8x7b-32768"], index=0)
    
    if st.button("⚔️ FIGHT!"):
        if not api_key: st.error("Need Key")
        else:
            client = Groq(api_key=api_key)
            with col_a:
                with st.spinner(f"{model_a} attacking..."):
                    try:
                        resp_a = client.chat.completions.create(model=model_a, messages=[{"role":"user", "content": arena_prompt}])
                        st.success(f"{model_a} Result")
                        st.markdown(resp_a.choices[0].message.content)
                    except Exception as e: st.error(e)
            with col_b:
                with st.spinner(f"{model_b} attacking..."):
                    try:
                        resp_b = client.chat.completions.create(model=model_b, messages=[{"role":"user", "content": arena_prompt}])
                        st.info(f"{model_b} Result")
                        st.markdown(resp_b.choices[0].message.content)
                    except Exception as e: st.error(e)

# ==========================================
# TOOL 3: REVERSE ENGINEER
# ==========================================
elif mode == "🔄 Reverse Engineer":
    st.title("🔄 De-Compiler")
    st.caption("Paste a great AI response to find out the prompt that likely created it.")
    
    output_text = st.text_area("Paste the AI Output here:", height=300)
    
    if st.button("🔍 Reverse Engineer"):
        if not api_key: st.error("Need Key")
        else:
            client = Groq(api_key=api_key)
            system = "Reverse-engineer the prompt that likely created this text. Identify constraints, tone, and persona."
            resp = client.chat.completions.create(model=model, messages=[{"role":"system", "content": system}, {"role":"user", "content": output_text}])
            st.markdown("### 🕵️ Likely Source Prompt")
            st.code(resp.choices[0].message.content)

# ==========================================
# TOOL 4: PROMPT VAULT
# ==========================================
elif mode == "💾 Prompt Vault":
    st.title("💾 The Vault")
    st.caption("Your library of saved Master Prompts.")
    vault = load_vault()
    if not vault: st.info("Vault is empty.")
    for i, item in enumerate(vault):
        with st.expander(f"{item['timestamp']} | {item['tags']}"):
            st.code(item['prompt'])

# ==========================================
# TOOL 5: DOCUMENTATION
# ==========================================
elif mode == "📘 Documentation":
    st.title("📘 Feature Documentation")
    st.markdown("### How to use the Elite Suite")
    
    st.markdown("""
    <div class="feature-card">
    <h4>🏗️ Master Architect</h4>
    <p>The core engine. Uses 'Meta-Prompting' to rewrite lazy requests into professional engineering formats.</p>
    <ul>
        <li><b>Domain Strategy:</b> Select 'Coding' for error handling, 'Creative' for tone.</li>
        <li><b>Target AI:</b> Switches between XML (Gemini) and Markdown (GPT-5).</li>
        <li><b>🎤 Voice Input:</b> Record your ideas verbally; the AI transcribes them via Whisper.</li>
        <li><b>📚 CSV Loader:</b> Upload spreadsheets to teach the AI by example (Few-Shot).</li>
    </ul>
    </div>
    
    <div class="feature-card">
    <h4>⚖️ The Critic Agent</h4>
    <p>An autonomous AI agent that reviews your prompt <i>before</i> you see it. It checks for clarity, safety, and missing constraints, then auto-fixes it.</p>
    </div>

    <div class="feature-card">
    <h4>📉 Token Diet</h4>
    <p>Enterprise optimization. Compresses the prompt by ~30% by removing fluff words (like 'please', 'kindly'), saving money on API costs.</p>
    </div>

    <div class="feature-card">
    <h4>🧩 Variable Wizard</h4>
    <p>Automatically scans for placeholders like <code>{{name}}</code> and creates input fields. Crucial for building templates for automation (Make/Zapier).</p>
    </div>

    <div class="feature-card">
    <h4>⚔️ Battle Arena</h4>
    <p>The ultimate test. Runs your prompt against two different AI models (e.g., Llama 3 vs Mixtral) simultaneously. If one fails, your prompt isn't robust enough.</p>
    </div>
    
    <div class="feature-card">
    <h4>🔄 Reverse Engineer</h4>
    <p>The learning tool. Paste a great email or code block you found, and this tool will deduce the prompt used to create it.</p>
    </div>
    """, unsafe_allow_html=True)


    