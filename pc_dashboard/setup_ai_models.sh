#!/bin/bash
# setup_ai_models.sh
# Script d'installation des modèles IA pour le dashboard

set -e

echo "🤖 Installation des modèles IA pour Robocar Dashboard"
echo "======================================================"

# Créer et activer un environnement virtuel
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
    echo "✅ Environnement virtuel créé: venv/"
else
    echo ""
    echo "✅ Environnement virtuel existant trouvé"
fi

# Activer l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo ""
echo "⬆️ Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Créer dossier models
mkdir -p models

echo ""
echo "📦 Installation des dépendances Python..."
# Installer les packages compatibles Python 3.13
pip install ultralytics opencv-python torch torchvision

# OpenVINO optionnel (peut échouer avec Python 3.13)
echo ""
echo "📦 Tentative d'installation OpenVINO (optionnel)..."
pip install openvino 2>/dev/null || echo "⚠️ OpenVINO non installé (incompatible Python 3.13) - segmentation désactivée"

echo ""
echo "📥 Téléchargement YOLOv8n (nano)..."
python3 << EOF
from ultralytics import YOLO
print("Téléchargement YOLOv8n...")
model = YOLO('yolov8n.pt')
print("✅ YOLOv8n téléchargé")
EOF

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Modèles installés:"
echo "  ✅ YOLOv8n pour détection d'objets"
if python -c "import openvino" 2>/dev/null; then
    echo "  ✅ OpenVINO pour segmentation de route"
    echo ""
    echo "⚠️ Note: Les modèles OpenVINO doivent être téléchargés manuellement"
    echo "   avec 'omz_downloader' si disponible, ou désactivés."
else
    echo "  ⚠️ OpenVINO non disponible (segmentation désactivée)"
fi
echo ""
echo "Pour activer l'environnement virtuel:"
echo "  source venv/bin/activate"
echo ""
echo "Vous pouvez maintenant lancer le dashboard avec l'IA:"
echo "  ./run_dashboard.sh"
