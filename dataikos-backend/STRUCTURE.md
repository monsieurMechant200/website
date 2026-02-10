# Structure du Projet DATAIKOŠ Backend

Ce document explique l'organisation et l'architecture du code.

## 📂 Organisation des Dossiers

```
dataikos-backend-fixed/
│
├── app/                          # Package principal de l'application
│   ├── __init__.py              # Initialisation du package
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── config.py                # Configuration centralisée
│   ├── models.py                # Modèles Pydantic (validation données)
│   ├── schemas.py               # Schémas de requêtes/réponses
│   ├── auth.py                  # Logique d'authentification
│   ├── crud.py                  # Opérations CRUD business logic
│   │
│   ├── routes/                  # Routes API organisées par domaine
│   │   ├── __init__.py
│   │   ├── auth.py             # Routes authentification
│   │   ├── orders.py           # Routes commandes
│   │   ├── messages.py         # Routes messages
│   │   ├── gallery.py          # Routes galerie
│   │   ├── admin.py            # Routes administration
│   │   └── appointments.py     # Routes rendez-vous
│   │
│   ├── utils/                   # Utilitaires réutilisables
│   │   ├── __init__.py
│   │   ├── supabase_client.py  # Client Supabase
│   │   ├── security.py         # Sécurité (JWT, hash)
│   │   ├── email_service.py    # Service emails
│   │   └── scheduler.py        # Tâches planifiées
│   │
│   └── templates/               # Templates (emails, etc.)
│       └── email/
│           ├── appointment_confirmation.html
│           └── appointment_reminder.html
│
├── tests/                       # Tests unitaires et d'intégration
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_orders.py
│   └── test_api.py
│
├── uploads/                     # Fichiers uploadés (gitignored)
│   └── .gitkeep
│
├── .env.example                 # Variables d'environnement exemple
├── .gitignore                   # Fichiers à ignorer par Git
├── requirements.txt             # Dépendances Python
├── Procfile                     # Configuration déploiement
├── README.md                    # Documentation principale
├── DEPLOYMENT.md                # Guide de déploiement
└── STRUCTURE.md                 # Ce fichier
```

## 🏗️ Architecture

### Flux de Requête

```
Client (Frontend)
    ↓
FastAPI Router (app/routes/)
    ↓
Auth Middleware (app/auth.py)
    ↓
CRUD Handler (app/crud.py)
    ↓
Database Manager (app/utils/supabase_client.py)
    ↓
Supabase Database
```

### Couches de l'Application

#### 1. Routes Layer (`app/routes/`)
- Définit les endpoints API
- Validation des requêtes avec Pydantic
- Gestion des réponses HTTP
- Authentification/autorisation

#### 2. Business Logic Layer (`app/crud.py`)
- Logique métier
- Orchestration des opérations
- Gestion des transactions
- Envoi d'emails
- Validation business

#### 3. Data Access Layer (`app/utils/supabase_client.py`)
- Interaction avec Supabase
- Requêtes SQL
- Gestion des erreurs DB
- Transactions

#### 4. Security Layer (`app/auth.py`, `app/utils/security.py`)
- Authentification JWT
- Hachage mots de passe
- Vérification tokens
- Autorisations

## 📋 Modèles de Données

### Hiérarchie des Modèles Pydantic

```python
# Base Model (structure commune)
OrderBase
    ├── OrderCreate (création)
    ├── OrderInDB (BDD)
    └── OrderUpdate (modification)

# Même pattern pour :
- User (utilisateurs)
- Message (messages contact)
- GalleryItem (galerie)
- Appointment (rendez-vous)
- TimeSlot (créneaux)
```

## 🔄 Flux de Données Principaux

### 1. Création de Commande avec Rendez-vous

```
POST /api/orders
    ↓
routes/orders.py : create_order()
    ↓
crud.py : CRUDHandler.create_order()
    ├── Créer la commande
    ├── Si time_slot_id fourni :
    │   ├── Créer le rendez-vous
    │   ├── Incrémenter le compteur de réservations
    │   └── Envoyer email de confirmation
    └── Retourner la commande
```

### 2. Authentification

```
POST /api/auth/login
    ↓
routes/auth.py : login()
    ↓
auth.py : AuthHandler.authenticate_user()
    ├── Récupérer l'utilisateur
    ├── Vérifier le mot de passe
    └── Créer les tokens (access + refresh)
```

### 3. Upload d'Image

```
POST /api/gallery/upload
    ↓
routes/gallery.py : upload_image()
    ├── Vérifier autorisation admin
    ├── Valider le fichier (taille, type)
    ├── Sauvegarder localement
    ├── Créer l'entrée en BDD
    └── Retourner l'URL
```

