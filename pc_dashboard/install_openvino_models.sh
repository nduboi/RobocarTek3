#!/bin/bash
# install_openvino_models.sh
# Télécharge les modèles OpenVINO avec Python 3.11

set -e

echo "🤖 Installation des modèles OpenVINO"
echo "====================================="

# Installer Python 3.11 si manquant
if ! command -v python3.11 &> /dev/null; then
    echo ""
    echo "📥 Installation de Python 3.11..."
    sudo dnf install -y python3.11 python3.11-devel
fi

# Créer venv 3.11 dédié
if [ ! -d "venv311" ]; then
    echo ""
    echo "📦 Création venv Python 3.11..."
    python3.11 -m venv venv311
fi

source venv311/bin/activate

echo ""
echo "⬆️ Mise à jour pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "📦 Installation openvino-dev..."
pip install "openvino>=2023.0" "openvino-dev>=2023.0"

echo ""
echo "📥 Téléchargement road-segmentation-adas-0001..."
mkdir -p models
cd models

omz_downloader --name road-segmentation-adas-0001 --output_dir .

echo ""
echo "🔄 Conversion du modèle..."
omz_converter --name road-segmentation-adas-0001 --download_dir . --output_dir .

cd ..

echo ""
echo "✅ Modèles téléchargés!"
echo ""
echo "Les modèles sont maintenant dans: models/intel/road-segmentation-adas-0001/"
echo ""
echo "Le dashboard les utilisera automatiquement (nécessite accès direct aux fichiers)"
echo ""
echo "Pour désactiver le venv311:"
echo "  deactivate"
