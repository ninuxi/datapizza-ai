"""
🥗 Profilo Personalizzato - Antonio Mainenti
============================================

Profilo nutrizionale personalizzato basato su preferenze e obiettivi specifici.
"""

from datetime import datetime
from nutrition_agent import UserProfile, ActivityLevel, DietaryGoal

def create_antonio_profile() -> UserProfile:
    """
    Crea profilo personalizzato per Antonio Mainenti.
    
    DATI PERSONALI:
    - Nato: 5 febbraio 1978 (47 anni)
    - Peso: 74 kg
    - Altezza: 173 cm
    - Obiettivi: Perdere peso + mettere muscoli + alimentazione sana
    
    ALLENAMENTO:
    - Frequenza: 3-4 giorni/settimana
    - Tipo: Circuiti intensi 30min + Calisthenics
    - Giorni: Flessibili (no preferenze)
    - Orari: Flessibili (no preferenze)
    
    ALIMENTAZIONE:
    - Filosofia: Flexitariano (pochissima carne)
    - Priorità: Verdure stagione, legumi, cereali integrali
    - Evita: Pollo, volatili, frutta, pesce (troppo caro)
    - Colazione: Yogurt/kefir, pane, tahina, miele
    - Cena: Preferisce abbondante (ma sa che dovrebbe essere più leggera)
    
    STILE CUCINA:
    - Skill: Buono, ma non vuole cucinare per ore
    - Meal prep: SÌ! (es: bollire legumi in batch)
    - Importanza stagionalità: MASSIMA
    - Cereali: Solo integrali (riso, pasta, pane, quinoa, farro, orzo)
    """
    
    # Calcola età
    birth_date = datetime(1978, 2, 5)
    age = (datetime.now() - birth_date).days // 365
    
    return UserProfile(
        name="Antonio",
        age=age,
        weight=74.0,
        height=173.0,
        activity_level=ActivityLevel.MODERATO,  # 3-4 giorni/settimana
        dietary_goal=DietaryGoal.DIMAGRIMENTO,  # Perdere peso (ma anche muscoli)
        
        # Cibi amati
        preferred_foods=[
            # Verdure (stagionali)
            "verdure di stagione", "verdure a foglia verde", "broccoli", "cavolfiore", 
            "zucca", "carciofi", "spinaci", "radicchio", "finocchi", "pomodori",
            "melanzane", "zucchine", "peperoni", "cavolo nero",
            
            # Legumi (base alimentazione)
            "legumi", "lenticchie", "ceci", "fagioli", "fagioli neri", 
            "fagioli borlotti", "piselli", "fave", "lupini",
            
            # Cereali integrali
            "riso integrale", "pasta integrale", "pane integrale", 
            "quinoa", "farro", "orzo", "avena integrale", "bulgur",
            
            # Proteine
            "uova", "tofu", "tempeh", "seitan",  # Flexitariano
            
            # Colazione
            "yogurt", "kefir", "tahina", "miele", "frutta secca", "noci", "mandorle",
            
            # Grassi sani
            "olio extravergine oliva", "avocado", "semi di lino", "semi di chia",
            
            # Occasionalmente
            "pesce" # (ma poco per costo)
        ],
        
        # Cibi da evitare
        disliked_foods=[
            "pollo", "tacchino", "volatili in generale",
            "frutta", "frutta fresca", "frutta di stagione",  # NON mangia frutta
            "pesce" # (troppo caro, quindi limita)
        ],
        
        # Nessuna allergia/intolleranza
        allergies=[],
        intolerances=[],
        
        # Restrizioni dietetiche
        vegetarian=False,  # Flexitariano (pochissima carne)
        vegan=False,
        gluten_free=False,
        dairy_free=False,
        
        # Allenamento: Flessibile
        # Nota: Assegno giorni distribuiti ma l'utente può cambiarli
        workout_days=["lunedì", "mercoledì", "venerdì"],  # 3-4 giorni, flessibili
        workout_time="pomeriggio",  # Default, ma flessibile
        
        # Orari pasti (da chiedere conferma)
        meal_times={
            "colazione": "07:30",
            "pranzo": "13:00",
            "cena": "20:00"
        },
        
        # Stile cucina
        cooking_time_available="medio",  # Sa cucinare ma non vuole ore
        budget_level="medio",
        meal_prep=True  # IMPORTANTE: Batch cooking (es: legumi bolliti)
    )


