# DATAIKOŠ Backend API

Backend API complet pour la plateforme étudiante DATAIKOŠ. Construit avec FastAPI, Supabase et déployable sur Render.

## 🚀 Fonctionnalités

- ✅ Authentification JWT (Access + Refresh tokens)
- ✅ Gestion des commandes (Orders)
- ✅ Système de rendez-vous (Appointments)
- ✅ Galerie d'images avec upload
- ✅ Messagerie de contact
- ✅ Tableau de bord administrateur
- ✅ Service d'envoi d'emails
- ✅ Scheduler pour rappels automatiques
- ✅ API REST complète avec documentation Swagger

## 📋 Prérequis

- Python 3.9+
- Compte Supabase
- (Optionnel) Compte Gmail pour emails

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd dataikos-backend-fixed
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement

Copier `.env.example` vers `.env` et configurer :

```bash
cp .env.example .env
```

Éditer `.env` avec vos informations :

```env
# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-anon
SUPABASE_SERVICE_ROLE_KEY=votre-clé-service

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=VotreMotDePasseSecurisé

# Email (optionnel)
EMAIL_ENABLED=true
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-app-password
```

### 5. Configuration Supabase

Créer les tables suivantes dans Supabase :

#### Table `users`
```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `orders`
```sql
CREATE TABLE orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    service TEXT NOT NULL,
    formula TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    client_name TEXT NOT NULL,
    client_email TEXT NOT NULL,
    client_phone TEXT NOT NULL,
    client_description TEXT,
    status TEXT DEFAULT 'pending',
    appointment_id UUID,
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `time_slots`
```sql
CREATE TABLE time_slots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    max_capacity INT DEFAULT 5,
    current_bookings INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `appointments`
```sql
CREATE TABLE appointments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    time_slot_id UUID REFERENCES time_slots(id),
    client_email TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_phone TEXT NOT NULL,
    service TEXT NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'confirmed',
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `contact_messages`
```sql
CREATE TABLE contact_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    phone TEXT,
    status TEXT DEFAULT 'unread',
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `gallery`
```sql
CREATE TABLE gallery (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    image_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🚀 Lancement

### Développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📚 Documentation API

Une fois le serveur lancé, accéder à :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔗 Endpoints principaux

### Authentication
- `POST /api/auth/login` - Connexion
- `POST /api/auth/logout` - Déconnexion
- `POST /api/auth/refresh` - Rafraîchir le token
- `GET /api/auth/validate-token` - Valider le token
- `GET /api/auth/me` - Informations utilisateur

### Orders
- `POST /api/orders` - Créer une commande
- `GET /api/orders` - Liste des commandes (admin)
- `GET /api/orders/{id}` - Détails commande (admin)
- `PUT /api/orders/{id}` - Modifier commande (admin)
- `DELETE /api/orders/{id}` - Supprimer commande (admin)

### Appointments
- `GET /api/appointments/available-slots` - Créneaux disponibles
- `POST /api/appointments` - Créer rendez-vous (admin)
- `GET /api/appointments` - Liste rendez-vous (admin)
- `PUT /api/appointments/{id}` - Modifier rendez-vous (admin)
- `DELETE /api/appointments/{id}` - Annuler rendez-vous (admin)

### Messages
- `POST /api/messages` - Envoyer message
- `GET /api/messages` - Liste messages (admin)
- `PUT /api/messages/{id}/read` - Marquer comme lu (admin)

### Gallery
- `GET /api/gallery` - Liste galerie
- `POST /api/gallery/upload` - Upload image (admin)
- `DELETE /api/gallery/{id}` - Supprimer image (admin)

### Admin
- `GET /api/admin/dashboard/stats` - Statistiques
- `GET /api/admin/recent-activity` - Activité récente
- `GET /api/admin/revenue/chart` - Graphique revenus
- `GET /api/admin/orders/chart` - Graphique commandes

## 🌐 Déploiement sur Render

1. Connecter votre repo GitHub à Render
2. Créer un nouveau "Web Service"
3. Configurer :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Ajouter les variables d'environnement du fichier `.env`
5. Déployer !

## 📧 Configuration Email (Gmail)

1. Activer l'authentification à deux facteurs sur Gmail
2. Générer un "App Password" : https://myaccount.google.com/apppasswords
3. Utiliser ce mot de passe dans `SMTP_PASSWORD`

## 🔒 Sécurité

- ✅ Mots de passe hachés avec bcrypt
- ✅ JWT avec expiration
- ✅ CORS configuré
- ✅ Validation des entrées avec Pydantic
- ✅ Protection admin sur routes sensibles

## 📁 Structure du projet

```
dataikos-backend-fixed/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── models.py            # Modèles Pydantic
│   ├── schemas.py           # Schémas de validation
│   ├── auth.py              # Authentification
│   ├── crud.py              # Logique métier
│   ├── routes/              # Routes API
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── orders.py
│   │   ├── messages.py
│   │   ├── gallery.py
│   │   ├── admin.py
│   │   └── appointments.py
│   ├── utils/               # Utilitaires
│   │   ├── __init__.py
│   │   ├── security.py      # JWT, hachage
│   │   ├── supabase_client.py
│   │   ├── email_service.py
│   │   └── scheduler.py
│   └── templates/           # Templates email
│       └── email/
├── tests/                   # Tests
├── uploads/                 # Uploads (créé auto)
├── .env.example            # Variables d'env exemple
├── .gitignore
├── requirements.txt
├── Procfile
└── README.md
```

## 🧪 Tests

```bash
pytest
```

## 🐛 Debugging

Activer le mode debug dans `.env` :

```env
DEBUG=true
```

Les logs détaillés seront affichés dans la console.

## 📞 Support

Pour toute question ou problème :
- Email : contact@dataikos.com
- GitHub Issues : [Créer une issue](#)

## 📄 Licence

© 2024 DATAIKOŠ. Tous droits réservés.

---

**Développé avec ❤️ par l'équipe DATAIKOŠ**
