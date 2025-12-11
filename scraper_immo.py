"""
Scraper immobilier via Apify
Zones : 10km autour de Vergt et Le Bugue (Dordogne)
"""

import urllib.request
import urllib.parse
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
TIMEZONE_FRANCE = ZoneInfo("Europe/Paris")

# === ZONES DE RECHERCHE ===

# Codes postaux et communes dans un rayon de 10km autour de Vergt
ZONE_VERGT = {
    "centre": "Vergt",
    "code_postal_principal": "24380",
    "communes": [
        "Vergt", "Église-Neuve-de-Vergt", "Grun-Bordas", "Saint-Michel-de-Double",
        "Salon", "Fouleix", "Breuilh", "Chalagnac", "Creyssensac-et-Pissot",
        "Saint-Mayme-de-Péreyrol", "Lacropte", "Cendrieux", "Saint-Félix-de-Villadeix"
    ],
    "codes_postaux": ["24380", "24400", "24420"]
}

# Codes postaux et communes dans un rayon de 10km autour du Bugue
ZONE_BUGUE = {
    "centre": "Le Bugue",
    "code_postal_principal": "24260",
    "communes": [
        "Le Bugue", "Campagne", "Saint-Chamassy", "Limeuil", "Audrix",
        "Mauzens-et-Miremont", "Les Eyzies", "Journiac", "Le Buisson-de-Cadouin",
        "Saint-Avit-Sénieur", "Trémolat", "Paunat", "Sainte-Alvère"
    ],
    "codes_postaux": ["24260", "24480", "24510", "24220"]
}

# === FONCTIONS APIFY ===

def lancer_scraping_leboncoin(zone: dict) -> dict:
    """Lance un scraping LeBonCoin via Apify pour une zone donnée"""
    
    if not APIFY_TOKEN:
        return {"error": "APIFY_TOKEN non configuré"}
    
    # Actor LeBonCoin sur Apify (on utilise un scraper générique)
    actor_id = "drobnikj/crawler-leboncoin"
    
    # Construction de la recherche
    search_urls = []
    for cp in zone["codes_postaux"]:
        # URL LeBonCoin pour ventes immobilières dans ce code postal
        url = f"https://www.leboncoin.fr/recherche?category=9&locations={cp}&owner_type=all"
        search_urls.append(url)
    
    input_data = {
        "startUrls": [{"url": url} for url in search_urls],
        "maxItems": 100,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        }
    }
    
    return executer_actor_apify(actor_id, input_data)


def lancer_scraping_seloger(zone: dict) -> dict:
    """Lance un scraping SeLoger via Apify pour une zone donnée"""
    
    if not APIFY_TOKEN:
        return {"error": "APIFY_TOKEN non configuré"}
    
    # On utilise le Website Content Crawler d'Apify
    actor_id = "apify/website-content-crawler"
    
    search_urls = []
    for commune in zone["communes"][:5]:  # Limiter pour ne pas exploser les crédits
        commune_slug = commune.lower().replace(" ", "-").replace("é", "e").replace("è", "e")
        url = f"https://www.seloger.com/immobilier/achat/immo-{commune_slug}-24/"
        search_urls.append(url)
    
    input_data = {
        "startUrls": [{"url": url} for url in search_urls],
        "maxCrawlPages": 20,
        "crawlerType": "cheerio"
    }
    
    return executer_actor_apify(actor_id, input_data)


def lancer_scraping_bienici(zone: dict) -> dict:
    """Lance un scraping Bien'ici via Apify"""
    
    if not APIFY_TOKEN:
        return {"error": "APIFY_TOKEN non configuré"}
    
    actor_id = "apify/website-content-crawler"
    
    # Bien'ici utilise des recherches par zone géographique
    # On cherche par département + filtres
    input_data = {
        "startUrls": [
            {"url": "https://www.bienici.com/recherche/achat/dordogne-24?page=1"}
        ],
        "maxCrawlPages": 50,
        "crawlerType": "playwright"  # Nécessaire car site dynamique
    }
    
    return executer_actor_apify(actor_id, input_data)


def executer_actor_apify(actor_id: str, input_data: dict) -> dict:
    """Exécute un actor Apify et retourne les résultats"""
    
    try:
        # Lancer l'actor
        url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"
        
        data = json.dumps(input_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            run_id = result.get('data', {}).get('id')
            
            if run_id:
                return {
                    "status": "started",
                    "run_id": run_id,
                    "actor": actor_id,
                    "message": f"Scraping lancé, ID: {run_id}"
                }
            else:
                return {"error": "Pas de run_id retourné", "response": result}
                
    except Exception as e:
        return {"error": str(e)}


def recuperer_resultats_apify(run_id: str) -> list:
    """Récupère les résultats d'un run Apify terminé"""
    
    try:
        url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode())
            
    except Exception as e:
        return [{"error": str(e)}]


def verifier_status_run(run_id: str) -> dict:
    """Vérifie le status d'un run Apify"""
    
    try:
        url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "status": data.get('data', {}).get('status'),
                "finished": data.get('data', {}).get('finishedAt')
            }
            
    except Exception as e:
        return {"error": str(e)}


# === FONCTION PRINCIPALE DE VEILLE ===

def lancer_veille_complete():
    """Lance une veille complète sur les deux zones"""
    
    timestamp = datetime.now(TIMEZONE_FRANCE).strftime("%Y-%m-%d %H:%M")
    resultats = {
        "timestamp": timestamp,
        "zones": {}
    }
    
    # Zone Vergt
    print(f"[{timestamp}] Lancement veille zone Vergt...")
    resultats["zones"]["vergt"] = {
        "leboncoin": lancer_scraping_leboncoin(ZONE_VERGT)
    }
    
    # Zone Le Bugue
    print(f"[{timestamp}] Lancement veille zone Le Bugue...")
    resultats["zones"]["bugue"] = {
        "leboncoin": lancer_scraping_leboncoin(ZONE_BUGUE)
    }
    
    return resultats


def generer_rapport_biens(biens: list) -> str:
    """Génère un rapport texte des biens trouvés"""
    
    if not biens:
        return "Aucun bien trouvé."
    
    rapport = []
    for i, bien in enumerate(biens[:50], 1):  # Limiter à 50
        titre = bien.get('title', bien.get('titre', 'Sans titre'))
        prix = bien.get('price', bien.get('prix', 'Prix non indiqué'))
        lieu = bien.get('location', bien.get('lieu', 'Lieu non précisé'))
        url = bien.get('url', bien.get('link', ''))
        
        rapport.append(f"{i}. {titre}")
        rapport.append(f"   Prix: {prix} | Lieu: {lieu}")
        if url:
            rapport.append(f"   {url}")
        rapport.append("")
    
    return "\n".join(rapport)


# === TEST ===

if __name__ == "__main__":
    print("=== Test du scraper immobilier ===")
    print(f"Token Apify: {'Configuré' if APIFY_TOKEN else 'MANQUANT'}")
    print(f"Zone Vergt: {len(ZONE_VERGT['communes'])} communes")
    print(f"Zone Le Bugue: {len(ZONE_BUGUE['communes'])} communes")
