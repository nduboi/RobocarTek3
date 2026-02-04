#!/bin/bash
################################################################################
# test_modules.sh - Test individuel des modules
# 
# Usage: ./test_modules.sh {controller|camera|lidar|all}
################################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

print_usage() {
    echo "Usage: $0 {controller|camera|lidar|all}"
    echo ""
    echo "Test les modules individuellement hors systemd"
}

# Vérifier venv
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}[ERREUR]${NC} Environnement virtuel non trouvé"
    echo "Lancez d'abord: sudo ./install_all.sh"
    exit 1
fi

# Activer venv
source "${VENV_DIR}/bin/activate"

test_controller() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Test Module Controller${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    cd "${SCRIPT_DIR}/controller"
    
    # Vérifier fichier principal
    if [ ! -f "server/robocar_server.py" ]; then
        echo -e "${RED}✗${NC} Fichier server/robocar_server.py non trouvé"
        return 1
    fi
    
    # Vérifier config
    if [ ! -f "config/server_config.yaml" ]; then
        echo -e "${YELLOW}⚠${NC} Fichier config/server_config.yaml non trouvé"
    fi
    
    echo -e "${GREEN}Démarrage du controller...${NC}"
    echo "Port contrôle : 5000"
    echo "Port télémétrie : 5001"
    echo ""
    echo "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    
    python server/robocar_server.py --config config/server_config.yaml
}

test_camera() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Test Module Camera${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    cd "${SCRIPT_DIR}/camera"
    
    # Vérifier fichier principal
    if [ ! -f "video_sender.py" ]; then
        echo -e "${RED}✗${NC} Fichier video_sender.py non trouvé"
        echo ""
        echo "Veuillez créer ce fichier ou ajuster le nom dans:"
        echo "  - /etc/systemd/system/robocar-camera.service"
        echo "  - Ce script de test"
        return 1
    fi
    
    # Vérifier OAK-D
    if ! lsusb | grep -iq "03e7"; then
        echo -e "${YELLOW}⚠${NC} OAK-D non détecté"
    else
        echo -e "${GREEN}✓${NC} OAK-D détecté"
    fi
    
    echo ""
    echo -e "${GREEN}Démarrage de la caméra...${NC}"
    echo "Port TCP : 4488"
    echo ""
    echo "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    
    python video_sender.py --host 0.0.0.0 --port 4488
}

test_lidar() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Test Module Lidar${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    cd "${SCRIPT_DIR}/lidar"
    
    # Vérifier fichier principal
    if [ ! -f "lidar_radar.py" ]; then
        echo -e "${RED}✗${NC} Fichier lidar_radar.py non trouvé"
        echo ""
        echo "Veuillez créer ce fichier ou ajuster le nom dans:"
        echo "  - /etc/systemd/system/robocar-lidar.service"
        echo "  - Ce script de test"
        return 1
    fi
    
    # Vérifier port série
    if [ ! -e "/dev/ttyUSB0" ]; then
        echo -e "${YELLOW}⚠${NC} Port /dev/ttyUSB0 non trouvé"
        echo "Ports série disponibles:"
        ls /dev/ttyUSB* 2>/dev/null || echo "  Aucun"
    else
        echo -e "${GREEN}✓${NC} Port /dev/ttyUSB0 disponible"
    fi
    
    echo ""
    echo -e "${GREEN}Démarrage du lidar...${NC}"
    echo "Port UDP : 15975"
    echo "Port série : /dev/ttyUSB0"
    echo ""
    echo "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    
    python lidar_radar.py --port 15975 --serial /dev/ttyUSB0
}

test_all() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Test de tous les modules${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Ce test nécessite 3 terminaux séparés."
    echo ""
    echo "Terminal 1 (Controller):"
    echo "  ./test_modules.sh controller"
    echo ""
    echo "Terminal 2 (Camera):"
    echo "  ./test_modules.sh camera"
    echo ""
    echo "Terminal 3 (Lidar):"
    echo "  ./test_modules.sh lidar"
    echo ""
    echo "Ou utilisez les services systemd:"
    echo "  ./manage_services.sh start"
}

# Main
case "$1" in
    controller)
        test_controller
        ;;
    camera)
        test_camera
        ;;
    lidar)
        test_lidar
        ;;
    all)
        test_all
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
