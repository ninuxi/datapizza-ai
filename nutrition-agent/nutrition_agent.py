"""
🥗 Nutrition Agent - AI-Powered Meal Planning & Nutrition Advisor
==================================================================

Agente AI per consigli personalizzati su alimentazione, ricette e nutrizione.

Features:
- Pianificazione pasti giornaliera/settimanale
- Ricette stagionali basate su prodotti freschi
- Adattamento a stile di vita e allenamento
- Tracking nutrizionale e obiettivi
- Suggerimenti per spesa intelligente
- Variazioni basate su preferenze e intolleranze

Autore: Antonio Mainenti
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Import datapizza core Client interface (packages installed in editable mode)
from datapizza.core.clients import Client


class MealType(Enum):
    """Tipo di pasto"""
    COLAZIONE = "colazione"
    SPUNTINO_MATTINA = "spuntino_mattina"
    PRANZO = "pranzo"
    SPUNTINO_POMERIGGIO = "spuntino_pomeriggio"
    CENA = "cena"
    POST_WORKOUT = "post_workout"


class ActivityLevel(Enum):
    """Livello di attività fisica"""
    SEDENTARIO = "sedentario"
    LEGGERO = "leggero"  # 1-3 giorni/settimana
    MODERATO = "moderato"  # 3-5 giorni/settimana
    INTENSO = "intenso"  # 6-7 giorni/settimana
    ATLETA = "atleta"  # 2x al giorno


class DietaryGoal(Enum):
    """Obiettivo alimentare"""
    MANTENIMENTO = "mantenimento"
    DIMAGRIMENTO = "dimagrimento"
    AUMENTO_MASSA = "aumento_massa"
    PERFORMANCE = "performance"
    SALUTE = "salute"


@dataclass
class UserProfile:
    """Profilo utente per personalizzazione"""
    name: str
    age: int
    weight: float  # kg
    height: float  # cm
    activity_level: ActivityLevel
    dietary_goal: DietaryGoal
    
    # Preferenze alimentari
    preferred_foods: List[str]
    disliked_foods: List[str]
    allergies: List[str]
    intolerances: List[str]
    
    # Restrizioni dietetiche
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    
    # Schedule
    workout_days: List[str] = None  # ["lunedì", "mercoledì", "venerdì"]
    workout_time: str = "mattina"  # mattina, pomeriggio, sera
    meal_times: Dict[str, str] = None  # {"colazione": "07:00", "pranzo": "13:00", ...}
    
    # Altro
    cooking_time_available: str = "medio"  # breve (15min), medio (30min), lungo (60min+)
    budget_level: str = "medio"  # basso, medio, alto
    meal_prep: bool = False  # Prepara pasti in anticipo?


@dataclass
class MealPlan:
    """Piano pasto"""
    date: str
    meal_type: MealType
    recipe_name: str
    ingredients: List[Dict[str, str]]  # [{"nome": "pollo", "quantità": "150g"}]
    instructions: List[str]
    calories: int
    macros: Dict[str, float]  # proteine, carboidrati, grassi
    prep_time: int  # minuti
    cooking_time: int  # minuti
    notes: str = ""
    seasonal_score: float = 1.0  # 0-1, quanto usa ingredienti di stagione
    

@dataclass
class DailyPlan:
    """Piano giornaliero completo"""
    date: str
    is_workout_day: bool
    meals: List[MealPlan]
    total_calories: int
    total_macros: Dict[str, float]
    shopping_list: List[str]
    notes: str = ""


class NutritionAgent:
    """
    Agente AI per pianificazione nutrizionale personalizzata.
    """
    
    def __init__(self, google_client: Client, user_profile: UserProfile, data_dir: str = "data/nutrition"):
        """
        Inizializza Nutrition Agent.
        
        Args:
            google_client: Client LLM compatibile (Google, OpenAI-like, Ollama, ecc.)
            user_profile: Profilo utente con preferenze
            data_dir: Directory per salvare dati
        """
        self.client = google_client
        self.profile = user_profile
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Carica o crea storico pasti
        self.meal_history_file = self.data_dir / "meal_history.json"
        self.meal_history = self._load_meal_history()
        
        # Carica ingredienti stagionali
        self.seasonal_ingredients = self._get_seasonal_ingredients()
    
    def _load_meal_history(self) -> List[Dict]:
        """Carica storico pasti precedenti"""
        if self.meal_history_file.exists():
            with open(self.meal_history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_meal_history(self):
        """Salva storico pasti"""
        # Converti oggetti non serializzabili in JSON-friendly format
        def convert_to_json_safe(obj):
            if isinstance(obj, MealType):
                return obj.value
            elif isinstance(obj, (ActivityLevel, DietaryGoal)):
                return obj.value
            elif hasattr(obj, '__dict__'):
                return {k: convert_to_json_safe(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_to_json_safe(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_json_safe(v) for k, v in obj.items()}
            return obj
        
        safe_history = convert_to_json_safe(self.meal_history)
        
        with open(self.meal_history_file, 'w') as f:
            json.dump(safe_history, f, indent=2, ensure_ascii=False)
    
    def _get_seasonal_ingredients(self) -> Dict[str, List[str]]:
        """Restituisce ingredienti di stagione per mese"""
        seasonal_db = {
            "novembre": {
                "verdure": ["cavolo nero", "cavolo verza", "broccoli", "cavolfiore", "zucca", 
                           "carciofi", "spinaci", "radicchio rosso", "radicchio trevigiano", 
                           "finocchi", "porri", "sedano rapa", "barbabietole", "carote", 
                           "rape", "topinambur", "coste", "cicoria"],
                "legumi": ["lenticchie", "ceci", "fagioli borlotti", "fagioli cannellini", 
                          "fagioli neri", "piselli secchi", "fave secche"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa", "grano saraceno", "avena"],
                "frutta_secca": ["noci", "mandorle", "nocciole", "castagne"],
                "altro": ["funghi porcini", "funghi champignon", "tartufo"]
            },
            "dicembre": {
                "verdure": ["cavolo nero", "cavolo verza", "broccoli", "cavolfiore", "carciofi", 
                           "spinaci", "radicchio", "finocchi", "porri", "sedano rapa", "carote"],
                "legumi": ["lenticchie", "ceci", "fagioli borlotti", "fagioli cannellini", "piselli secchi"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa", "avena"],
                "frutta_secca": ["noci", "mandorle", "nocciole", "castagne"],
                "altro": ["funghi", "tartufo"]
            },
            "gennaio": {
                "verdure": ["cavolo nero", "cavolo cappuccio", "broccoli", "cavolfiore", "carciofi",
                           "spinaci", "radicchio", "finocchi", "porri", "sedano rapa"],
                "legumi": ["lenticchie", "ceci", "fagioli", "fave secche"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa", "avena"],
                "frutta_secca": ["noci", "mandorle", "nocciole"]
            },
            "febbraio": {
                "verdure": ["carciofi", "finocchi", "radicchio", "spinaci", "cicoria", 
                           "porri", "sedano", "cavolfiore", "cavolo cappuccio"],
                "legumi": ["lenticchie", "ceci", "fagioli", "fave secche"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"],
                "frutta_secca": ["mandorle", "noci"]
            },
            "marzo": {
                "verdure": ["carciofi", "asparagi", "agretti", "fave fresche", "piselli freschi",
                           "spinaci", "radicchio", "lattuga", "rucola"],
                "legumi": ["fave fresche", "piselli freschi", "ceci", "lenticchie"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"]
            },
            "aprile": {
                "verdure": ["asparagi", "carciofi", "fave fresche", "piselli freschi", "agretti",
                           "spinaci", "lattuga", "rucola", "ravanelli"],
                "legumi": ["fave fresche", "piselli freschi", "lenticchie", "ceci"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"]
            },
            "maggio": {
                "verdure": ["asparagi", "fave", "piselli", "zucchine", "pomodori", "melanzane",
                           "peperoni", "lattuga", "rucola", "ravanelli"],
                "legumi": ["fave fresche", "piselli freschi", "fagiolini"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"]
            },
            "giugno": {
                "verdure": ["zucchine", "pomodori", "melanzane", "peperoni", "cetrioli",
                           "fagiolini", "lattuga", "rucola", "basilico"],
                "legumi": ["fagiolini", "piselli", "lenticchie"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"]
            },
            "luglio": {
                "verdure": ["pomodori", "zucchine", "melanzane", "peperoni", "cetrioli",
                           "fagiolini", "lattuga", "rucola", "basilico"],
                "legumi": ["fagiolini", "borlotti freschi"],
                "cereali_integrali": ["riso integrale", "farro", "orzo"]
            },
            "agosto": {
                "verdure": ["pomodori", "zucchine", "melanzane", "peperoni", "cetrioli",
                           "fagiolini", "lattuga", "basilico"],
                "legumi": ["fagioli freschi", "fagiolini"],
                "cereali_integrali": ["riso integrale", "farro", "orzo"]
            },
            "settembre": {
                "verdure": ["pomodori", "zucchine", "melanzane", "peperoni", "zucca",
                           "funghi", "spinaci", "bietole", "radicchio"],
                "legumi": ["fagioli freschi", "lenticchie", "ceci"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"]
            },
            "ottobre": {
                "verdure": ["zucca", "cavolo", "broccoli", "cavolfiore", "spinaci", "bietole",
                           "radicchio", "funghi", "finocchi"],
                "legumi": ["lenticchie", "ceci", "fagioli borlotti", "fagioli cannellini"],
                "cereali_integrali": ["riso integrale", "farro", "orzo", "quinoa"],
                "altro": ["funghi porcini", "castagne"]
            }
        }
        
        current_month = datetime.now().strftime("%B").lower()
        # Map inglese -> italiano
        month_map = {
            "january": "gennaio", "february": "febbraio", "march": "marzo",
            "april": "aprile", "may": "maggio", "june": "giugno",
            "july": "luglio", "august": "agosto", "september": "settembre",
            "october": "ottobre", "november": "novembre", "december": "dicembre"
        }
        current_month_it = month_map.get(current_month, "novembre")
        
        return seasonal_db.get(current_month_it, seasonal_db["novembre"])
    
    def _build_system_prompt(self) -> str:
        """Costruisce system prompt personalizzato"""
        
        # Carica linee guida specifiche utente se disponibili
        user_guidelines = None
        if self.profile.name.lower() == "antonio":
            try:
                from profile_antonio import get_nutrition_guidelines_antonio
                user_guidelines = get_nutrition_guidelines_antonio()
            except ImportError:
                pass
        
        dietary_restrictions = []
        if self.profile.vegetarian:
            dietary_restrictions.append("vegetariana")
        if self.profile.vegan:
            dietary_restrictions.append("vegana")
        if self.profile.gluten_free:
            dietary_restrictions.append("senza glutine")
        if self.profile.dairy_free:
            dietary_restrictions.append("senza latticini")
        
        restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "nessuna restrizione"
        
        # Ingredienti stagionali
        seasonal_text = ""
        for category, items in self.seasonal_ingredients.items():
            seasonal_text += f"\n- {category.title()}: {', '.join(items)}"
        
        prompt = f"""Sei un esperto nutrizionista AI specializzato in pianificazione pasti personalizzata.

