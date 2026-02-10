# Guide de Déploiement DATAIKOŠ Backend

Ce guide vous explique comment déployer le backend DATAIKOŠ sur différentes plateformes.

## 📦 Déploiement sur Render.com (Recommandé)

### Étape 1 : Préparation

1. Créer un compte sur [Render.com](https://render.com)
2. Connecter votre compte GitHub
3. Pousser votre code sur GitHub

### Étape 2 : Configuration Supabase

1. Créer un projet sur [Supabase](https://supabase.com)
2. Exécuter les scripts SQL fournis dans le README
3. Noter vos clés :
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (anon public)
   - `SUPABASE_SERVICE_ROLE_KEY`

### Étape 3 : Créer le Web Service

1. Dans Render, cliquer sur "New +" → "Web Service"
2. Connecter votre repository GitHub
3. Configurer :
   - **Name** : `dataikos-backend`
   - **Environment** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Étape 4 : Variables d'environnement

Ajouter ces variables dans "Environment" :

```
APP_NAME=DATAIKOŠ Backend
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=https://votre-frontend.netlify.app

SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_clé_anon
SUPABASE_SERVICE_ROLE_KEY=votre_clé_service

SECRET_KEY=générer_une_clé_secrète_forte
ADMIN_USERNAME=admin
ADMIN_PASSWORD=mot_de_passe_admin_sécurisé
ADMIN_EMAIL=admin@dataikos.com

EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre_app_password

SCHEDULER_ENABLED=true
```

**⚠️ Important** : Générer une clé secrète forte :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Étape 5 : Déployer

1. Cliquer sur "Create Web Service"
2. Attendre la fin du build (3-5 minutes)
3. Votre API sera disponible sur : `https://dataikos-backend.onrender.com`

### Étape 6 : Vérification

Tester l'API :
```bash
curl https://dataikos-backend.onrender.com/health
```

## 🐳 Déploiement avec Docker

### Créer un Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer le dossier uploads
RUN mkdir -p uploads

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
```

### Lancer avec Docker

```bash
docker-compose up -d
```

## ☁️ Déploiement sur Railway

1. Créer un compte sur [Railway](https://railway.app)
2. Nouveau projet → "Deploy from GitHub repo"
3. Sélectionner votre repo
4. Railway détecte automatiquement Python
5. Ajouter les variables d'environnement
6. Déployer !

## 🌐 Déploiement sur Vercel (Serverless)

**Note** : Vercel fonctionne en mode serverless, certaines fonctionnalités (scheduler) ne fonctionneront pas.

### vercel.json

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### Déployer

```bash
npm i -g vercel
vercel
```

## 🔧 Configuration Post-Déploiement

### 1. Tester l'API

```bash
# Health check
curl https://votre-api.com/health

# Login admin
curl -X POST https://votre-api.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"votre_password"}'
```

### 2. Configurer CORS

Dans le frontend, mettre à jour `API_BASE_URL` :

```javascript
// api.js
const API_BASE_URL = 'https://votre-api.onrender.com';
```

### 3. Configurer les emails

Pour Gmail :
1. Activer 2FA : https://myaccount.google.com/security
2. Créer un App Password : https://myaccount.google.com/apppasswords
3. Utiliser ce mot de passe dans `SMTP_PASSWORD`

### 4. Générer les créneaux horaires

Via l'API (authentifié admin) :

```bash
curl -X POST https://votre-api.com/api/appointments/generate-slots \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-02-01",
    "end_date": "2024-02-28",
    "service_duration": 60
  }'
```

## 📊 Monitoring

### Logs sur Render

1. Dashboard Render → Votre service → "Logs"
2. Logs en temps réel disponibles

### Métriques

Surveiller :
- Temps de réponse
- Taux d'erreurs
- Utilisation mémoire/CPU
- Uptime

## 🔒 Sécurité Production

### Checklist

- [ ] `DEBUG=false` en production
- [ ] Clés secrètes fortes et uniques
- [ ] HTTPS activé (automatique sur Render)
- [ ] Variables d'environnement sécurisées
- [ ] Firewall Supabase configuré
- [ ] Rate limiting activé
- [ ] Backups réguliers Supabase

### Variables sensibles

**NE JAMAIS** commiter :
- `.env`
- Clés API
- Mots de passe
- Tokens

## 🔄 Mise à jour

### Sur Render

1. Push sur GitHub
2. Render redéploie automatiquement
3. Vérifier les logs

### Rollback

En cas de problème :
1. Dashboard Render → "Deploys"
2. Sélectionner le déploiement précédent
3. "Redeploy"

## 🆘 Dépannage

### Erreur "Application failed to respond"

```bash
# Vérifier les logs Render
# Vérifier que le port est correct : $PORT
```

### Erreur connexion Supabase

```bash
# Vérifier les variables SUPABASE_URL et SUPABASE_KEY
# Tester la connexion depuis un autre outil
```

### Emails non envoyés

```bash
# Vérifier SMTP_USERNAME et SMTP_PASSWORD
# Vérifier que le App Password Gmail est correct
# Vérifier les logs pour voir l'erreur exacte
```

## 📞 Support

- Documentation Render : https://render.com/docs
- Documentation Supabase : https://supabase.com/docs
- Support DATAIKOŠ : contact@dataikos.com

---

**Bon déploiement ! 🚀**