def get_nutrition_guidelines_antonio() -> dict:
    """
    Linee guida nutrizionali specifiche per Antonio.
    
    Returns:
        dict con note personalizzate per l'AI
    """
    return {
        "philosophy": "Flexitariano - pochissima carne, focus vegetali",
        
        "priorities": [
            "Verdure di stagione (base di ogni pasto)",
            "Legumi come fonte proteica principale",
            "Cereali solo integrali (mai raffinati)",
            "Meal prep friendly (batch cooking legumi)",
            "NO frutta (sostituti: verdure, frutta secca)",
            "Colazione: yogurt/kefir + pane + tahina + miele",
            "Proteine: legumi > uova > tofu/seitan > pesce occasionale",
            "NO pollo, tacchino, volatili"
        ],
        
        "macros_target": {
            "note": "Dimagrimento + muscoli = deficit calorico moderato + proteine alte",
            "calories_range": "1800-2100 kcal/giorno",
            "protein_target": "130-150g/giorno (1.8-2g per kg)",
            "carbs": "Moderati, da fonti integrali",
            "fats": "Grassi sani da olio EVO, frutta secca, avocado"
        },
        
        "meal_structure": {
            "colazione": "Yogurt/kefir + pane integrale + tahina + miele (300-400 kcal)",
            "pranzo": "Abbondante e bilanciato - legumi + cereali integrali + verdure (500-600 kcal)",
            "cena": "Leggera ma saziante - proteine + verdure abbondanti (400-500 kcal)",
            "spuntini": "Frutta secca, hummus, verdure crude"
        },
        
        "batch_cooking": [
            "Legumi: Bollire 500g-1kg alla volta, conservare in frigo 3-4 giorni",
            "Cereali: Cuocere riso/farro/quinoa in batch",
            "Verdure: Prep verdure crude già tagliate",
            "Salse: Hummus, tahina, pesto fatto in casa"
        ],
        
        "seasonal_focus": {
            "novembre": [
                "Verdure: cavolo, broccoli, cavolfiore, zucca, carciofi, spinaci, radicchio",
                "Legumi: sempre (secchi o in barattolo)",
                "No frutta: sostituire con verdure dolci (zucca) e frutta secca"
            ]
        },
        
        "workout_nutrition": {
            "pre_workout": "Carboidrati integrali (riso, farro) 1-2h prima",
            "post_workout": "Proteine (legumi/uova/tofu) + carboidrati integrali",
            "circuiti_intensi": "Focus recupero con proteine + verdure antiossidanti"
        },
        
        "budget_tips": [
            "Legumi secchi (più economici che in scatola)",
            "Verdure di stagione al mercato",
            "Cereali integrali in bulk",
            "Uova come proteine economiche",
            "Pesce solo occasionale (quando in offerta)"
        ],
        
        "avoid_completely": [
            "Pollo e volatili (tutti)",
            "Frutta fresca (anche se di stagione)",
            "Cereali raffinati (pasta bianca, riso bianco, pane bianco)"
        ]
    }


if __name__ == "__main__":
    print("🥗 Profilo Personalizzato - Antonio Mainenti")
    print("="*60)
    
    profile = create_antonio_profile()
    guidelines = get_nutrition_guidelines_antonio()
    
    print(f"\n✅ PROFILO CREATO")
    print(f"   Nome: {profile.name}")
    print(f"   Età: {profile.age} anni")
    print(f"   Peso: {profile.weight} kg")
    print(f"   Altezza: {profile.height} cm")
    print(f"   Obiettivo: {profile.dietary_goal.value}")
    print(f"   Attività: {profile.activity_level.value}")
    
    print(f"\n🍽️ PREFERENZE ALIMENTARI")
    print(f"   Filosofia: {guidelines['philosophy']}")
    print(f"   Cibi preferiti: {len(profile.preferred_foods)} categorie")
    print(f"   Da evitare: {', '.join(profile.disliked_foods[:3])}...")
    print(f"   Meal prep: {'✅ Sì' if profile.meal_prep else '❌ No'}")
    
    print(f"\n💪 ALLENAMENTO")
    print(f"   Frequenza: 3-4 giorni/settimana")
    print(f"   Tipo: Circuiti intensi + Calisthenics")
    print(f"   Giorni: Flessibili")
    
    print(f"\n📊 TARGET NUTRIZIONALI")
    print(f"   Calorie: {guidelines['macros_target']['calories_range']}")
    print(f"   Proteine: {guidelines['macros_target']['protein_target']}")
    
    print(f"\n🌱 FOCUS STAGIONALITÀ")
    for veg in guidelines['seasonal_focus']['novembre'][:3]:
        print(f"   • {veg}")
    
    print("\n" + "="*60)
    print("✨ Profilo pronto per l'uso!")