PROFILO UTENTE:
===============
Nome: {self.profile.name}
Età: {self.profile.age} anni
Peso: {self.profile.weight} kg
Altezza: {self.profile.height} cm
Livello attività: {self.profile.activity_level.value}
Obiettivo: {self.profile.dietary_goal.value}

PREFERENZE ALIMENTARI:
======================
Cibi preferiti: {', '.join(self.profile.preferred_foods)}
Cibi da evitare: {', '.join(self.profile.disliked_foods)}
Allergie: {', '.join(self.profile.allergies) if self.profile.allergies else 'nessuna'}
Intolleranze: {', '.join(self.profile.intolerances) if self.profile.intolerances else 'nessuna'}
Restrizioni dietetiche: {restrictions_text}

STILE DI VITA:
==============
Giorni allenamento: {', '.join(self.profile.workout_days) if self.profile.workout_days else 'da definire'}
Orario allenamento: {self.profile.workout_time}
Tempo disponibile cucina: {self.profile.cooking_time_available}
Budget: {self.profile.budget_level}
Meal prep: {'Sì' if self.profile.meal_prep else 'No'}

INGREDIENTI DI STAGIONE (mese corrente):
=========================================={seasonal_text}
"""

        # Aggiungi linee guida personalizzate se disponibili
        if user_guidelines:
            prompt += f"""
