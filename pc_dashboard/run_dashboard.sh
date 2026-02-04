#!/bin/bash
################################################################################
# run_dashboard.sh - Script de lancement du dashboard PC
#
# Usage: ./run_dashboard.sh [ROBOT_IP]
################################################################################

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROBOT_IP="${1:-10.84.106.222}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Robocar PC Dashboard${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Robot IP: $ROBOT_IP"
echo ""

# Vérifier environnement virtuel
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Environnement virtuel non trouvé.${NC}"
    echo "Création de l'environnement..."
    python3 -m venv "$SCRIPT_DIR/venv"
    
    echo "Installation des dépendances..."
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Activer venv
source "$SCRIPT_DIR/venv/bin/activate"

# Vérifier dépendances
if ! python -c "import cv2" 2>/dev/null; then
    echo -e "${YELLOW}OpenCV non installé. Installation...${NC}"
    pip install opencv-python
fi

# Lancer
echo -e "${GREEN}Lancement du dashboard...${NC}"
echo ""
python "$SCRIPT_DIR/main_pc.py" --robot-ip "$ROBOT_IP"
