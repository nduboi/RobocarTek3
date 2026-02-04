#!/bin/bash
# activate_venv.sh
# Script pour activer l'environnement virtuel

if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé!"
    echo "Lancez d'abord: ./setup_ai_models.sh"
    exit 1
fi

echo "✅ Activation de l'environnement virtuel..."
echo ""
echo "Pour désactiver plus tard, tapez: deactivate"
echo ""

# Note: Ce script doit être sourcé, pas exécuté
# Utilisation: source activate_venv.sh

source venv/bin/activate
