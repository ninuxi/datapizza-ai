# 🥗 Nutrition Agent

**Agente AI per pianificazione nutrizionale personalizzata e consigli alimentari intelligenti**

---

## 🎯 Cosa Fa

Nutrition Agent è il tuo assistente personale per:
- **Pianificare pasti** giornalieri e settimanali
- **Ricette stagionali** con ingredienti freschi
- **Adattamento** a stile di vita e allenamento
- **Liste della spesa** automatiche
- **Tracking nutrizionale** e obiettivi
- **Suggerimenti AI** personalizzati in tempo reale

---

## ⚡ Quick Start

### 1. Configura API Key

Assicurati che il file `.env` nella root del progetto contenga:

```bash
GOOGLE_API_KEY=la_tua_chiave_google
```

### 2. Installa dipendenze

```bash
cd nutrition-agent
pip install -r requirements.txt
```

### 3. Avvia Dashboard

```bash
./start_nutrition.sh
```

Oppure manualmente:

```bash
streamlit run nutrition_dashboard.py --server.port 8550
```

Dashboard disponibile su: **http://127.0.0.1:8550**

---

## 📋 Features Principali

### 🎯 Personalizzazione Completa

- **Profilo utente** con età, peso, altezza, obiettivi
- **Preferenze alimentari** (cibi preferiti/da evitare)
- **Allergie e intolleranze** (glutine, lattosio, etc.)
- **Restrizioni dietetiche** (vegetariano, vegano, etc.)

### 💪 Integrazione Allenamento

- **Pianificazione giorni** allenamento
- **Adattamento calorie/macros** basato su attività
- **Pasto post-workout** automatico
- **Timing ottimale** nutrizionale

### 🌱 Ingredienti Stagionali

- **Database stagionale** (verdure, frutta, altro)
- **Priorità prodotti freschi** e locali
- **Score stagionalità** per ogni ricetta
- **Aggiornamento automatico** per mese

### 🧠 Intelligenza AI

- **Gemini 2.0 Flash** per generazione ricette
- **Apprendimento preferenze** utente
- **Variazione automatica** per evitare monotonia
- **Suggerimenti contestuali** intelligenti

### 📊 Tracking & Analytics

- **Storico pasti** completo
- **Analisi nutrizionale** periodica
- **Grafici calorie/macros** trend
- **Report progressi** verso obiettivi

---

## 🖥️ Interfaccia Dashboard

### 📱 Pagine Disponibili

1. **🏠 Home** - Overview e quick actions
2. **👤 Profilo** - Configurazione utente dettagliata
3. **📅 Piano Giornaliero** - Generazione piano singolo giorno
4. **📆 Piano Settimanale** - Piano completo 7 giorni
5. **🔍 Cerca Ricette** - Suggerimenti AI per tipo pasto
6. **📊 Analisi** - Report nutrizionale e storico
7. **⚙️ Impostazioni** - Gestione dati e export

### 🎨 UI Features

- Design moderno con gradient e card
- Visualizzazione ricette espandibili
- Download lista spesa formato testo
- Export profilo JSON
- Metriche real-time

---

## 📁 Struttura Progetto

```
nutrition-agent/
├── nutrition_agent.py          # Core agent logic
├── nutrition_dashboard.py      # Streamlit UI
├── start_nutrition.sh          # Launch script
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── data/
    └── nutrition/
        └── meal_history.json   # Storico piani generati
```

---

## 🔧 Configurazione Avanzata

### Profilo Utente

Il profilo include:

```python
UserProfile(
    name="Antonio",
    age=35,
    weight=75.0,
    height=175.0,
    activity_level=ActivityLevel.MODERATO,
    dietary_goal=DietaryGoal.PERFORMANCE,
    preferred_foods=["pollo", "riso", "verdure", ...],
    disliked_foods=["funghi", "cozze"],
    allergies=[],
    intolerances=[],
    workout_days=["lunedì", "mercoledì", "venerdì"],
    workout_time="pomeriggio",
    cooking_time_available="medio",
    budget_level="medio",
    meal_prep=True
)
```

### Tipi di Pasto

