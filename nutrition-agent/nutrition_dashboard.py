"""
🥗 Nutrition Dashboard - Interfaccia Grafica per Nutrition Agent
=================================================================

Dashboard Streamlit per gestire piano alimentare personalizzato.

Features:
- Setup profilo utente
- Generazione piano giornaliero/settimanale
- Visualizzazione ricette con ingredienti
- Lista della spesa automatica
- Tracking nutrizionale
- Suggerimenti AI personalizzati

Autore: Antonio Mainenti
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Import nutrition agent
sys.path.insert(0, str(Path(__file__).parent))
from nutrition_agent import (
    NutritionAgent, UserProfile, MealType, ActivityLevel, 
    DietaryGoal, create_sample_profile
)

# Import datapizza
sys.path.insert(0, str(Path(__file__).parent.parent / "datapizza-ai-core"))
# Add OpenAI-like and Google client packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "datapizza-ai-clients" / "datapizza-ai-clients-openai-like"))
sys.path.insert(0, str(Path(__file__).parent.parent / "datapizza-ai-clients" / "datapizza-ai-clients-google"))

# Page config
st.set_page_config(
    page_title="🥗 Nutrition Agent - Verdure & Benessere",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Small factory to build LLM client from settings
def create_llm_client(provider: str, api_key: str | None, model: str, base_url: str | None):
    provider = (provider or "google").lower()
    if provider == "google":
        if not api_key:
            raise ValueError("Manca la API key per Google. Inseriscila nella sidebar.")
        # Lazy import to avoid import errors when package not present
        from datapizza.clients.google import GoogleClient  # type: ignore
        return GoogleClient(model=model or "gemini-2.0-flash-exp", api_key=api_key)

    # OpenAI-compatible providers (free/cheap tiers): OpenRouter, Groq, DeepSeek, Together, Local Ollama
    # Defaults per provider
    defaults = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": model or "meta-llama/llama-3.1-8b-instruct:free",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "model": model or "llama-3.1-8b-instant",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "model": model or "deepseek-chat",
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "model": model or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "model": model or "llama3.2:3b",
        },
        "openai-like": {
            "base_url": base_url or "",
            "model": model or "gpt-4o-mini",
        },
    }

    key = provider if provider in defaults else "openai-like"
    cfg = defaults[key]
    base = base_url or cfg.get("base_url")
    mdl = cfg.get("model")

    # Ollama non richiede API key
    if provider == "ollama":
        from datapizza.clients.openai_like import OpenAILikeClient  # type: ignore
        return OpenAILikeClient(api_key=api_key or "ollama", model=mdl, base_url=base)

    if not api_key:
        raise ValueError("Manca la API key per il provider selezionato. Inseriscila nella sidebar.")
    from datapizza.clients.openai_like import OpenAILikeClient  # type: ignore
    return OpenAILikeClient(api_key=api_key, model=mdl, base_url=base)

# Custom CSS - Tema Verdure Stagionali Allegro
st.markdown("""
<style>
    /* Sfondo generale con pattern verdure */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%);
    }
    
    /* Header principale - Colori verdure di stagione */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 30%, #66BB6A 60%, #81C784 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Card pasti - Colori vegetali */
    .meal-card {
        background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
        padding: 1.5rem;
        border-left: 5px solid #689F38;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(104, 159, 56, 0.1);
        transition: transform 0.2s;
    }
    
    .meal-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(104, 159, 56, 0.2);
    }
    
    /* Card giorno workout - Colore arancio/rosso peperoni */
    .workout-day {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left-color: #FF6F00;
    }
    
    /* Metric cards - Palette verdure */
    .metric-card {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
    }
    
    .metric-card-alt {
        background: linear-gradient(135deg, #FFA726 0%, #FF7043 100%);
    }
    
    .metric-card-protein {
        background: linear-gradient(135deg, #8D6E63 0%, #6D4C41 100%);
    }
    
    /* Sidebar - Tema foglie verdi */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #a5d6a7 0%, #c8e6c9 100%);
    }
    
    /* Bottoni - Colori vivaci verdure */
    .stButton > button {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        transform: scale(1.05);
    }
    
    /* Tab - Colori stagionali */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #e8f5e9;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #2E7D32;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
        color: white !important;
        border-radius: 6px;
    }
    
    /* Expander - Tema verdure */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #c8e6c9 0%, #a5d6a7 100%);
        border-radius: 8px;
        color: #1B5E20;
        font-weight: 600;
    }
    
    /* Success/Info boxes - Colori vegetali */
    .stSuccess {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
    }
    
    .stInfo {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
    }
    
    /* Emoji decorativi */
    .veggie-emoji {
        font-size: 2rem;
        animation: bounce 2s ease-in-out infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
</style>
""", unsafe_allow_html=True)

# Header con emoji verdure animate
st.markdown('''
<div style="text-align: center; margin-bottom: 2rem;">
    <span class="veggie-emoji">🥬</span>
    <span class="veggie-emoji">🥦</span>
    <span class="veggie-emoji">🌶️</span>
    <span class="veggie-emoji">🥕</span>
    <span class="veggie-emoji">🍆</span>
    <span class="veggie-emoji">🥒</span>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="main-header">🥗 Nutrition Agent - Il Tuo Nutrizionista Verde</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #558B2F; font-size: 1.2rem; margin-top: -1rem;">🌱 Alimentazione Sana, Stagionale e Sostenibile 🌱</p>', unsafe_allow_html=True)

# Emoji verdure di stagione per mese
seasonal_emojis = {
    "gennaio": "❄️ 🥬 🥦 🫑 🧅",
    "febbraio": "❄️ 🥬 🫑 🧄 🥕",
    "marzo": "🌸 🥬 🥦 🫛 🥕",
    "aprile": "🌸 🥬 🫛 🥕 🌶️",
    "maggio": "🌻 🥒 🍅 🥬 🫛",
    "giugno": "☀️ 🍅 🥒 🫑 🥬",
    "luglio": "☀️ 🍅 🥒 🍆 🫑",
    "agosto": "☀️ 🍅 🥒 🍆 🫑",
    "settembre": "🍂 🍅 🍆 🫑 🥦",
    "ottobre": "🍂 🎃 🥦 🥬 🍄",
    "novembre": "🍂 🎃 🥦 🥬 🍄",
    "dicembre": "❄️ 🥦 🥬 🫑 🎄"
}
current_month = datetime.now().strftime("%B").lower()
month_map = {
    "january": "gennaio", "february": "febbraio", "march": "marzo",
    "april": "aprile", "may": "maggio", "june": "giugno",
    "july": "luglio", "august": "agosto", "september": "settembre",
    "october": "ottobre", "november": "novembre", "december": "dicembre"
}
current_month_it = month_map.get(current_month, "novembre")
st.markdown(f'<p style="text-align: center; font-size: 1.5rem;">{seasonal_emojis.get(current_month_it, "🥬 🥦 🥕")}</p>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align: center; color: #666;">🍽️ Il tuo assistente AI per alimentazione sana e personalizzata - Stagione: {current_month_it.title()}</p>', unsafe_allow_html=True)

# Initialize session state
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None
if 'weekly_plan' not in st.session_state:
    st.session_state.weekly_plan = None

# Auto-carica profilo Antonio se non c'è profilo
if st.session_state.profile is None:
    try:
        from profile_antonio import create_antonio_profile
        st.session_state.profile = create_antonio_profile()
        
        # Inizializza anche l'agent
        if st.session_state.agent is None:
            # Leggi preferenze provider da sessione (fallback Ollama per essere gratuito di default)
            provider = st.session_state.get("llm_provider", "ollama")
            model = st.session_state.get("llm_model", "llama3.2:3b")
            base_url = st.session_state.get("llm_base_url", "http://localhost:11434/v1")
            api_key = os.getenv("GOOGLE_API_KEY") if provider == "google" else os.getenv("API_KEY")
            if api_key or provider == "ollama":
                try:
                    client = create_llm_client(provider, api_key, model or "", base_url)
                    st.session_state.agent = NutritionAgent(client, st.session_state.profile)
                except Exception as e:
                    st.error(f"⚠️ Errore inizializzazione agent con provider '{provider}': {e}")
                    st.info("💡 Controlla la configurazione nella sidebar o ricarica la pagina.")
    except ImportError:
        pass  # Se profile_antonio non esiste, lascia che l'utente lo configuri manualmente

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    # Provider selection
    st.subheader("🤖 Modello LLM")
    provider = st.selectbox(
        "Provider",
        ["ollama", "google", "openrouter", "groq", "deepseek", "together"],
        index=["ollama", "google", "openrouter", "groq", "deepseek", "together"].index(st.session_state.get("llm_provider", "ollama"))
    )
    st.session_state.llm_provider = provider

    defaults = {
        "ollama": {"model": "llama3.2:3b", "base_url": "http://localhost:11434/v1"},
        "google": {"model": "gemini-2.0-flash-exp", "base_url": ""},
        "openrouter": {"model": "meta-llama/llama-3.1-8b-instruct:free", "base_url": "https://openrouter.ai/api/v1"},
        "groq": {"model": "llama-3.1-8b-instant", "base_url": "https://api.groq.com/openai/v1"},
        "deepseek": {"model": "deepseek-chat", "base_url": "https://api.deepseek.com"},
        "together": {"model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "base_url": "https://api.together.xyz/v1"},
    }
    def_val = defaults.get(provider, defaults["google"]) 
    model = st.text_input("Modello", value=st.session_state.get("llm_model", def_val["model"]))
    st.session_state.llm_model = model
    base_url = st.text_input("Base URL (se richiesto)", value=st.session_state.get("llm_base_url", def_val["base_url"]))
    st.session_state.llm_base_url = base_url

    # Check API key (Google o generica)
    api_key_env = os.getenv("GOOGLE_API_KEY") if provider == "google" else os.getenv("API_KEY")
    if provider == "ollama":
        st.info("🖥️ Ollama non richiede API key. Assicurati che Ollama giri su localhost:11434 e che il modello sia installato (es: `ollama pull llama3.1:8b`).")
    elif not api_key_env:
        st.error("❌ API key mancante. Inseriscila nel pannello qui sotto e salva.")
    else:
        st.success("✅ API Key presente nelle variabili d'ambiente")

    # Permetti aggiornamento della API key se scaduta/invalid
    with st.expander("🔑 Configura/aggiorna API Key", expanded=not bool(api_key_env)):
        label = "GOOGLE_API_KEY" if provider == "google" else "API_KEY"
        new_key = st.text_input(f"Inserisci nuova {label}", type="password", value=api_key_env or "")
        if st.button("💾 Salva API Key"):
            # Aggiorna .env e variabile d'ambiente
            env_path = Path(__file__).parent / ".env"
            try:
                # Carica contenuto esistente se presente
                env_lines = []
                if env_path.exists():
                    env_lines = env_path.read_text().splitlines()
                # Rimuovi eventuali righe precedenti
                env_lines = [l for l in env_lines if not (l.startswith("GOOGLE_API_KEY=") or l.startswith("API_KEY="))]
                if provider == "google":
                    env_lines.append(f"GOOGLE_API_KEY={new_key}")
                else:
                    env_lines.append(f"API_KEY={new_key}")
                env_path.write_text("\n".join(env_lines))
            except Exception:
                pass

            if provider == "google":
                os.environ["GOOGLE_API_KEY"] = new_key
            else:
                os.environ["API_KEY"] = new_key
            # Reinizializza client
            try:
                client = create_llm_client(provider, new_key, model, base_url)
                if st.session_state.profile:
                    st.session_state.agent = NutritionAgent(client, st.session_state.profile)
                st.success("✅ API Key aggiornata e client reinizializzato")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nell'inizializzazione client: {e}")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📍 Navigazione")
    page = st.radio(
        "Seleziona sezione:",
        ["🏠 Home", "👤 Profilo", "📅 Piano Giornaliero", "📆 Piano Settimanale", 
         "🔍 Cerca Ricette", "⏱️ Tabata Timer", "📊 Analisi", "⚙️ Impostazioni"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    if st.session_state.agent:
        st.subheader("📈 Stats Rapide")
        history = st.session_state.agent.meal_history
        st.metric("Piani generati", len(history))
        st.metric("Ricette totali", sum(len(day.get("meals", [])) for day in history))

# ============================================================================
# HOME PAGE
# ============================================================================
if page == "🏠 Home":
    st.header("🏠 Benvenuto nel tuo Nutrition Agent!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 Features
        - Piani pasto personalizzati
        - Ricette stagionali
        - Adattamento allenamento
        - Lista spesa automatica
        """)
    
    with col2:
        st.markdown("""
        ### 🌟 Intelligenza AI
        - Gemini 2.0 Flash
        - Apprendimento preferenze
        - Suggerimenti real-time
        - Analisi nutrizionale
        """)
    
    with col3:
        st.markdown("""
        ### 📱 Workflow
        1. Configura profilo
        2. Genera piano
        3. Segui ricette
        4. Traccia progressi
        """)
    
    st.markdown("---")
    
    if not st.session_state.profile:
        st.warning("⚠️ **Inizia configurando il tuo profilo** nella sezione 👤 Profilo")
        if st.button("🚀 Vai a Profilo", type="primary", use_container_width=True):
            st.session_state.page = "👤 Profilo"
            st.rerun()
    else:
        st.success(f"✅ Profilo attivo: **{st.session_state.profile.name}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 Genera Piano Oggi", type="primary", use_container_width=True):
                if st.session_state.agent is None:
                    st.error("❌ Agent non inizializzato. Controlla la configurazione del provider e ricarica la pagina.")
                else:
                    with st.spinner("Generando piano giornaliero..."):
                        try:
                            today = datetime.now().strftime("%Y-%m-%d")
                            weekday_it = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"][datetime.now().weekday()]
                            is_workout = weekday_it in (st.session_state.profile.workout_days or [])
                            plan = st.session_state.agent.generate_daily_plan(today, is_workout)
                            st.session_state.current_plan = plan
                            st.success("✅ Piano generato!")
                            st.rerun()
                        except Exception as e:
                            # Cerca messaggio chiave API scaduta
                            msg = str(e)
                            if "API key expired" in msg or "API_KEY_INVALID" in msg:
                                st.error("❌ API Key scaduta o invalida. Aggiorna la chiave nella sidebar sotto '🔑 Configura/aggiorna GOOGLE_API_KEY'.")
                            else:
                                st.error(f"Errore nella generazione del piano: {e}")
        
        with col2:
            if st.button("📆 Genera Piano Settimana", type="secondary", use_container_width=True):
                st.info("Vai alla sezione 📆 Piano Settimanale per generare")

