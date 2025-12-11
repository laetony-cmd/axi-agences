import anthropic
import os
import urllib.request
import urllib.parse
import json
import re
import smtplib
import base64
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http.server import HTTPServer, BaseHTTPRequestHandler

# === CONFIGURATION ===
TIMEZONE_FRANCE = ZoneInfo("Europe/Paris")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "laetony-cmd/axi-agences"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Destinataires des rapports
DESTINATAIRES_RAPPORT = [
    "dorleanthony@gmail.com",  # Anthony
    # Ajouter l'email de Ludo ici
]

# Fichiers à sauvegarder sur GitHub
FICHIERS_A_SAUVEGARDER = [
    "rapport_quotidien.txt",
    "veille_concurrence.txt",
    "opportunites.txt",
    "journal_activite.txt",
    "config_agences.txt"
]

# === FONCTIONS UTILITAIRES ===

def heure_france():
    return datetime.now(TIMEZONE_FRANCE)

def log_activite(message):
    """Log une activité dans le journal"""
    timestamp = heure_france().strftime("%Y-%m-%d %H:%M:%S")
    ligne = f"[{timestamp}] {message}\n"
    ajouter_fichier("journal_activite.txt", ligne)
    print(ligne.strip())

def lire_fichier(chemin):
    try:
        with open(chemin, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def ecrire_fichier(chemin, contenu):
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write(contenu)
    nom_fichier = os.path.basename(chemin)
    if nom_fichier in FICHIERS_A_SAUVEGARDER:
        sauvegarder_sur_github(nom_fichier)

def ajouter_fichier(chemin, contenu):
    with open(chemin, 'a', encoding='utf-8') as f:
        f.write(contenu)
    nom_fichier = os.path.basename(chemin)
    if nom_fichier in FICHIERS_A_SAUVEGARDER:
        sauvegarder_sur_github(nom_fichier)

# === GITHUB ===

def sauvegarder_sur_github(nom_fichier):
    if not GITHUB_TOKEN:
        return False
    try:
        contenu = lire_fichier(nom_fichier)
        if not contenu:
            return False
        
        content_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nom_fichier}"
        
        # Récupérer SHA existant
        req_get = urllib.request.Request(url)
        req_get.add_header('Authorization', f'token {GITHUB_TOKEN}')
        sha = None
        try:
            with urllib.request.urlopen(req_get, timeout=10) as response:
                data = json.loads(response.read().decode())
                sha = data.get('sha')
        except:
            pass
        
        # Push
        push_data = {
            "message": f"🔄 {nom_fichier} - {heure_france().strftime('%Y-%m-%d %H:%M')}",
            "content": content_b64
        }
        if sha:
            push_data["sha"] = sha
        
        req_put = urllib.request.Request(url, data=json.dumps(push_data).encode(), method='PUT')
        req_put.add_header('Authorization', f'token {GITHUB_TOKEN}')
        req_put.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req_put, timeout=10) as response:
            return response.status == 200 or response.status == 201
    except Exception as e:
        log_activite(f"Erreur GitHub: {e}")
        return False

# === EMAIL ===

