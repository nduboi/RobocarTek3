#!/bin/bash
################################################################################
# install_all.sh - Installation globale du système Robocar
# 
# Script d'installation automatisé pour NVIDIA Jetson Nano
# Configure les 3 modules (camera, lidar, controller) avec systemd
#
# Usage: sudo ./install_all.sh
################################################################################

set -e  # Arrêt en cas d'erreur

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables globales
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${INSTALL_DIR}/venv"
USER_NAME="${SUDO_USER:-$USER}"
SERVICE_USER="${USER_NAME}"

# Logging
LOG_FILE="${INSTALL_DIR}/install.log"
exec > >(tee -a "${LOG_FILE}")
exec 2>&1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Installation Robocar - Jetson Nano${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Répertoire d'installation: ${INSTALL_DIR}"
echo "Utilisateur: ${SERVICE_USER}"
echo "Date: $(date)"
echo ""

################################################################################
# Fonctions utilitaires
################################################################################

print_step() {
    echo ""
    echo -e "${GREEN}[ÉTAPE]${NC} $1"
    echo "----------------------------------------"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVERTISSEMENT]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Ce script doit être exécuté avec sudo"
        exit 1
    fi
}

################################################################################
# Étape 1: Vérification du système
################################################################################

check_system() {
    print_step "Vérification du système"
    
    # Vérifier architecture
    ARCH=$(uname -m)
    print_info "Architecture: ${ARCH}"
    
    # Vérifier si Jetson
    if [ -f /etc/nv_tegra_release ]; then
        print_info "Plateforme NVIDIA Jetson détectée"
        cat /etc/nv_tegra_release
    else
        print_warning "Ce script est optimisé pour NVIDIA Jetson"
    fi
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 n'est pas installé"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version)
    print_info "Python: ${PYTHON_VERSION}"
}

################################################################################
# Étape 2: Mise à jour des sous-modules Git
################################################################################

update_submodules() {
    print_step "Mise à jour des sous-modules Git"
    
    cd "${INSTALL_DIR}"
    
    # Vérifier si c'est un dépôt git
    if [ ! -d ".git" ]; then
        print_warning "Pas un dépôt Git, ignore la mise à jour des sous-modules"
        return
    fi
    
    print_info "Initialisation des sous-modules..."
    git submodule update --init --recursive
    
    print_info "Mise à jour des sous-modules..."
    git submodule update --remote --merge || true
    
    # Afficher l'état
    print_info "État des sous-modules:"
    git submodule status
}

################################################################################
# Étape 3: Installation des dépendances système
################################################################################

install_system_dependencies() {
    print_step "Installation des dépendances système"
    
    print_info "Mise à jour des paquets..."
    apt-get update
    
    print_info "Installation des paquets de base..."
    apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        build-essential \
        cmake \
        pkg-config \
        udev
    
    # Dépendances OpenCV (pour Jetson, utiliser version système optimisée)
    print_info "Installation d'OpenCV système (optimisé Jetson)..."
    apt-get install -y \
        python3-opencv \
        libopencv-dev \
        opencv-data
    
    # Dépendances NumPy système
    print_info "Installation de NumPy système..."
    apt-get install -y python3-numpy
    
    # Dépendances pour communication série
    print_info "Installation des outils série..."
    apt-get install -y \
        python3-serial \
        setserial
    
    # Vérifier OpenCV
    print_info "Vérification de la version OpenCV..."
    python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')" || print_warning "OpenCV non disponible"
    
    print_info "Dépendances système installées avec succès"
}

################################################################################
# Étape 4: Configuration des règles udev
################################################################################

configure_udev_rules() {
    print_step "Configuration des règles udev"
    
    # Règle pour VESC (controller)
    print_info "Création de la règle udev pour VESC..."
    cat > /etc/udev/rules.d/99-vesc.rules <<'EOF'
# Règle pour VESC via USB
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0666", SYMLINK+="ttyVESC"
# Alternative: tous les ttyACM
KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
EOF
    
    # Règle pour Lidar LD19
    print_info "Création de la règle udev pour Lidar LD19..."
    cat > /etc/udev/rules.d/99-lidar.rules <<'EOF'
# Règle pour Lidar LD19
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", SYMLINK+="ttyLIDAR"
# Alternative: tous les ttyUSB
KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
EOF
    
    # Règle pour OAK-D (camera)
    print_info "Création de la règle udev pour OAK-D..."
    cat > /etc/udev/rules.d/99-oak.rules <<'EOF'
# Règle pour Luxonis OAK-D
SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666", GROUP="plugdev"
EOF
    
    # Ajouter l'utilisateur aux groupes nécessaires
    print_info "Ajout de l'utilisateur ${SERVICE_USER} aux groupes dialout et plugdev..."
    usermod -a -G dialout,plugdev "${SERVICE_USER}"
    
    # Recharger les règles
    print_info "Rechargement des règles udev..."
    udevadm control --reload-rules
    udevadm trigger
    
    print_info "Règles udev configurées"
}