# ============================================================================
# PROFILO PAGE
# ============================================================================
elif page == "👤 Profilo":
    st.header("👤 Configurazione Profilo")
    
    # Mostra profilo Antonio caricato
    if st.session_state.profile and st.session_state.profile.name == "Antonio":
        st.success("✅ **Profilo Antonio caricato automaticamente!**")
        
        with st.expander("📋 Visualizza Profilo Completo", expanded=False):
            profile = st.session_state.profile
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👤 Nome", profile.name)
                st.metric("🎂 Età", f"{profile.age} anni")
                st.metric("⚖️ Peso", f"{profile.weight} kg")
            with col2:
                st.metric("📏 Altezza", f"{profile.height} cm")
                st.metric("💪 Attività", profile.activity_level.value)
                st.metric("🎯 Obiettivo", profile.dietary_goal.value)
            with col3:
                st.metric("🥗 Cibi preferiti", len(profile.preferred_foods))
                st.metric("🚫 Cibi evitati", len(profile.disliked_foods))
                st.metric("📅 Giorni workout", len(profile.workout_days) if profile.workout_days else 0)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🥗 Cibi Preferiti (Top 20)**")
                for food in profile.preferred_foods[:20]:
                    st.markdown(f"- {food}")
                if len(profile.preferred_foods) > 20:
                    st.markdown(f"*...e altri {len(profile.preferred_foods)-20}*")
            
            with col2:
                st.markdown("**🚫 Cibi da Evitare**")
                for food in profile.disliked_foods:
                    st.markdown(f"- ❌ {food}")
            
            st.markdown("---")
            st.markdown("**📅 Giorni Allenamento**")
            if profile.workout_days:
                st.write(", ".join(profile.workout_days))
            else:
                st.write("Nessun giorno configurato")
            
            st.markdown("**🔧 Altre Impostazioni**")
            st.write(f"- Vegetariano: {'✅' if profile.vegetarian else '❌'}")
            st.write(f"- Vegano: {'✅' if profile.vegan else '❌'}")
            st.write(f"- Senza glutine: {'✅' if profile.gluten_free else '❌'}")
            st.write(f"- Senza latticini: {'✅' if profile.dairy_free else '❌'}")
            st.write(f"- Meal prep: {'✅' if profile.meal_prep else '❌'}")
        
        st.info("💡 **Questo è il tuo profilo preset personale!** Include tutte le tue preferenze: NO frutta, NO pollo/volatili, solo cereali integrali, cibi a calorie negative, enfasi sulle uova, ecc.")
        
        if st.button("🔄 Resetta e Crea Nuovo Profilo"):
            st.session_state.profile = None
            st.session_state.agent = None
            st.rerun()
    
    # Se non c'è profilo o è stato resettato
    if not st.session_state.profile or st.session_state.profile.name != "Antonio":
        tab1, tab2 = st.tabs(["✏️ Nuovo Profilo", "📥 Carica Profilo Antonio"])
        
        with tab2:
            st.markdown("### 📥 Carica Profilo Preset Antonio")
            st.markdown("""
            Questo profilo include:
            - ✅ Età: 47 anni, Peso: 74kg, Altezza: 173cm
            - 🎯 Obiettivo: Dimagrimento + massa muscolare
            - 🥗 60+ cibi preferiti (verdure, legumi, uova, cereali integrali)
            - ❌ NO frutta, NO pollo/volatili, NO cereali raffinati
            - � Cibi a calorie negative (sedano, cetrioli, zenzero, etc)
            - 🥚 Enfasi sulle UOVA come fonte proteica principale
            - 💪 Allenamento: 3-4 giorni/settimana (circuiti intensi)
            - 🍳 Meal prep: Batch cooking legumi e uova sode
            """)
            
            if st.button("✅ Carica Profilo Antonio", type="primary"):
                try:
                    from profile_antonio import create_antonio_profile
                    st.session_state.profile = create_antonio_profile()
                    
                    provider = st.session_state.get("llm_provider", "google")
                    model_name = st.session_state.get("llm_model", "gemini-2.0-flash-exp")
                    base_url = st.session_state.get("llm_base_url", None)
                    api_key = os.getenv("GOOGLE_API_KEY") if provider == "google" else os.getenv("API_KEY")
                    client = create_llm_client(provider, api_key, model_name or "", base_url)
                    st.session_state.agent = NutritionAgent(client, st.session_state.profile)
                    
                    st.success("✅ Profilo Antonio caricato con successo!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore nel caricamento: {e}")
        
        with tab1:
            st.subheader("Crea il tuo profilo personalizzato")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome", value="Antonio")
                age = st.number_input("Età", min_value=18, max_value=100, value=35)
                weight = st.number_input("Peso (kg)", min_value=40.0, max_value=200.0, value=75.0, step=0.5)
                height = st.number_input("Altezza (cm)", min_value=140.0, max_value=220.0, value=175.0, step=1.0)
                
                activity = st.selectbox(
                    "Livello Attività",
                    [e.value for e in ActivityLevel],
                    index=2
                )
                
                goal = st.selectbox(
                    "Obiettivo",
                    [e.value for e in DietaryGoal],
                    index=3
                )
            
            with col2:
                st.markdown("**Preferenze Alimentari**")
                preferred = st.text_area(
                    "Cibi preferiti (separati da virgola)",
                    value="pollo, riso, verdure, pesce, avocado, noci"
                )
                disliked = st.text_area(
                    "Cibi da evitare (separati da virgola)",
                    value="funghi, cozze"
                )
                allergies = st.text_input("Allergie", value="")
                intolerances = st.text_input("Intolleranze", value="")
                
                st.markdown("**Restrizioni Dietetiche**")
                col_a, col_b = st.columns(2)
                with col_a:
                    vegetarian = st.checkbox("Vegetariano")
                    gluten_free = st.checkbox("Senza glutine")
                with col_b:
                    vegan = st.checkbox("Vegano")
                    dairy_free = st.checkbox("Senza latticini")
            
            st.markdown("**Allenamento**")
            col1, col2, col3 = st.columns(3)
            with col1:
                workout_days = st.multiselect(
                    "Giorni allenamento",
                    ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
                    default=["lunedì", "mercoledì", "venerdì"]
                )
            with col2:
                workout_time = st.selectbox("Orario allenamento", ["mattina", "pomeriggio", "sera"], index=1)
            with col3:
                meal_prep = st.checkbox("Meal Prep", value=True, help="Prepari pasti in anticipo?")
            
            st.markdown("**Altro**")
            col1, col2 = st.columns(2)
            with col1:
                cooking_time = st.selectbox("Tempo disponibile cucina", ["breve", "medio", "lungo"], index=1)
            with col2:
                budget = st.selectbox("Budget", ["basso", "medio", "alto"], index=1)
            
            if st.button("💾 Salva Profilo", type="primary", use_container_width=True):
                # Crea profilo
                profile = UserProfile(
                    name=name,
                    age=age,
                    weight=weight,
                    height=height,
                    activity_level=ActivityLevel(activity),
                    dietary_goal=DietaryGoal(goal),
                    preferred_foods=[f.strip() for f in preferred.split(",")],
                    disliked_foods=[f.strip() for f in disliked.split(",")],
                    allergies=[a.strip() for a in allergies.split(",") if a.strip()],
                    intolerances=[i.strip() for i in intolerances.split(",") if i.strip()],
                    vegetarian=vegetarian,
                    vegan=vegan,
                    gluten_free=gluten_free,
                    dairy_free=dairy_free,
                    workout_days=workout_days,
                    workout_time=workout_time,
                    cooking_time_available=cooking_time,
                    budget_level=budget,
                    meal_prep=meal_prep
                )
                
                # Inizializza agent
                provider = st.session_state.get("llm_provider", "google")
                model_name = st.session_state.get("llm_model", "gemini-2.0-flash-exp")
                base_url = st.session_state.get("llm_base_url", None)
                api_key = os.getenv("GOOGLE_API_KEY") if provider == "google" else os.getenv("API_KEY")
                client = create_llm_client(provider, api_key, model_name or "", base_url)
                agent = NutritionAgent(client, profile)
                
                st.session_state.profile = profile
                st.session_state.agent = agent
                
                st.success("✅ Profilo salvato con successo!")
                st.balloons()