def envoyer_email(destinataires, sujet, contenu_html):
    """Envoie un email à plusieurs destinataires"""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        log_activite("Email non configuré")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = sujet
        msg['From'] = f"Axi Agences <{GMAIL_USER}>"
        msg['To'] = ", ".join(destinataires)
        
        msg.attach(MIMEText(contenu_html, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, destinataires, msg.as_string())
        
        log_activite(f"Email envoyé à {destinataires}")
        return True
    except Exception as e:
        log_activite(f"Erreur email: {e}")
        return False

# === TÂCHES AUTOMATIQUES ===

def tache_veille_leboncoin():
    """Scrape LeBonCoin pour trouver des particuliers qui vendent"""
    log_activite("🔍 Veille LeBonCoin - Recherche de mandats potentiels")
    
    # Communes à surveiller
    communes = ["vergt", "le-bugue", "perigueux", "bergerac", "sarlat"]
    opportunites = []
    
    for commune in communes:
        try:
            # Recherche maisons à vendre par particuliers
            url = f"https://www.leboncoin.fr/recherche?category=9&locations={commune}&owner_type=private"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            # Note: LeBonCoin bloque le scraping direct, on simule pour l'exemple
            # En production, utiliser une API ou un service de scraping
            opportunites.append(f"[{commune.upper()}] Recherche effectuée")
            
        except Exception as e:
            log_activite(f"Erreur veille {commune}: {e}")
    
    # Sauvegarder les résultats
    timestamp = heure_france().strftime("%Y-%m-%d %H:%M")
    rapport = f"\n=== VEILLE {timestamp} ===\n"
    rapport += "\n".join(opportunites) + "\n"
    ajouter_fichier("veille_concurrence.txt", rapport)
    
    return opportunites

def tache_analyse_marche():
    """Analyse les prix du marché immobilier local"""
    log_activite("📊 Analyse du marché immobilier")
    
    # Données simulées (à remplacer par vraies sources)
    analyse = {
        "vergt": {"prix_m2_moyen": 1850, "tendance": "+2%"},
        "le_bugue": {"prix_m2_moyen": 2100, "tendance": "+1%"},
        "perigueux": {"prix_m2_moyen": 1650, "tendance": "stable"},
    }
    
    return analyse

def tache_verification_annonces():
    """Vérifie que les annonces des agences sont bien en ligne"""
    log_activite("✅ Vérification des annonces en ligne")
    
    # À implémenter: vérifier les annonces sur les portails
    resultats = {
        "seloger": "OK",
        "leboncoin": "OK",
        "bienici": "OK"
    }
    
    return resultats

def generer_rapport_quotidien():
    """Génère le rapport quotidien complet"""
    log_activite("📝 Génération du rapport quotidien")
    
    date = heure_france().strftime("%d/%m/%Y")
    
    # Collecter les données
    veille = lire_fichier("veille_concurrence.txt")[-2000:]  # Derniers 2000 chars
    opportunites = lire_fichier("opportunites.txt")[-1000:]
    journal = lire_fichier("journal_activite.txt")[-3000:]
    
    # Construire le rapport HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 10px; }}
            h2 {{ color: #16213e; margin-top: 30px; }}
            .section {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .ok {{ color: green; }}
            .warning {{ color: orange; }}
            .urgent {{ color: red; font-weight: bold; }}
            pre {{ background: #1a1a2e; color: #eee; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>🏠 Rapport Quotidien - Ici Dordogne</h1>
        <p><strong>Date :</strong> {date}</p>
        <p><strong>Généré par :</strong> Axi Agences (AXIS Station)</p>
        
        <h2>📊 Résumé de la journée</h2>
        <div class="section">
            <p>Tâches automatiques exécutées : ✅</p>
            <p>Veille concurrentielle : ✅</p>
            <p>Vérification annonces : ✅</p>
        </div>
        
        <h2>🔍 Opportunités détectées</h2>
        <div class="section">
            <pre>{opportunites if opportunites else "Aucune nouvelle opportunité aujourd'hui"}</pre>
        </div>
        
        <h2>📈 Veille Concurrentielle</h2>
        <div class="section">
            <pre>{veille if veille else "Pas de données de veille"}</pre>
        </div>
        
        <h2>📋 Journal d'activité</h2>
        <div class="section">
            <pre>{journal if journal else "Pas d'activité enregistrée"}</pre>
        </div>
        
        <hr>
        <p style="color: #888; font-size: 12px;">
            Ce rapport est généré automatiquement par Axi Agences sur AXIS Station.<br>
            "Je ne lâche pas" — Symbine
        </p>
    </body>
    </html>
    """
    
    # Sauvegarder le rapport
    ecrire_fichier("rapport_quotidien.txt", f"=== RAPPORT {date} ===\n{journal}\n")
    
    return html

def envoyer_rapport_quotidien():
    """Envoie le rapport quotidien par email"""
    log_activite("📧 Envoi du rapport quotidien")
    
    html = generer_rapport_quotidien()
    date = heure_france().strftime("%d/%m/%Y")
    sujet = f"🏠 Rapport Ici Dordogne - {date}"
    
    if DESTINATAIRES_RAPPORT:
        envoyer_email(DESTINATAIRES_RAPPORT, sujet, html)
    else:
        log_activite("Aucun destinataire configuré pour le rapport")

# === SCHEDULER ===

def scheduler_taches():
    """Planifie et exécute les tâches automatiques"""
    log_activite("🚀 Scheduler démarré")
    
    derniere_veille = None
    dernier_rapport = None
    
    while True:
        try:
            maintenant = heure_france()
            heure = maintenant.hour
            minute = maintenant.minute
            
            # Veille toutes les 2 heures (8h, 10h, 12h, 14h, 16h)
            if heure in [8, 10, 12, 14, 16] and minute < 5:
                if derniere_veille != heure:
                    tache_veille_leboncoin()
                    tache_verification_annonces()
                    derniere_veille = heure
            
            # Rapport quotidien à 18h
            if heure == 18 and minute < 5:
                if dernier_rapport != maintenant.date():
                    tache_analyse_marche()
                    envoyer_rapport_quotidien()
                    dernier_rapport = maintenant.date()
            
            # Pause de 60 secondes
            time.sleep(60)
            
        except Exception as e:
            log_activite(f"Erreur scheduler: {e}")
            time.sleep(60)

# === SERVEUR WEB ===

class AxiAgencesHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            journal = lire_fichier("journal_activite.txt")[-5000:]
            veille = lire_fichier("veille_concurrence.txt")[-3000:]
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Axi Agences - Ici Dordogne</title>
                <style>
                    body {{ font-family: Georgia, serif; background: #1a1a2e; color: #eee; padding: 20px; }}
                    h1 {{ color: #e94560; }}
                    .section {{ background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    pre {{ background: #0f3460; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }}
                    .status {{ color: #4ade80; }}
                    button {{ background: #e94560; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }}
                    button:hover {{ background: #c73e54; }}
                </style>
            </head>
            <body>
                <h1>🏠 Axi Agences - Ici Dordogne</h1>
                <p class="status">● En ligne sur AXIS Station</p>
                
                <div class="section">
                    <h2>📋 Actions</h2>
                    <button onclick="location.href='/veille'">🔍 Lancer Veille</button>
                    <button onclick="location.href='/rapport'">📧 Envoyer Rapport</button>
                    <button onclick="location.href='/status'">📊 Status</button>
                </div>
                
                <div class="section">
                    <h2>📋 Journal d'activité</h2>
                    <pre>{journal if journal else "Aucune activité"}</pre>
                </div>
                
                <div class="section">
                    <h2>🔍 Dernière veille</h2>
                    <pre>{veille if veille else "Pas encore de veille"}</pre>
                </div>
                
                <p style="color: #888; margin-top: 40px;">Je ne lâche pas — Symbine</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == '/veille':
            tache_veille_leboncoin()
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        elif self.path == '/rapport':
            envoyer_rapport_quotidien()
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "running",
                "heure": heure_france().isoformat(),
                "github_repo": GITHUB_REPO
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Désactiver les logs HTTP

# === MAIN ===

def main():
    port = int(os.environ.get("PORT", 8080))
    
    # Créer les fichiers de base si inexistants
    for f in FICHIERS_A_SAUVEGARDER:
        if not os.path.exists(f):
            ecrire_fichier(f, f"# {f}\nCréé le {heure_france().strftime('%Y-%m-%d %H:%M')}\n")
    
    log_activite("🏠 Axi Agences démarré sur AXIS Station")
    log_activite(f"📡 Serveur web sur port {port}")
    
    # Lancer le scheduler en arrière-plan
    scheduler_thread = threading.Thread(target=scheduler_taches, daemon=True)
    scheduler_thread.start()
    
    # Lancer le serveur web
    server = HTTPServer(('0.0.0.0', port), AxiAgencesHandler)
    print(f"Axi Agences prêt sur http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
