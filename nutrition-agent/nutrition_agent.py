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

# Import datapizza AI
sys.path.insert(0, str(Path(__file__).parent.parent / "datapizza-ai-core"))
from datapizza.clients.google import GoogleClient


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
    
    def __init__(self, google_client: GoogleClient, user_profile: UserProfile, data_dir: str = "data/nutrition"):
        """
        Inizializza Nutrition Agent.
        
        Args:
            google_client: Client Google Gemini
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
        with open(self.meal_history_file, 'w') as f:
            json.dump(self.meal_history, f, indent=2)
    
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

        prompt += """
FORMATO RISPOSTA:
=================
Per ogni pasto genera un JSON strutturato con:
- recipe_name: nome ricetta appetitoso e descrittivo
- ingredients: lista ingredienti con quantità precise
- instructions: step by step chiari e numerati
- calories: calorie totali stimate
- macros: {"protein": X, "carbs": Y, "fats": Z} in grammi
- prep_time: minuti preparazione
- cooking_time: minuti cottura
- seasonal_score: 0.0-1.0 (quanto usa ingredienti stagionali)
- notes: consigli per conservazione, varianti, meal prep

Sii creativo ma pratico. L'utente vuole mangiare sano senza stress.
Ricette della tradizione italiana rivisitate in chiave salutare.
"""

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
        
        # Salva nello storico
        self.meal_history.append(asdict(daily_plan))
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
            context += "- Energetica ma leggera\n- 300-500 calorie\n- Proteine: 20-30g\n"
        elif meal_type == MealType.PRANZO:
            if is_workout_day:
                context += "- Bilanciata con focus su carboidrati complessi\n- 500-700 calorie\n- Proteine: 35-45g\n"
            else:
                context += "- Bilanciata\n- 400-600 calorie\n- Proteine: 30-40g\n"
        elif meal_type == MealType.CENA:
            context += "- Leggera e digeribile\n- 400-600 calorie\n- Proteine: 30-40g\n"
        elif meal_type in [MealType.SPUNTINO_MATTINA, MealType.SPUNTINO_POMERIGGIO]:
            context += "- Leggero e nutriente\n- 150-250 calorie\n- Proteine: 10-15g\n"
        elif meal_type == MealType.POST_WORKOUT:
            context += "- Recovery focused\n- Proteine + carboidrati\n- 300-400 calorie\n- Proteine: 25-35g\n"
        
        context += "\nGenera SOLO il JSON della ricetta, senza commenti aggiuntivi."
        
        # Genera con AI usando invoke()
        prompt = f"{self._build_system_prompt()}\n\n{context}"
        response = self.client.invoke(input=prompt, max_tokens=2000)
        
        # Parse risposta
        try:
            # Estrai JSON dalla risposta
            text = response.text
            # Rimuovi markdown code blocks se presenti
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            meal_data = json.loads(text)
            
            meal_plan = MealPlan(
                date=date,
                meal_type=meal_type,
                recipe_name=meal_data["recipe_name"],
                ingredients=meal_data["ingredients"],
                instructions=meal_data["instructions"],
                calories=meal_data["calories"],
                macros=meal_data["macros"],
                prep_time=meal_data["prep_time"],
                cooking_time=meal_data["cooking_time"],
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
                name = ingredient["nome"].lower()
                qty = ingredient["quantità"]
                
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