# ============================================================================
# PIANO GIORNALIERO
# ============================================================================
elif page == "📅 Piano Giornaliero":
    st.header("📅 Piano Pasti Giornaliero")
    
    if not st.session_state.agent:
        st.warning("⚠️ Configura prima il tuo profilo nella sezione 👤 Profilo")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_date = st.date_input("Seleziona data", value=datetime.now())
        with col2:
            weekday_it = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"][selected_date.weekday()]
            default_days = []
            if st.session_state.profile and getattr(st.session_state.profile, 'workout_days', None):
                default_days = st.session_state.profile.workout_days
            is_workout = st.checkbox(
                "Giorno allenamento", 
                value=weekday_it in default_days
            )
        with col3:
            if st.button("🔄 Rigenera Piano", type="primary"):
                st.session_state.current_plan = None
        
        if not st.session_state.current_plan or st.session_state.current_plan.date != selected_date.strftime("%Y-%m-%d"):
            if st.button("✨ Genera Piano", type="primary", use_container_width=True):
                with st.spinner("🤖 AI sta preparando il tuo piano..."):
                    try:
                        plan = st.session_state.agent.generate_daily_plan(
                            selected_date.strftime("%Y-%m-%d"), 
                            is_workout
                        )
                        st.session_state.current_plan = plan
                        st.success("✅ Piano generato!")
                        st.rerun()
                    except Exception as e:
                        msg = str(e)
                        if "API key expired" in msg or "API_KEY_INVALID" in msg:
                            st.error("❌ API Key scaduta o invalida. Aggiorna la chiave nella sidebar sotto '🔑 Configura/aggiorna GOOGLE_API_KEY'.")
                        else:
                            st.error(f"Errore nella generazione del piano: {e}")
        
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            # Summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📆 Data", weekday_it.title())
            with col2:
                st.metric("🔥 Calorie Tot", f"{plan.total_calories} kcal")
            with col3:
                st.metric("🥩 Proteine", f"{plan.total_macros['proteine']:.0f}g")
            with col4:
                st.metric("💪 Allenamento", "Sì" if plan.is_workout_day else "No")
            
            st.markdown("---")
            
            # Meals
            for meal in plan.meals:
                meal_card_class = "meal-card workout-day" if plan.is_workout_day else "meal-card"
                
                with st.expander(f"🍽️ **{meal.meal_type.value.upper()}** - {meal.recipe_name} ({meal.calories} kcal)", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**📝 Ingredienti:**")
                        for ing in meal.ingredients:
                            st.markdown(f"- {ing['nome']}: **{ing['quantità']}**")
                        
                        st.markdown("**👨‍🍳 Preparazione:**")
                        for i, step in enumerate(meal.instructions, 1):
                            st.markdown(f"{i}. {step}")
                    
                    with col2:
                        st.markdown("**📊 Info Nutrizionali:**")
                        st.metric("Calorie", f"{meal.calories} kcal")
                        st.metric("Proteine", f"{meal.macros['proteine']}g")
                        st.metric("Carboidrati", f"{meal.macros['carboidrati']}g")
                        st.metric("Grassi", f"{meal.macros['grassi']}g")
                        
                        st.markdown(f"⏱️ **Prep:** {meal.prep_time} min")
                        st.markdown(f"🔥 **Cottura:** {meal.cooking_time} min")
                        
                        if meal.seasonal_score > 0.7:
                            st.success(f"🌱 Stagionale: {meal.seasonal_score:.0%}")
                        
                        if meal.notes:
                            st.info(f"💡 {meal.notes}")
            
            st.markdown("---")
            
            # Shopping List
            with st.expander("🛒 Lista della Spesa", expanded=False):
                st.markdown("**Ingredienti necessari:**")
                for item in plan.shopping_list:
                    st.markdown(f"- {item}")
                
                # Download
                shopping_text = "\n".join([f"☐ {item}" for item in plan.shopping_list])
                st.download_button(
                    "📥 Scarica Lista",
                    shopping_text,
                    file_name=f"spesa_{plan.date}.txt",
                    mime="text/plain"
                )

# ============================================================================
# PIANO SETTIMANALE
# ============================================================================
elif page == "📆 Piano Settimanale":
    st.header("📆 Piano Pasti Settimanale")
    
    if not st.session_state.agent:
        st.warning("⚠️ Configura prima il tuo profilo")
    else:
        st.info("💡 **Genera un piano completo per la settimana** - L'AI creerà ricette diverse per ogni giorno")
        
        if st.button("✨ Genera Piano Settimanale", type="primary", use_container_width=True):
            with st.spinner("🤖 Generazione in corso... (può richiedere 1-2 minuti)"):
                try:
                    weekly = st.session_state.agent.generate_weekly_plan()
                    # Save to session
                    st.session_state.weekly_plan = weekly
                    st.success("✅ Piano settimanale generato!")
                except Exception as e:
                    msg = str(e)
                    if "API key expired" in msg or "API_KEY_INVALID" in msg:
                        st.error("❌ API Key scaduta o invalida. Aggiorna la chiave nella sidebar sotto '🔑 Configura/aggiorna GOOGLE_API_KEY'.")
                    else:
                        st.error(f"Errore nella generazione del piano settimanale: {e}")
        
        if 'weekly_plan' in st.session_state and st.session_state.weekly_plan:
            weekly = st.session_state.weekly_plan
            
            # Weekly summary
            total_weekly_cal = sum(day.total_calories for day in weekly)
            avg_daily_cal = total_weekly_cal / 7
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔥 Calorie medie/giorno", f"{avg_daily_cal:.0f} kcal")
            with col2:
                workout_days_count = sum(1 for day in weekly if day.is_workout_day)
                st.metric("💪 Giorni allenamento", workout_days_count)
            with col3:
                all_meals = sum(len(day.meals) for day in weekly)
                st.metric("🍽️ Pasti totali", all_meals)
            
            st.markdown("---")
            
            # Daily tabs
            weekday_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            tabs = st.tabs(weekday_names)
            
            for i, (tab, day) in enumerate(zip(tabs, weekly)):
                with tab:
                    if day.is_workout_day:
                        st.markdown("### 💪 Giorno Allenamento")
                    
                    st.metric("🔥 Calorie totali", f"{day.total_calories} kcal")
                    
                    for meal in day.meals:
                        with st.expander(f"**{meal.meal_type.value}** - {meal.recipe_name}", expanded=False):
                            st.markdown(f"**Calorie:** {meal.calories} kcal")
                            st.markdown(f"**Macros:** P:{meal.macros['proteine']}g | C:{meal.macros['carboidrati']}g | F:{meal.macros['grassi']}g")

# ============================================================================
# CERCA RICETTE
# ============================================================================
elif page == "🔍 Cerca Ricette":
    st.header("🔍 Suggerimenti Ricette")
    
    if not st.session_state.agent:
        st.warning("⚠️ Configura prima il tuo profilo")
    else:
        st.markdown("Cerca ricette specifiche per un tipo di pasto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            meal_type = st.selectbox(
                "Tipo pasto",
                [e.value for e in MealType]
            )
        
        with col2:
            quick = st.checkbox("Solo ricette veloci (< 20 min)")
            high_protein = st.checkbox("Alto contenuto proteico")
        
        if st.button("🔍 Cerca", type="primary"):
            preferences = {}
            if quick:
                preferences["veloce"] = True
            if high_protein:
                preferences["proteico"] = True
            
            with st.spinner("🤖 Cercando ricette..."):
                try:
                    meal_enum = MealType(meal_type)
                    suggestions = st.session_state.agent.get_meal_suggestions(meal_enum, preferences)
                    st.success(f"✅ Trovate {len(suggestions)} ricette!")
                    for i, recipe in enumerate(suggestions, 1):
                        st.markdown(f"{i}. **{recipe}**")
                except Exception as e:
                    msg = str(e)
                    if "API key expired" in msg or "API_KEY_INVALID" in msg:
                        st.error("❌ API Key scaduta o invalida. Aggiorna la chiave nella sidebar sotto '🔑 Configura/aggiorna GOOGLE_API_KEY'.")
                    else:
                        st.error(f"Errore nella ricerca: {e}")

# ============================================================================
# TABATA TIMER - ALLENAMENTO
# ============================================================================
elif page == "⏱️ Tabata Timer":
    st.header("⏱️ Tabata Timer - Allenamento")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%); 
                padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0; text-align: center;">💪 Il Tuo Timer per Circuiti Intensi</h2>
        <p style="text-align: center; margin: 0.5rem 0 0 0; opacity: 0.9;">
            Allenamento ad alta intensità sincronizzato con la tua nutrizione
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Informazioni sull'allenamento dell'utente
    if st.session_state.profile:
        st.markdown("### 🎯 Il Tuo Programma")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 Frequenza", "3-4 giorni/settimana")
        with col2:
            st.metric("⏱️ Durata", "30 min circuito")
        with col3:
            st.metric("💪 Tipo", "Circuiti + Calisthenics")
        
        st.info("🥗 **Nutrizione Pre-Workout**: Carboidrati integrali (riso, farro) 1-2h prima")
        st.success("🥚 **Nutrizione Post-Workout**: Proteine (legumi/uova/tofu) + carboidrati integrali")
    
    st.markdown("---")
    
    # Opzioni di accesso al timer
    st.markdown("### 🚀 Scegli come Allenarti")
    
    tab1, tab2, tab3 = st.tabs(["🌐 Web Timer", "🐍 Python Timer", "📱 App Mobile"])
    
    with tab1:
        st.markdown("""
        ### 🌐 Timer Online (Consigliato)
        
        Timer Tabata completo e professionale con:
        - ✨ Design moderno ottimizzato per mobile
        - 🔊 Sintesi vocale per countdown
        - 📱 Layout responsive
        - 🎯 Preset rapidi (20/10, 30/15, 40/20)
        - 💾 Salvataggio preset personalizzati
        - 📅 Calendario allenamenti con tracking
        - 📲 Installabile come PWA (funziona offline!)
        """)
        
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <a href="https://ninuxi.github.io/tabata-timer/" target="_blank">
                <button style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
                               color: white; border: none; padding: 1rem 3rem;
                               font-size: 1.2rem; font-weight: bold; border-radius: 12px;
                               cursor: pointer; box-shadow: 0 4px 12px rgba(255,107,107,0.4);">
                    🚀 Apri Timer Web
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**💡 Tip**: Aggiungi alla Home del tuo smartphone per accesso rapido!")
    
    with tab2:
        st.markdown("""
        ### 🐍 Timer Python
        
        Versioni desktop per chi preferisce lavorare da terminale:
        
        **1️⃣ Timer Classico** (`tabata_fisso.py`)
        - Impostazioni predefinite: 20s lavoro / 10s recupero / 8 round
        - Segnali audio
        - Compatibile Windows/Mac/Linux
        
        **2️⃣ Timer Personalizzabile** (`tabata_personalizzabile.py`)
        - Personalizzazione completa
        - Sintesi vocale
        - Beep differenziati
        """)
        
        st.code("""
# Timer classico
cd nutrition-agent/tabata-timer-main
python tabata_fisso.py

# Timer personalizzabile
python tabata_personalizzabile.py
        """, language="bash")
        
        if st.button("📂 Apri cartella Tabata Timer"):
            import subprocess
            import platform
            tabata_path = Path(__file__).parent / "tabata-timer-main"
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(tabata_path)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(tabata_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(tabata_path)])
    
    with tab3:
        st.markdown("""
        ### 📱 App PWA (Progressive Web App)
        
        Installa il timer come app sul tuo smartphone:
        
        **iPhone/iPad:**
        1. Apri https://ninuxi.github.io/tabata-timer/ in Safari
        2. Tap su icona "Condividi" (quadrato con freccia)
        3. Scorri e tap "Aggiungi a Home"
        4. Conferma - l'app sarà nella tua Home!
        
        **Android:**
        1. Apri https://ninuxi.github.io/tabata-timer/ in Chrome
        2. Tap menu (3 puntini)
        3. Tap "Installa app" o "Aggiungi a Home"
        4. Conferma
        
        **✨ Vantaggi PWA:**
        - 📲 Icona sulla Home come app nativa
        - 🚀 Apertura istantanea
        - 📡 Funziona offline
        - 💾 Salva i tuoi preset
        - 📅 Tracking allenamenti
        """)
        
        st.image("https://raw.githubusercontent.com/ninuxi/tabata-timer/main/icon-192.svg", width=150)
    
    st.markdown("---")
    
    # Sincronizzazione con nutrizione
    st.markdown("### 🔄 Sincronizzazione Allenamento-Nutrizione")
    
    st.markdown("""
    Il tuo piano nutrizionale si adatta automaticamente ai giorni di allenamento:
    
    | Giorni Allenamento | Giorni Riposo |
    |-------------------|---------------|
    | 🔼 **+10-15% calorie** | 📊 Calorie base |
    | 💪 **+20-30g proteine** | 🥗 Proteine standard |
    | 🍚 **+carboidrati integrali** | ⚖️ Bilanciato |
    | ⚡ Pre: riso/farro | 🌿 Focus verdure |
    | 🥚 Post: uova/legumi | 🥗 Pasti leggeri |
    """)
    
    if st.session_state.profile and st.session_state.profile.workout_days:
        giorni = ", ".join(st.session_state.profile.workout_days)
        st.success(f"✅ Giorni allenamento configurati: **{giorni}**")
        st.info("💡 I piani giornalieri generati riconosceranno automaticamente questi giorni e adatteranno le ricette!")