- `COLAZIONE` - Prima colazione
- `SPUNTINO_MATTINA` - Snack mattutino
- `PRANZO` - Pranzo principale
- `SPUNTINO_POMERIGGIO` - Snack pomeridiano
- `CENA` - Cena serale
- `POST_WORKOUT` - Recovery post allenamento

### Livelli Attività

- `SEDENTARIO` - Poco movimento
- `LEGGERO` - 1-3 giorni/settimana
- `MODERATO` - 3-5 giorni/settimana
- `INTENSO` - 6-7 giorni/settimana
- `ATLETA` - 2x al giorno

### Obiettivi

- `MANTENIMENTO` - Mantenere peso attuale
- `DIMAGRIMENTO` - Perdere peso gradualmente
- `AUMENTO_MASSA` - Aumentare massa muscolare
- `PERFORMANCE` - Ottimizzare performance sportiva
- `SALUTE` - Focus benessere generale

---

## 🤖 Uso Programmatico

### Esempio Python

```python
from nutrition_agent import NutritionAgent, UserProfile, ActivityLevel, DietaryGoal
from datapizza.clients.google import GoogleClient

# Setup
client = GoogleClient(api_key="your_key", model="gemini-2.0-flash-exp")
profile = UserProfile(
    name="Mario",
    age=30,
    weight=70,
    height=175,
    activity_level=ActivityLevel.MODERATO,
    dietary_goal=DietaryGoal.MANTENIMENTO,
    preferred_foods=["pasta", "verdure", "pesce"],
    disliked_foods=[],
    allergies=[],
    intolerances=[],
    workout_days=["lunedì", "giovedì"]
)

agent = NutritionAgent(client, profile)

# Genera piano giornaliero
plan = agent.generate_daily_plan("2025-11-01", is_workout_day=True)

print(f"Calorie totali: {plan.total_calories} kcal")
print(f"Pasti: {len(plan.meals)}")
print(f"Lista spesa: {len(plan.shopping_list)} ingredienti")

# Genera piano settimanale
weekly = agent.generate_weekly_plan()
print(f"Piano settimana: {len(weekly)} giorni")
```

---

## 📊 Output Esempio

### Piano Giornaliero

```json
{
  "date": "2025-11-01",
  "is_workout_day": true,
  "total_calories": 2400,
  "total_macros": {
    "proteine": 180,
    "carboidrati": 250,
    "grassi": 70
  },
  "meals": [
    {
      "meal_type": "colazione",
      "recipe_name": "Porridge proteico con frutta",
      "calories": 450,
      "macros": {"proteine": 30, "carboidrati": 55, "grassi": 12},
      "prep_time": 10,
      "cooking_time": 5,
      "seasonal_score": 0.9
    }
    // ... altri pasti
  ],
  "shopping_list": [
    "avena: 100g",
    "latte: 250ml",
    "banane: 1",
    // ...
  ]
}
```

---

## 🔄 Workflow Tipico

1. **Setup iniziale**
   - Configura profilo con dati personali
   - Imposta preferenze alimentari
   - Definisci giorni allenamento

2. **Generazione piano**
   - Seleziona data/periodo
   - AI genera ricette personalizzate
   - Review e conferma

3. **Esecuzione**
   - Segui ricette giornaliere
   - Usa lista spesa generata
   - Traccia progressi

4. **Analisi**
   - Verifica calorie/macros
   - Analizza trend settimanali
   - Aggiusta obiettivi se necessario

---

## 🎯 Prossimi Sviluppi

- [ ] **Database ricette** salvate e preferite
- [ ] **Import foto piatti** per analisi nutrizionale
- [ ] **Integrazione wearable** (Apple Health, Fitbit)
- [ ] **Social features** - condividi ricette
- [ ] **Grocery delivery** integration (Amazon Fresh, etc)
- [ ] **Calorie counter** foto-based con AI vision
- [ ] **Meal prep scheduler** ottimizzato
- [ ] **Multi-lingua** support

---

## 🤝 Contributi

Basato su **datapizza-ai** framework.

**Autore:** Antonio Mainenti  
**Licenza:** MIT  
**Data creazione:** Novembre 2025

---

## 📞 Support

Per domande o supporto:
- GitHub Issues
- Email: oggettosonoro@gmail.com

---

**Buon appetito! 🥗**
