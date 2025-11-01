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
from datapizza.clients.google import GoogleClient

# Page config
st.set_page_config(
    page_title="🥗 Nutrition Agent",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .meal-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .workout-day {
        border-left-color: #FF5722;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🥗 Nutrition Agent</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Il tuo assistente AI per alimentazione sana e personalizzata</p>', unsafe_allow_html=True)

# Initialize session state
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ GOOGLE_API_KEY non trovata nel file .env")
        st.stop()
    else:
        st.success("✅ API Key configurata")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📍 Navigazione")
    page = st.radio(
        "Seleziona sezione:",
        ["🏠 Home", "👤 Profilo", "📅 Piano Giornaliero", "📆 Piano Settimanale", 
         "🔍 Cerca Ricette", "📊 Analisi", "⚙️ Impostazioni"],
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
                with st.spinner("Generando piano giornaliero..."):
                    today = datetime.now().strftime("%Y-%m-%d")
                    weekday_it = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"][datetime.now().weekday()]
                    is_workout = weekday_it in (st.session_state.profile.workout_days or [])
                    
                    plan = st.session_state.agent.generate_daily_plan(today, is_workout)
                    st.session_state.current_plan = plan
                    st.success("✅ Piano generato!")
                    st.rerun()
        
        with col2:
            if st.button("📆 Genera Piano Settimana", type="secondary", use_container_width=True):
                st.info("Vai alla sezione 📆 Piano Settimanale per generare")

# ============================================================================
# PROFILO PAGE
# ============================================================================
elif page == "👤 Profilo":
    st.header("👤 Configurazione Profilo")
    
    tab1, tab2 = st.tabs(["✏️ Nuovo Profilo", "📋 Profilo Esistente"])
    
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
            client = GoogleClient(api_key=api_key, model="gemini-2.0-flash-exp")
            agent = NutritionAgent(client, profile)
            
            st.session_state.profile = profile
            st.session_state.agent = agent
            
            st.success("✅ Profilo salvato con successo!")
            st.balloons()
    
    with tab2:
        if st.session_state.profile:
            st.json({
                "nome": st.session_state.profile.name,
                "età": st.session_state.profile.age,
                "peso": st.session_state.profile.weight,
                "altezza": st.session_state.profile.height,
                "attività": st.session_state.profile.activity_level.value,
                "obiettivo": st.session_state.profile.dietary_goal.value,
                "giorni_allenamento": st.session_state.profile.workout_days
            })
        else:
            st.info("Nessun profilo configurato ancora")

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
            is_workout = st.checkbox(
                "Giorno allenamento", 
                value=weekday_it in (st.session_state.profile.workout_days or [])
            )
        with col3:
            if st.button("🔄 Rigenera Piano", type="primary"):
                st.session_state.current_plan = None
        
        if not st.session_state.current_plan or st.session_state.current_plan.date != selected_date.strftime("%Y-%m-%d"):
            if st.button("✨ Genera Piano", type="primary", use_container_width=True):
                with st.spinner("🤖 AI sta preparando il tuo piano..."):
                    plan = st.session_state.agent.generate_daily_plan(
                        selected_date.strftime("%Y-%m-%d"), 
                        is_workout
                    )
                    st.session_state.current_plan = plan
                    st.success("✅ Piano generato!")
                    st.rerun()
        
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
                weekly = st.session_state.agent.generate_weekly_plan()
                
                # Save to session
                st.session_state.weekly_plan = weekly
                st.success("✅ Piano settimanale generato!")
        
        if 'weekly_plan' in st.session_state:
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
                meal_enum = MealType(meal_type)
                suggestions = st.session_state.agent.get_meal_suggestions(meal_enum, preferences)
                
                st.success(f"✅ Trovate {len(suggestions)} ricette!")
                
                for i, recipe in enumerate(suggestions, 1):
                    st.markdown(f"{i}. **{recipe}**")

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
            profile_json = json.dumps(asdict(st.session_state.profile), indent=2, default=str)
            st.download_button(
                "💾 Scarica JSON",
                profile_json,
                file_name="nutrition_profile.json",
                mime="application/json"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
    🥗 Nutrition Agent | Powered by Google Gemini 2.0 | Built with ❤️
</div>
""", unsafe_allow_html=True)