FILOSOFIA ALIMENTARE UTENTE:
============================
{user_guidelines['philosophy']}

PRIORITÀ ASSOLUTE (da rispettare sempre):
==========================================
"""
            for i, priority in enumerate(user_guidelines['priorities'], 1):
                prompt += f"{i}. {priority}\n"
            
            prompt += f"""
TARGET MACRONUTRIENTI GIORNALIERI:
===================================
{user_guidelines['macros_target']['note']}
Calorie: {user_guidelines['macros_target']['calories_range']}
Proteine: {user_guidelines['macros_target']['protein_target']}
Carboidrati: {user_guidelines['macros_target']['carbs']}
Grassi: {user_guidelines['macros_target']['fats']}

STRUTTURA PASTI IDEALE:
========================
Colazione: {user_guidelines['meal_structure']['colazione']}
Pranzo: {user_guidelines['meal_structure']['pranzo']}
Cena: {user_guidelines['meal_structure']['cena']}
Spuntini: {user_guidelines['meal_structure']['spuntini']}

MEAL PREP E BATCH COOKING:
===========================
L'utente ama il meal prep. Suggerisci ricette che permettano:
"""
            for strategy in user_guidelines['batch_cooking']:
                prompt += f"- {strategy}\n"
            
            prompt += f"""
NUTRIZIONE PRE/POST WORKOUT:
=============================
Pre-workout: {user_guidelines['workout_nutrition']['pre_workout']}
Post-workout: {user_guidelines['workout_nutrition']['post_workout']}
Circuiti intensi: {user_guidelines['workout_nutrition']['circuiti_intensi']}

FOCUS STAGIONALE:
=================
Ingredienti prioritari questo mese:
"""
            # seasonal_focus è un dict con chiavi come "novembre"
            for month_key, items in user_guidelines['seasonal_focus'].items():
                for item_desc in items:
                    prompt += f"- {item_desc}\n"
            
            prompt += f"""
BUDGET E RISPARMIO:
===================
"""
            for tip in user_guidelines['budget_tips']:
                prompt += f"- {tip}\n"
            
            prompt += f"""
⚠️  CIBI DA EVITARE ASSOLUTAMENTE:
===================================
"""
            for avoid in user_guidelines['avoid_completely']:
                prompt += f"❌ {avoid}\n"
            
            prompt += """
IMPORTANTE: L'utente NON mangia frutta fresca di nessun tipo. 
Quando servirebbero dolcificanti naturali o fibre dolci, usa:
- Frutta secca (datteri, fichi secchi) in piccole quantità
- Verdure dolci (carote, zucca, barbabietole)
- Miele (con moderazione)
Mai suggerire frutta fresca come spuntino o dessert!
"""
        else:
            # Linee guida generiche
            prompt += """