# ============================================================================
# ANALISI
# ============================================================================
elif page == "📊 Analisi":
    st.header("📊 Analisi Nutrizionale")
    
    if not st.session_state.agent:
        st.warning("⚠️ Configura prima il tuo profilo")
    else:
        report = st.session_state.agent.analyze_nutrition_goals()
        st.markdown(report)
        
        # History visualization
        if st.session_state.agent.meal_history:
            st.markdown("### 📈 Storico Piani")
            
            history_data = []
            for day in st.session_state.agent.meal_history[-14:]:
                history_data.append({
                    "Data": day["date"],
                    "Calorie": day["total_calories"],
                    "Proteine": day["total_macros"]["proteine"],
                    "Allenamento": "💪" if day["is_workout_day"] else "🏠"
                })
            
            st.dataframe(history_data, use_container_width=True)

# ============================================================================
# IMPOSTAZIONI
# ============================================================================
elif page == "⚙️ Impostazioni":
    st.header("⚙️ Impostazioni")
    
    st.markdown("### 🔧 Configurazione Sistema")
    st.code(f"""
API Key: {'✅ Configurata' if os.getenv('GOOGLE_API_KEY') else '❌ Mancante'}
Model: gemini-2.0-flash-exp
Data Directory: data/nutrition/
""")
    
    if st.session_state.agent:
        st.markdown("### 📁 Gestione Dati")
        
        if st.button("🗑️ Cancella Storico", type="secondary"):
            if st.checkbox("Conferma cancellazione"):
                st.session_state.agent.meal_history = []
                st.session_state.agent._save_meal_history()
                st.success("✅ Storico cancellato")
        
        if st.button("📥 Esporta Profilo"):
            import json
            from dataclasses import asdict
            if st.session_state.profile:
                profile_json = json.dumps(asdict(st.session_state.profile), indent=2, default=str)
                st.download_button(
                    "💾 Scarica JSON",
                    profile_json,
                    file_name="nutrition_profile.json",
                    mime="application/json"
                )
            else:
                st.warning("Nessun profilo caricato da esportare.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
    🥗 Nutrition Agent | Powered by Google Gemini 2.0 | Built with ❤️
</div>
""", unsafe_allow_html=True)
