# 🏠 Axi Agences - Ici Dordogne

IA opérationnelle pour les agences immobilières Ici Dordogne.

## Fonctionnalités

- 🔍 **Veille concurrentielle** : Surveillance automatique des annonces concurrentes
- 🏠 **Chasse aux mandats** : Détection des particuliers qui vendent
- 📊 **Analyse marché** : Suivi des prix au m² par commune
- ✅ **Vérification annonces** : Contrôle des annonces en ligne
- 📧 **Rapport quotidien** : Email de synthèse chaque jour à 18h

## Déploiement

### Variables d'environnement requises

```
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
GMAIL_USER=email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### Docker

```bash
docker build -t axi-agences .
docker run -d --name axi-agences -p 8080:8080 --env-file .env --restart always axi-agences
```

## Accès

- Interface web : http://localhost:8080
- Boutons : Lancer veille, Envoyer rapport, Status

## Architecture Symbine

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Axis     │     │     Axi     │     │ Axi Agences │
│  (Claude)   │◄───►│  (Railway)  │     │  (Serveur)  │
│   Penseur   │     │   Mémoire   │     │ Opérationnel│
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                     GitHub
              (Synchronisation)
```

---

*"Je ne lâche pas" — Symbine*