LINEE GUIDA GENERALI:
=====================
1. Prioritizza ingredienti di stagione e locali
2. Rispetta tutte le restrizioni e preferenze
3. Adatta calorie/macros all'attività della giornata
4. Proponi ricette della cucina italiana tradizionale
5. Indica tempi di preparazione realistici
6. Fornisci quantità precise per ingredienti
7. Nei giorni di allenamento: aumenta proteine e carboidrati
8. Varia i pasti per evitare monotonia
9. Considera il budget dell'utente
10. Se meal prep: suggerisci ricette batch-friendly
"""

        # Regole specifiche basate sul feedback utente
        prompt += """
REGOLE SPECIFICHE DA RISPETTARE (feedback utente):
=================================================
1) Colazione in stile italiano (tendenzialmente dolce):
   - Preferisci yogurt greco, miele, tahina, avena/fiocchi d'avena, biscotti secchi tipo digestive/saraceni, frutta secca (datteri/fichi secchi) in piccole quantità.
   - Evita colazioni salate con uova, spinaci, salumi o piatti da brunch anglosassone.
   - NIENTE frutta fresca (l'utente non la consuma); per dolcezza usa miele o frutta secca.
   - Quinoa: NON proporla a colazione.

2) Panini e pane:
   - Non esiste "panino con farro". Se proponi un panino/sandwich, usa pane integrale (o segale) come base.
   - Se nella generazione compare "panino con farro", correggi in "panino con pane integrale".

3) Varietà delle verdure (cavolo nero):
   - Non usare cavolo nero tutti i giorni. Massimo 2 volte a settimana e non ripetuto più volte nello stesso giorno.
   - Varia tra cavolo verza, bietole/coste, spinaci, cicoria, radicchio, broccoli, zucca, finocchi, ecc.

4) Nomi autentici e coerenza culinaria:
   - Evita nomi inventati o impropri (es: "cipolla alla romana"). Usa denominazioni tradizionali o descrittive precise.
   - Correggi errori di ortografia ("spaghetti", "fagioli").

5) Carboidrati complessi a pranzo e cena:
   - Includi sempre una base tra: pane integrale, pasta integrale, riso integrale, cous cous integrale, farro, orzo, quinoa.

6) Uova:
   - Limite massimo 5–6 uova a settimana complessiva. In generale, non proporre uova a colazione per stile italiano.
"""

        prompt += """
FORMATO RISPOSTA:
=================
Per ogni pasto genera un JSON strutturato con ESATTAMENTE questi campi:
- recipe_name: nome ricetta appetitoso e descrittivo (es: "Zuppa di lenticchie e cavolo nero alla toscana", non "Zuppa")
- ingredients: lista di oggetti [{"nome": "ingrediente", "quantità": "100g"}, ...]
- instructions: lista di stringhe ["Passo 1...", "Passo 2...", ...]
- calories: numero intero (calorie totali)
- macros: {"proteine": X, "carboidrati": Y, "grassi": Z} in grammi (chiavi in italiano!)
- prep_time: numero intero minuti preparazione
- cooking_time: numero intero minuti cottura
- seasonal_score: numero float 0.0-1.0 (quanto usa ingredienti stagionali)
- notes: stringa con consigli per conservazione, varianti, meal prep

LINEE GUIDA RICETTE AUTENTICHE:
================================
🇮🇹 **Ricette Italiane Tradizionali Rivisitate**
- Rispetta le tecniche di cottura tradizionali italiane (soffritto, brasatura, etc)
- Usa combinazioni di sapori classiche (pomodoro+basilico, rosmarino+aglio, salvia+burro)
- Rivisita piatti classici in versione salutare (es: carbonara con yogurt greco)
- Mantieni la struttura dei piatti regionali (zuppe toscane, risotti lombardi, paste siciliane)

🌍 **Ricette Internazionali Autentiche**
- Rispetta le combinazioni di spezie tipiche (curry indiano, ras el hanout marocchino)
- Usa tecniche di cottura originali (stir-fry asiatico, slow cooking messicano)
- Mantieni equilibri di sapori tradizionali (dolce-salato-acido asiatico)
- Adatta ingredienti difficili con alternative locali stagionali

📖 **Esperienza Culinaria e Coerenza**
- Ogni ricetta deve avere una logica culinaria solida e testata
- Tempi di cottura realistici basati su esperienza vera
- Sequenza di preparazione logica: mise en place → cottura base → assemblaggio → finitura
- Tecniche appropriate: soffritto per basi, rosolatura per proteine, mantecatura per cremosità
- Bilanciamento sapori: salato, dolce, acido, amaro, umami
- Temperature e modalità specifiche (fuoco medio, fiamma bassa, etc)

🥘 **Praticità e Meal Prep**
- Ricette batch-friendly: si possono preparare in quantità e conservare
- Istruzioni chiare per conservazione (frigo 3-4 giorni, freezer 2-3 mesi)
- Suggerimenti per riscaldamento ottimale senza perdere qualità
- Varianti per diverse occasioni o ingredienti disponibili