## 🔐 Système d'Authentification

### Token Flow

```
1. Login
   ↓
2. Génération Access Token (30min) + Refresh Token (7j)
   ↓
3. Client stocke les tokens
   ↓
4. Requêtes avec Header: "Authorization: Bearer {access_token}"
   ↓
5. Validation du token à chaque requête
   ↓
6. Si expiré → Utiliser refresh_token pour nouveau access_token
```

### Protection des Routes

```python
# Route publique
@router.get("/public")
async def public_endpoint():
    return {"message": "Accessible à tous"}

# Route authentifiée
@router.get("/protected")
async def protected_endpoint(
    user = Depends(auth_handler.get_current_user)
):
    return {"user": user}

# Route admin uniquement
@router.get("/admin")
async def admin_endpoint(
    user = Depends(auth_handler.get_current_admin)
):
    return {"admin": user}
```

## 📧 Service Email

### Architecture

```
crud.py
    ↓
email_service.py
    ├── Charger le template Jinja2
    ├── Remplir les variables
    ├── Envoyer via SMTP
    └── Logger le résultat
```

### Templates disponibles

- `appointment_confirmation.html` : Confirmation de rendez-vous
- `appointment_reminder.html` : Rappel 24h avant

## ⏰ Scheduler

### Fonctionnement

```python
# Démarrage au lancement de l'app
app startup → scheduler.start()
    ↓
Boucle toutes les 60 minutes
    ↓
Vérifier les rendez-vous dans 24h
    ↓
Envoyer les rappels
    ↓
Marquer comme "reminder_sent"
```

## 🗄️ Base de Données

### Relations

```
users (administrateurs)

orders (commandes)
    ↓ order_id
appointments (rendez-vous)
    ↓ time_slot_id
time_slots (créneaux horaires)

contact_messages (messages contact)
    (table indépendante)

gallery (galerie images)
    (table indépendante)
```

## 🛡️ Validation des Données

### Niveaux de Validation

1. **FastAPI automatique** : Types de base (str, int, etc.)
2. **Pydantic Models** : Validation avancée
3. **Custom Validators** : Logique métier
4. **Database Constraints** : Contraintes SQL

### Exemple

```python
class OrderCreate(BaseModel):
    price: float  # 1. FastAPI vérifie que c'est un nombre
    
    @validator('price')  # 2. Pydantic validator custom
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v
```

## 🔧 Configuration

### Centralisation dans `config.py`

```python
# Toutes les variables d'environnement
settings = Settings()

# Utilisation dans l'app
from app.config import settings

max_size = settings.MAX_FILE_SIZE_MB
```

### Avantages

- ✅ Configuration centralisée
- ✅ Validation des types
- ✅ Valeurs par défaut
- ✅ Auto-complétion IDE

## 📝 Logging

### Niveaux de Log

```python
logger.debug("Détail développement")
logger.info("Information générale")
logger.warning("Avertissement")
logger.error("Erreur")
logger.exception("Erreur avec traceback")
```

### Configuration

```python
# DEBUG=true → Logs détaillés
# DEBUG=false → Logs warnings et erreurs uniquement
```

## 🧪 Testing

### Structure des Tests

```
tests/
├── test_auth.py          # Tests authentification
├── test_orders.py        # Tests commandes
├── test_appointments.py  # Tests rendez-vous
└── test_api.py          # Tests intégration
```

### Lancer les Tests

```bash
pytest
pytest -v  # Verbose
pytest tests/test_auth.py  # Un fichier spécifique
```

## 🚀 Optimisations

### Performance

- **Async/Await** : Toutes les opérations I/O sont asynchrones
- **Connection Pooling** : Supabase gère le pool de connexions
- **Caching** : À implémenter si nécessaire (Redis)

### Scalabilité

- **Horizontal** : Ajouter des instances (Render auto-scale)
- **Database** : Supabase gère la scalabilité
- **CDN** : Pour les images (à implémenter)

## 📦 Dépendances Principales

```
FastAPI      → Framework web
Supabase     → Base de données
Pydantic     → Validation données
PyJWT        → Tokens JWT
Passlib      → Hachage mots de passe
Jinja2       → Templates emails
Pillow       → Traitement images
```

## 🔄 Workflow de Développement

1. **Créer une branche** : `git checkout -b feature/nouvelle-fonctionnalite`
2. **Coder** : Suivre la structure existante
3. **Tester** : `pytest`
4. **Commit** : `git commit -m "feat: description"`
5. **Push** : `git push origin feature/nouvelle-fonctionnalite`
6. **Pull Request** : Review et merge

## 📚 Ressources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

**Questions ?** Consultez le README.md ou contactez l'équipe !