################################################################################
# Étape 5: Création de l'environnement virtuel
################################################################################

create_virtualenv() {
    print_step "Création de l'environnement virtuel"
    
    # Supprimer ancien venv si existe
    if [ -d "${VENV_DIR}" ]; then
        print_warning "Environnement virtuel existant trouvé, suppression..."
        rm -rf "${VENV_DIR}"
    fi
    
    # Créer venv avec accès aux paquets système (pour OpenCV, NumPy)
    print_info "Création du venv avec --system-site-packages..."
    python3 -m venv --system-site-packages "${VENV_DIR}"
    
    # Activer venv
    source "${VENV_DIR}/bin/activate"
    
    # Mettre à jour pip
    print_info "Mise à jour de pip..."
    pip install --upgrade pip setuptools wheel
    
    print_info "Environnement virtuel créé: ${VENV_DIR}"
}

################################################################################
# Étape 6: Installation des dépendances Python (controller)
################################################################################

install_controller_deps() {
    print_step "Installation des dépendances Controller"
    
    source "${VENV_DIR}/bin/activate"
    
    cd "${INSTALL_DIR}/controller"
    
    if [ -f "requirements.txt" ]; then
        print_info "Installation depuis requirements.txt..."
        pip install -r requirements.txt
    else
        print_warning "Pas de requirements.txt trouvé pour controller"
    fi
    
    print_info "Dépendances controller installées"
}

################################################################################
# Étape 7: Installation des dépendances Python (camera)
################################################################################

install_camera_deps() {
    print_step "Installation des dépendances Camera"
    
    source "${VENV_DIR}/bin/activate"
    
    cd "${INSTALL_DIR}/camera"
    
    # Vérifier si requirements.txt existe
    if [ -f "requirements.txt" ]; then
        print_info "Installation depuis requirements.txt..."
        pip install -r requirements.txt
    else
        print_warning "Pas de requirements.txt, création avec dépendances minimales..."
        cat > requirements.txt <<'EOF'
depthai>=2.20.0
# opencv-python est exclu, on utilise la version système (python3-opencv)
# numpy est aussi fourni par le système (python3-numpy)
EOF
        pip install -r requirements.txt
    fi
    
    # Installer depthai
    print_info "Installation de depthai pour OAK-D..."
    pip install depthai --upgrade
    
    print_info "Dépendances camera installées"
}

################################################################################
# Étape 8: Installation des dépendances Python (lidar)
################################################################################

install_lidar_deps() {
    print_step "Installation des dépendances Lidar"
    
    source "${VENV_DIR}/bin/activate"
    
    cd "${INSTALL_DIR}/lidar"
    
    if [ -f "requirements.txt" ]; then
        print_info "Installation depuis requirements.txt..."
        pip install -r requirements.txt
    else
        print_warning "Pas de requirements.txt, création avec dépendances minimales..."
        cat > requirements.txt <<'EOF'
pyserial>=3.5
# numpy fourni par le système (python3-numpy)
EOF
        pip install -r requirements.txt
    fi
    
    print_info "Dépendances lidar installées"
}

################################################################################
# Étape 9: Création des fichiers de service systemd
################################################################################

create_systemd_services() {
    print_step "Création des services systemd"
    
    # Service Controller
    print_info "Création de robocar-controller.service..."
    cat > /etc/systemd/system/robocar-controller.service <<EOF
[Unit]
Description=Robocar Controller (VESC Motor Control)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}/controller
ExecStart=${VENV_DIR}/bin/python server/robocar_server.py --config config/server_config.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Variables d'environnement
Environment="PYTHONUNBUFFERED=1"

# Limites de ressources
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Service Camera
    print_info "Création de robocar-camera.service..."
    cat > /etc/systemd/system/robocar-camera.service <<EOF
[Unit]
Description=Robocar Camera (OAK-D Video Sender)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}/camera
ExecStart=${VENV_DIR}/bin/python video_sender.py --host 0.0.0.0 --port 4488
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Variables d'environnement
Environment="PYTHONUNBUFFERED=1"