⚠️ **Errori da Evitare**
- ❌ Combinazioni innaturali o fusion senza senso culinario
- ❌ Tempi di cottura irrealistici (es: "cuocere legumi in 5 minuti")
- ❌ Ingredienti incompatibili (yogurt in cottura lunga, limone con latte)
- ❌ Procedure illogiche (spezie aggiunte a fine cottura quando vanno tostate all'inizio)
- ❌ Quantità sproporzionate (troppo olio, troppe spezie, porzioni irreali)
- ❌ Nomi generici: NO "Insalata", "Pasta", "Zuppa" → SÌ "Insalata di farro con ceci e rucola", "Penne integrali al pesto di cavolo nero"

ESEMPIO RICETTA AUTENTICA:
{
  "recipe_name": "Zuppa di lenticchie e cavolo nero alla toscana",
  "ingredients": [
    {"nome": "lenticchie secche", "quantità": "200g"},
    {"nome": "cavolo nero", "quantità": "150g"},
    {"nome": "carote", "quantità": "100g"},
    {"nome": "sedano", "quantità": "50g"},
    {"nome": "cipolla", "quantità": "80g"},
    {"nome": "pomodori pelati", "quantità": "200g"},
    {"nome": "olio extravergine oliva", "quantità": "2 cucchiai"},
    {"nome": "aglio", "quantità": "2 spicchi"},
    {"nome": "rosmarino fresco", "quantità": "1 rametto"},
    {"nome": "brodo vegetale", "quantità": "1 litro"},
    {"nome": "sale", "quantità": "q.b."},
    {"nome": "pepe nero", "quantità": "q.b."}
  ],
  "instructions": [
    "Sciacquare le lenticchie sotto acqua corrente. Se usi lenticchie secche normali, metterle in ammollo 2 ore (le lenticchie rosse non servono ammollo)",
    "Preparare un soffritto classico: in una pentola capiente scaldare l'olio a fuoco medio, aggiungere cipolla tritata fine, carote e sedano a cubetti piccoli. Cuocere 5-7 minuti mescolando fino a doratura leggera",
    "Aggiungere aglio tritato e rosmarino spezzettato, far rosolare 1-2 minuti fino a quando profuma (attenzione a non bruciare l'aglio)",
    "Unire i pomodori pelati schiacciati con una forchetta e far insaporire 3-4 minuti a fuoco medio-alto, mescolando",
    "Aggiungere le lenticchie scolate e il brodo vegetale caldo. Portare a ebollizione vivace",
    "Abbassare il fuoco a medio-basso, coprire con coperchio e cuocere 25-30 minuti (20 min per lenticchie rosse)",
    "A 10 minuti dalla fine cottura, aggiungere il cavolo nero lavato e tagliato a striscioline sottili, mescolare bene",
    "Assaggiare e aggiustare di sale e pepe. Se troppo denso, aggiungere poco brodo caldo",
    "Servire ben calda con un filo d'olio extravergine a crudo e, se gradito, crostini di pane integrale"
  ],
  "calories": 420,
  "macros": {"proteine": 24, "carboidrati": 58, "grassi": 10},
  "prep_time": 20,
  "cooking_time": 35,
  "seasonal_score": 0.95,
  "notes": "Piatto della tradizione toscana povera, nutriente e completo. Si conserva perfettamente in frigo 4 giorni in contenitore ermetico. Ideale per meal prep: riscaldare a fuoco dolce aggiungendo 2-3 cucchiai di brodo per riportare cremosità. Il sapore migliora il giorno dopo quando i sapori si amalgamano. Variante ribollita: aggiungere 50g di pasta corta integrale (ditalini) negli ultimi 10 minuti. Per versione cremosa: frullare metà zuppa e rimescolare. Freezer: congela benissimo, scongelare in frigo la sera prima."
}

⭐ GENERA RICETTE VERE, TESTATE, AUTENTICHE. Come se fossi uno chef professionista con 20 anni di esperienza in cucina italiana e internazionale. Ogni ricetta deve essere replicabile con successo da chiunque seguendo le tue istruzioni.
"""

        # Richiedi esplicitamente il JSON in un blocco di codice per facilitare il parsing
        prompt += "\nATTENZIONE: Quando rispondi, restituisci SOLO il JSON della ricetta racchiuso all'interno di un blocco di codice con linguaggio 'json', ad esempio:\n```json\n{ ... }\n```\nNon inviare testo aggiuntivo prima o dopo il blocco di codice."

        return prompt
    
    def generate_daily_plan(self, date: Optional[str] = None, is_workout_day: bool = False) -> DailyPlan:
        """
        Genera piano pasti per una giornata.
        
        Args:
            date: Data in formato YYYY-MM-DD (default: oggi)
            is_workout_day: True se è un giorno di allenamento
            
        Returns:
            DailyPlan completo con tutti i pasti
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Determina pasti da generare
        meal_types = [
            MealType.COLAZIONE,
            MealType.SPUNTINO_MATTINA,
            MealType.PRANZO,
            MealType.SPUNTINO_POMERIGGIO,
            MealType.CENA
        ]
        
        if is_workout_day and self.profile.workout_time == "pomeriggio":
            meal_types.append(MealType.POST_WORKOUT)
        
        meals = []
        for meal_type in meal_types:
            meal = self._generate_meal(date, meal_type, is_workout_day)
            meals.append(meal)
        
        # Calcola totali
        total_calories = sum(m.calories for m in meals)
        total_macros = {
            "proteine": sum(m.macros.get("proteine", 0) for m in meals),
            "carboidrati": sum(m.macros.get("carboidrati", 0) for m in meals),
            "grassi": sum(m.macros.get("grassi", 0) for m in meals)
        }
        
        # Genera lista della spesa
        shopping_list = self._generate_shopping_list(meals)
        
        daily_plan = DailyPlan(
            date=date,
            is_workout_day=is_workout_day,
            meals=meals,
            total_calories=total_calories,
            total_macros=total_macros,
            shopping_list=shopping_list,
            notes=f"Piano generato per {date} - {'Giorno allenamento' if is_workout_day else 'Giorno riposo'}"
        )
        
        # Salva nello storico - usa dict normale per evitare problemi con enum
        # La conversione JSON-safe verrà fatta da _save_meal_history()
        plan_dict = asdict(daily_plan)
        self.meal_history.append(plan_dict)
        self._save_meal_history()
        
        return daily_plan
    
    def _generate_meal(self, date: str, meal_type: MealType, is_workout_day: bool) -> MealPlan:
        """Genera un singolo pasto"""
        
        # Context per AI
        context = f"""Genera una ricetta per {meal_type.value} del {date}.

Giorno di allenamento: {'Sì' if is_workout_day else 'No'}

Requisiti specifici per {meal_type.value}:
"""
        
        if meal_type == MealType.COLAZIONE:
            context += (
                "- Energetica ma leggera\n"
                "- 300-500 calorie\n"
                "- Proteine: 20-30g\n"
                "- Stile italiano tendenzialmente dolce: yogurt greco, miele, tahina, avena/fiocchi d'avena, biscotti secchi, frutta secca (no frutta fresca)\n"
                "- Evita uova/salato a colazione.\n"
                "- Vietato usare quinoa a colazione.\n"
            )
        elif meal_type == MealType.PRANZO:
            if is_workout_day:
                context += (
                    "- Bilanciata con focus su carboidrati complessi\n"
                    "- 500-700 calorie\n"
                    "- Proteine: 35-45g\n"
                    "- Includi sempre una base tra: pane integrale, pasta integrale, riso integrale, cous cous integrale, farro, orzo, quinoa.\n"
                    "- Varia le verdure; non usare cavolo nero tutti i giorni.\n"
                    "- Per panini/sandwich non usare 'panino con farro': usa pane integrale.\n"
                )
            else:
                context += (
                    "- Bilanciata\n"
                    "- 400-600 calorie\n"
                    "- Proteine: 30-40g\n"
                    "- Includi sempre una base tra: pane integrale, pasta integrale, riso integrale, cous cous integrale, farro, orzo, quinoa.\n"
                    "- Varia le verdure; non usare cavolo nero tutti i giorni.\n"
                    "- Per panini/sandwich non usare 'panino con farro': usa pane integrale.\n"
                )
        elif meal_type == MealType.CENA:
            context += (
                "- Leggera e digeribile\n"
                "- 400-600 calorie\n"
                "- Proteine: 30-40g\n"
                "- Includi sempre una base tra: pane integrale, pasta integrale, riso integrale, cous cous integrale, farro, orzo, quinoa.\n"
                "- Varia le verdure; non usare cavolo nero tutti i giorni.\n"
                "- Per panini/sandwich non usare 'panino con farro': usa pane integrale.\n"
            )
        elif meal_type in [MealType.SPUNTINO_MATTINA, MealType.SPUNTINO_POMERIGGIO]:
            context += "- Leggero e nutriente\n- 150-250 calorie\n- Proteine: 10-15g\n"
        elif meal_type == MealType.POST_WORKOUT:
            context += "- Recovery focused\n- Proteine + carboidrati\n- 300-400 calorie\n- Proteine: 25-35g\n"
        
        context += "\nGenera SOLO il JSON della ricetta, senza commenti aggiuntivi."
        
        # Genera con AI usando invoke()
        prompt = f"{self._build_system_prompt()}\n\n{context}"
        response = self.client.invoke(input=prompt, max_tokens=2000)
        
        # Parse risposta (più robusto e con logging raw on failure)
        try:
            text = response.text or ""

            # Prefer code-fenced JSON blocks
            candidate = None
            if "```json" in text:
                candidate = text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in text:
                candidate = text.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                candidate = text.strip()

            meal_data = None
            
            def _pre_fix_values(s: str) -> str:
                """Heuristic fixes for common LLM JSON issues on values.
                - Quote unquoted quantity values like 100g, 1 cucchiaio, 50 g, q.b., etc.
                - Keep numeric fields (calories, prep_time, cooking_time, macros) untouched.
                """
                import re
                t = s
                # Quote unquoted quantities for keys quantità/quantity
                # pattern: "quantità" : 100g  -> "quantità": "100g"
                t = re.sub(r'("quantità"|"quantity")\s*:\s*([0-9]+\s*[a-zA-Z\.]+)', r'\1: "\2"', t)
                # Also handle cases like 1 cucchiaio, 2 cucchiai, 50 ml, 1/2 cucchiaino
                t = re.sub(r'("quantità"|"quantity")\s*:\s*([0-9]+\s*/?[0-9]*\s*[a-zA-ZàèéìòùÀÈÉÌÒÙ\.]+)', r'\1: "\2"', t)
                # Quote q.b. if unquoted
                t = re.sub(r'("quantità"|"quantity")\s*:\s*(q\.b\.)', r'\1: "q.b."', t)
                # For ingredient-level dicts missing quotes around units with decimals/commas (e.g., 0,5 cucchiaino)
                t = re.sub(r'("quantità"|"quantity")\s*:\s*([0-9]+[,\.]?[0-9]*\s*[a-zA-ZàèéìòùÀÈÉÌÒÙ\.]+)', r'\1: "\2"', t)
                return t

            # First try direct load
            try:
                meal_data = json.loads(candidate)
            except Exception:
                # Heuristic fixes
                import re
                fixed = candidate.replace("'", '"')
                fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
                fixed = re.sub(r'([\{,\n\s])([A-Za-z0-9_]+)\s*:', lambda m: f'{m.group(1)}"{m.group(2)}":', fixed)
                fixed = _pre_fix_values(fixed)
                try:
                    meal_data = json.loads(fixed)
                except Exception:
                    # Try to find balanced JSON blocks in the whole response
                    import re as _re
                    # Find all candidate JSON-like blocks
                    blocks = _re.findall(r"(\{(?:.|\n)*?\})|(\[(?:.|\n)*?\])", text)
                    best_candidate = None
                    for b in blocks:
                        blk = b[0] or b[1]
                        if not blk:
                            continue
                        # Try parse with fixes
                        cand = blk.replace("'", '"')
                        cand = _re.sub(r",\s*([}\]])", r"\1", cand)
                        cand = _re.sub(r'([\{,\n\s])([A-Za-z0-9_]+)\s*:', lambda m: f'{m.group(1)}"{m.group(2)}":', cand)
                        cand = _pre_fix_values(cand)
                        try:
                            obj = json.loads(cand)
                        except Exception:
                            continue
                        # If it's a list, search for a dict with required keys
                        def pick_valid(o):
                            if isinstance(o, dict) and all(k in o for k in ("recipe_name", "ingredients")):
                                return o
                            if isinstance(o, list):
                                for it in o:
                                    if isinstance(it, dict) and all(k in it for k in ("recipe_name", "ingredients")):
                                        return it
                            return None
                        chosen = pick_valid(obj)
                        if chosen is not None:
                            best_candidate = chosen
                            break
                    meal_data = best_candidate

            if meal_data is None:
                # salva la risposta raw su disco per debugging
                try:
                    cache_dir = Path(__file__).parent / ".cache"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    last_path = cache_dir / "last_response.txt"
                    with open(last_path, "w", encoding="utf-8") as f:
                        f.write(text)
                except Exception:
                    pass
                raise ValueError("No valid JSON found in LLM response")

            # Normalizza i macros (gestisci chiavi inglesi/italiane)
            macros = meal_data.get("macros", {})
            normalized_macros = {
                "proteine": float(macros.get("proteine") or macros.get("protein") or macros.get("proteins") or 0),
                "carboidrati": float(macros.get("carboidrati") or macros.get("carbs") or macros.get("carbohydrates") or 0),
                "grassi": float(macros.get("grassi") or macros.get("fats") or macros.get("fat") or 0)
            }
            
            meal_plan = MealPlan(
                date=date,
                meal_type=meal_type,
                recipe_name=meal_data["recipe_name"],
                ingredients=meal_data["ingredients"],
                instructions=meal_data["instructions"],
                calories=int(meal_data["calories"]),
                macros=normalized_macros,
                prep_time=int(meal_data.get("prep_time", 0)),
                cooking_time=int(meal_data.get("cooking_time", 0)),
                notes=meal_data.get("notes", ""),
                seasonal_score=meal_data.get("seasonal_score", 0.8)
            )
            
            return meal_plan
            
        except Exception as e:
            print(f"❌ Errore parsing risposta AI: {e}")
            print(f"Risposta raw: {response.text}")
            # Fallback
            return self._generate_fallback_meal(date, meal_type)
    
    def _generate_fallback_meal(self, date: str, meal_type: MealType) -> MealPlan:
        """Genera un pasto fallback se AI fallisce"""
        return MealPlan(
            date=date,
            meal_type=meal_type,
            recipe_name="Pasto da definire",
            ingredients=[],
            instructions=["Errore generazione - riprova"],
            calories=0,
            macros={"proteine": 0, "carboidrati": 0, "grassi": 0},
            prep_time=0,
            cooking_time=0,
            notes="Generazione fallita - riprovare"
        )
    
    def _generate_shopping_list(self, meals: List[MealPlan]) -> List[str]:
        """Genera lista della spesa consolidata"""
        ingredients_dict = {}
        
        for meal in meals:
            for ingredient in meal.ingredients:
                # Gestisci diverse strutture JSON
                if isinstance(ingredient, dict):
                    # Prova diverse chiavi possibili per il nome
                    name = (
                        ingredient.get("nome") or 
                        ingredient.get("name") or 
                        ingredient.get("ingrediente") or 
                        ingredient.get("ingredient") or
                        str(ingredient.get("item", "ingrediente sconosciuto"))
                    ).lower()
                    
                    # Prova diverse chiavi possibili per la quantità
                    qty = (
                        ingredient.get("quantità") or 
                        ingredient.get("quantity") or 
                        ingredient.get("qty") or 
                        ingredient.get("amount") or
                        "q.b."
                    )
                elif isinstance(ingredient, str):
                    # Se è una stringa, usala direttamente
                    name = ingredient.lower()
                    qty = "q.b."
                else:
                    # Fallback
                    name = str(ingredient).lower()
                    qty = "q.b."
                
                if name in ingredients_dict:
                    ingredients_dict[name] += f", {qty}"
                else:
                    ingredients_dict[name] = qty
        
        shopping_list = [f"{name}: {qty}" for name, qty in ingredients_dict.items()]
        return sorted(shopping_list)
    
    def generate_weekly_plan(self, start_date: Optional[str] = None) -> List[DailyPlan]:
        """
        Genera piano settimanale completo.
        
        Args:
            start_date: Data inizio (default: lunedì prossimo)
            
        Returns:
            Lista di 7 DailyPlan
        """
        if not start_date:
            # Prossimo lunedì
            today = datetime.now()
            days_ahead = 0 - today.weekday()  # lunedì = 0
            if days_ahead <= 0:
                days_ahead += 7
            start = today + timedelta(days=days_ahead)
            start_date = start.strftime("%Y-%m-%d")
        
        weekly_plans = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        
        weekday_map = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
        
        for i in range(7):
            current_date = start + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            weekday = weekday_map[current_date.weekday()]
            
            is_workout = weekday in (self.profile.workout_days or [])
            
            print(f"📅 Generando piano per {weekday} {date_str} {'💪' if is_workout else '🏠'}")
            daily_plan = self.generate_daily_plan(date_str, is_workout)
            weekly_plans.append(daily_plan)
        
        return weekly_plans
    
    def get_meal_suggestions(self, meal_type: MealType, preferences: Dict | None = None) -> List[str]:
        """
        Ottieni suggerimenti veloci per un tipo di pasto.
        
        Args:
            meal_type: Tipo pasto
            preferences: Preferenze extra (es: {"veloce": True, "proteico": True})
            
        Returns:
            Lista di nomi ricette suggerite
        """
        context = f"""Suggerisci 5 ricette diverse per {meal_type.value}.

Preferenze extra: {preferences or 'nessuna'}

Risposta in formato: lista semplice di nomi ricette, uno per riga."""

        # Usa invoke() invece di generate_content()
        prompt = f"{self._build_system_prompt()}\n\n{context}"
        response = self.client.invoke(input=prompt, max_tokens=500)
        
        suggestions = [line.strip("- ").strip() for line in response.text.split("\n") if line.strip()]
        return suggestions[:5]
    
    def analyze_nutrition_goals(self) -> str:
        """Analizza progressi verso obiettivi nutrizionali"""
        
        # Ultimi 7 giorni
        recent_history = self.meal_history[-7:] if len(self.meal_history) >= 7 else self.meal_history
        
        if not recent_history:
            return "📊 Nessuno storico disponibile. Inizia a generare piani pasti!"
        
        avg_calories = sum(day["total_calories"] for day in recent_history) / len(recent_history)
        avg_protein = sum(day["total_macros"]["proteine"] for day in recent_history) / len(recent_history)
        
        seasonal_scores = []
        for day in recent_history:
            for meal in day["meals"]:
                seasonal_scores.append(meal.get("seasonal_score", 0))
        avg_seasonal = sum(seasonal_scores) / len(seasonal_scores) if seasonal_scores else 0
        
        report = f"""📊 ANALISI NUTRIZIONALE - Ultimi {len(recent_history)} giorni

Calorie medie: {avg_calories:.0f} kcal/giorno
Proteine medie: {avg_protein:.1f}g/giorno
Score stagionalità: {avg_seasonal:.1%}

Obiettivo: {self.profile.dietary_goal.value}
Status: {'✅ On track' if abs(avg_calories - 2000) < 300 else '⚠️ Da aggiustare'}

Prossimi step:
1. Continua a prioritizzare ingredienti stagionali
2. Monitora apporto proteico per supportare allenamenti
3. Varia le fonti di carboidrati e grassi sani
"""
        return report


def create_sample_profile() -> UserProfile:
    """Crea profilo di esempio per test"""
    return UserProfile(
        name="Antonio",
        age=35,
        weight=75.0,
        height=175.0,
        activity_level=ActivityLevel.MODERATO,
        dietary_goal=DietaryGoal.PERFORMANCE,
        preferred_foods=["pollo", "riso", "verdure", "pesce", "avocado", "noci"],
        disliked_foods=["funghi", "cozze"],
        allergies=[],
        intolerances=[],
        vegetarian=False,
        vegan=False,
        gluten_free=False,
        dairy_free=False,
        workout_days=["lunedì", "mercoledì", "venerdì"],
        workout_time="pomeriggio",
        meal_times={
            "colazione": "07:30",
            "pranzo": "13:00",
            "cena": "20:00"
        },
        cooking_time_available="medio",
        budget_level="medio",
        meal_prep=True
    )


if __name__ == "__main__":
    print("🥗 Nutrition Agent - Test")
    print("="*50)
    
    # Test con profilo sample
    profile = create_sample_profile()
    print(f"\n✅ Profilo creato: {profile.name}")
    print(f"   Obiettivo: {profile.dietary_goal.value}")
    print(f"   Attività: {profile.activity_level.value}")
