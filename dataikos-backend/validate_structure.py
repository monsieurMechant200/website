#!/usr/bin/env python3
"""
Script de validation de la structure du projet DATAIKOŠ Backend
Vérifie que tous les fichiers nécessaires sont présents et correctement organisés
"""

import os
import sys
from pathlib import Path

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file(filepath, required=True):
    """Vérifie qu'un fichier existe"""
    if os.path.exists(filepath):
        print(f"{GREEN}✓{RESET} {filepath}")
        return True
    else:
        status = f"{RED}✗{RESET}" if required else f"{YELLOW}○{RESET}"
        print(f"{status} {filepath} {'(REQUIS)' if required else '(optionnel)'}")
        return not required

def check_import(module_path):
    """Vérifie qu'un module Python peut être importé"""
    try:
        __import__(module_path)
        print(f"{GREEN}✓{RESET} Import: {module_path}")
        return True
    except ImportError as e:
        print(f"{RED}✗{RESET} Import: {module_path} - {e}")
        return False

def main():
    """Fonction principale de validation"""
    print("="*60)
    print("🔍 VALIDATION DE LA STRUCTURE DU PROJET DATAIKOŠ BACKEND")
    print("="*60)
    
    all_valid = True
    
    # Fichiers racine
    print("\n📋 Fichiers racine:")
    all_valid &= check_file("requirements.txt")
    all_valid &= check_file(".env.example")
    all_valid &= check_file(".gitignore")
    all_valid &= check_file("Procfile")
    all_valid &= check_file("README.md")
    all_valid &= check_file("DEPLOYMENT.md")
    all_valid &= check_file("STRUCTURE.md")
    check_file(".env", required=False)  # Optionnel en dev
    
    # Package app
    print("\n📦 Package app/:")
    all_valid &= check_file("app/__init__.py")
    all_valid &= check_file("app/main.py")
    all_valid &= check_file("app/config.py")
    all_valid &= check_file("app/models.py")
    all_valid &= check_file("app/schemas.py")
    all_valid &= check_file("app/auth.py")
    all_valid &= check_file("app/crud.py")
    
    # Routes
    print("\n🛣️  Routes app/routes/:")
    all_valid &= check_file("app/routes/__init__.py")
    all_valid &= check_file("app/routes/auth.py")
    all_valid &= check_file("app/routes/orders.py")
    all_valid &= check_file("app/routes/messages.py")
    all_valid &= check_file("app/routes/gallery.py")
    all_valid &= check_file("app/routes/admin.py")
    all_valid &= check_file("app/routes/appointments.py")
    
    # Utils
    print("\n🔧 Utilitaires app/utils/:")
    all_valid &= check_file("app/utils/__init__.py")
    all_valid &= check_file("app/utils/supabase_client.py")
    all_valid &= check_file("app/utils/security.py")
    all_valid &= check_file("app/utils/email_service.py")
    all_valid &= check_file("app/utils/scheduler.py")
    
    # Templates
    print("\n📧 Templates:")
    all_valid &= check_file("app/templates/email", required=False)
    
    # Dossiers
    print("\n📁 Dossiers:")
    check_file("uploads/", required=False)
    check_file("tests/", required=False)
    
    # Résumé
    print("\n" + "="*60)
    if all_valid:
        print(f"{GREEN}✓ VALIDATION RÉUSSIE{RESET}")
        print("La structure du projet est correcte ! 🎉")
        return 0
    else:
        print(f"{RED}✗ VALIDATION ÉCHOUÉE{RESET}")
        print("Certains fichiers requis sont manquants.")
        print("Consultez les messages ci-dessus pour plus de détails.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