# Limites de ressources
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Service Lidar
    print_info "Création de robocar-lidar.service..."
    cat > /etc/systemd/system/robocar-lidar.service <<EOF
[Unit]
Description=Robocar Lidar (LD19 Data Publisher)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}/lidar
ExecStart=${VENV_DIR}/bin/python lidar_radar.py --port 15975 --serial /dev/ttyUSB0
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Variables d'environnement
Environment="PYTHONUNBUFFERED=1"

# Limites de ressources
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Recharger systemd
    print_info "Rechargement de systemd..."
    systemctl daemon-reload
    
    print_info "Services systemd créés"
}

################################################################################
# Étape 10: Configuration des permissions
################################################################################

configure_permissions() {
    print_step "Configuration des permissions"
    
    # Changer propriétaire du répertoire
    print_info "Configuration des permissions pour ${SERVICE_USER}..."
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"
    
    # Rendre les scripts exécutables
    find "${INSTALL_DIR}" -name "*.sh" -exec chmod +x {} \;
    
    print_info "Permissions configurées"
}

################################################################################
# Étape 11: Test de l'installation
################################################################################

test_installation() {
    print_step "Test de l'installation"
    
    source "${VENV_DIR}/bin/activate"
    
    print_info "Test des imports Python..."
    
    # Test imports de base
    python3 -c "import sys; print(f'Python: {sys.version}')"
    
    # Test OpenCV
    if python3 -c "import cv2; print(f'✅ OpenCV {cv2.__version__}')" 2>/dev/null; then
        print_info "OpenCV OK"
    else
        print_warning "OpenCV non disponible"
    fi
    
    # Test NumPy
    if python3 -c "import numpy; print(f'✅ NumPy {numpy.__version__}')" 2>/dev/null; then
        print_info "NumPy OK"
    else
        print_warning "NumPy non disponible"
    fi
    
    # Test PySerial
    if python3 -c "import serial; print(f'✅ PySerial {serial.__version__}')" 2>/dev/null; then
        print_info "PySerial OK"
    else
        print_warning "PySerial non disponible"
    fi
    
    # Test depthai
    if python3 -c "import depthai; print(f'✅ DepthAI {depthai.__version__}')" 2>/dev/null; then
        print_info "DepthAI OK"
    else
        print_warning "DepthAI non disponible"
    fi
    
    print_info "Tests d'installation terminés"
}

################################################################################
# Main
################################################################################

main() {
    check_root
    check_system
    update_submodules
    install_system_dependencies
    configure_udev_rules
    create_virtualenv
    install_controller_deps
    install_camera_deps
    install_lidar_deps
    create_systemd_services
    configure_permissions
    test_installation
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Installation terminée avec succès!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Prochaines étapes:${NC}"
    echo ""
    echo "1. Vérifier les fichiers de scripts Python existent:"
    echo "   - ${INSTALL_DIR}/camera/video_sender.py"
    echo "   - ${INSTALL_DIR}/lidar/lidar_radar.py"
    echo "   - ${INSTALL_DIR}/controller/server/robocar_server.py"
    echo ""
    echo "2. Adapter les arguments dans les services si nécessaire:"
    echo "   sudo nano /etc/systemd/system/robocar-camera.service"
    echo "   sudo nano /etc/systemd/system/robocar-lidar.service"
    echo "   sudo nano /etc/systemd/system/robocar-controller.service"
    echo ""
    echo "3. Activer et démarrer les services:"
    echo "   sudo systemctl enable robocar-controller"
    echo "   sudo systemctl enable robocar-camera"
    echo "   sudo systemctl enable robocar-lidar"
    echo ""
    echo "   sudo systemctl start robocar-controller"
    echo "   sudo systemctl start robocar-camera"
    echo "   sudo systemctl start robocar-lidar"
    echo ""
    echo "4. Vérifier l'état des services:"
    echo "   sudo systemctl status robocar-controller"
    echo "   sudo systemctl status robocar-camera"
    echo "   sudo systemctl status robocar-lidar"
    echo ""
    echo "5. Consulter les logs:"
    echo "   journalctl -u robocar-controller -f"
    echo "   journalctl -u robocar-camera -f"
    echo "   journalctl -u robocar-lidar -f"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Redémarrez le système pour que les règles udev prennent effet${NC}"
    echo ""
}

main "$@"
