#!/bin/bash
################################################################################
# pre_install_check.sh - Vérifications avant installation
# 
# Vérifie que le système est prêt pour l'installation
################################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

errors=0
warnings=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Vérifications pré-installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

################################################################################
# Système
################################################################################

echo -e "${GREEN}[1] Système${NC}"
echo ""

# Architecture
ARCH=$(uname -m)
echo "  Architecture : $ARCH"
if [[ "$ARCH" != "aarch64" && "$ARCH" != "x86_64" ]]; then
    echo -e "  ${YELLOW}⚠${NC} Architecture non testée"
    warnings=$((warnings + 1))
fi

# Jetson
if [ -f /etc/nv_tegra_release ]; then
    echo -e "  ${GREEN}✓${NC} NVIDIA Jetson détecté"
    cat /etc/nv_tegra_release | head -1
else
    echo -e "  ${YELLOW}⚠${NC} Pas de Jetson détecté"
    warnings=$((warnings + 1))
fi

# OS
if [ -f /etc/os-release ]; then
    OS_NAME=$(grep "^NAME=" /etc/os-release | cut -d'"' -f2)
    echo "  OS : $OS_NAME"
fi

echo ""

################################################################################
# Permissions
################################################################################

echo -e "${GREEN}[2] Permissions${NC}"
echo ""

if [ "$EUID" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Exécuté avec sudo"
else
    echo -e "  ${RED}✗${NC} Doit être exécuté avec sudo"
    errors=$((errors + 1))
fi

echo ""

################################################################################
# Python
################################################################################

echo -e "${GREEN}[3] Python${NC}"
echo ""

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓${NC} $PYTHON_VERSION"
    
    # Version minimale
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PYTHON_MINOR" -lt 6 ]; then
        echo -e "  ${RED}✗${NC} Python 3.6+ requis"
        errors=$((errors + 1))
    fi
else
    echo -e "  ${RED}✗${NC} Python3 non installé"
    errors=$((errors + 1))
fi

# pip
if command -v pip3 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} pip3 disponible"
else
    echo -e "  ${YELLOW}⚠${NC} pip3 non trouvé (sera installé)"
    warnings=$((warnings + 1))
fi

# venv
if python3 -m venv --help &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} venv disponible"
else
    echo -e "  ${YELLOW}⚠${NC} venv non disponible (sera installé)"
    warnings=$((warnings + 1))
fi

echo ""

################################################################################
# Git
################################################################################

echo -e "${GREEN}[4] Git${NC}"
echo ""

if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo -e "  ${GREEN}✓${NC} $GIT_VERSION"
else
    echo -e "  ${YELLOW}⚠${NC} Git non installé (sera installé)"
    warnings=$((warnings + 1))
fi

# Vérifier si c'est un dépôt git
if [ -d ".git" ]; then
    echo -e "  ${GREEN}✓${NC} Dépôt Git détecté"
    
    # Vérifier les sous-modules
    if [ -f ".gitmodules" ]; then
        echo -e "  ${GREEN}✓${NC} Sous-modules configurés"
        git submodule status | while read line; do
            echo "    $line"
        done
    else
        echo -e "  ${YELLOW}⚠${NC} Pas de sous-modules configurés"
        warnings=$((warnings + 1))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Pas un dépôt Git"
    warnings=$((warnings + 1))
fi

echo ""

################################################################################
# Espace disque
################################################################################

echo -e "${GREEN}[5] Espace disque${NC}"
echo ""

DISK_AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
DISK_AVAILABLE_MB=$(df -m . | awk 'NR==2 {print $4}')

echo "  Disponible : $DISK_AVAILABLE"

if [ "$DISK_AVAILABLE_MB" -lt 2048 ]; then
    echo -e "  ${RED}✗${NC} Espace insuffisant (2GB minimum recommandé)"
    errors=$((errors + 1))
elif [ "$DISK_AVAILABLE_MB" -lt 5120 ]; then
    echo -e "  ${YELLOW}⚠${NC} Espace limité (5GB recommandé)"
    warnings=$((warnings + 1))
else
    echo -e "  ${GREEN}✓${NC} Espace suffisant"
fi

echo ""

################################################################################
# Connexion réseau
################################################################################

echo -e "${GREEN}[6] Réseau${NC}"
echo ""

if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Connexion Internet OK"
else
    echo -e "  ${RED}✗${NC} Pas de connexion Internet"
    errors=$((errors + 1))
fi

# DNS
if ping -c 1 google.com &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Résolution DNS OK"
else
    echo -e "  ${YELLOW}⚠${NC} Problème de résolution DNS"
    warnings=$((warnings + 1))
fi

echo ""

################################################################################
# Ports disponibles
################################################################################

echo -e "${GREEN}[7] Ports disponibles${NC}"
echo ""

check_port_available() {
    local port=$1
    local name=$2
    if ss -tuln | grep -q ":$port "; then
        echo -e "  ${YELLOW}⚠${NC} Port $port ($name) déjà utilisé"
        warnings=$((warnings + 1))
    else
        echo -e "  ${GREEN}✓${NC} Port $port ($name) disponible"
    fi
}

check_port_available 5000 "Controller"
check_port_available 5001 "Telemetry"
check_port_available 4488 "Camera"
check_port_available 15975 "Lidar"

echo ""

################################################################################
# Services existants
################################################################################

echo -e "${GREEN}[8] Services systemd${NC}"
echo ""

SERVICES=("robocar-controller" "robocar-camera" "robocar-lidar")
existing_services=0

for service in "${SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "$service.service"; then
        echo -e "  ${YELLOW}⚠${NC} $service existe déjà"
        existing_services=$((existing_services + 1))
        warnings=$((warnings + 1))
    fi
done

if [ "$existing_services" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Aucun service existant"
else
    echo -e "  ${YELLOW}⚠${NC} $existing_services service(s) existant(s) (seront écrasés)"
fi

echo ""

################################################################################
# Périphériques
################################################################################

echo -e "${GREEN}[9] Périphériques${NC}"
echo ""

# Ports série
if ls /dev/ttyACM* &> /dev/null || ls /dev/ttyUSB* &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Ports série détectés:"
    ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | while read port; do
        echo "    - $port"
    done
else
    echo -e "  ${YELLOW}⚠${NC} Aucun port série détecté"
    warnings=$((warnings + 1))
fi

# USB
if command -v lsusb &> /dev/null; then
    usb_count=$(lsusb | wc -l)
    echo -e "  ${GREEN}✓${NC} $usb_count périphérique(s) USB"
else
    echo -e "  ${YELLOW}⚠${NC} lsusb non disponible"
fi

echo ""

################################################################################
# Résumé
################################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Résumé${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "Erreurs : ${errors}"
echo -e "Avertissements : ${warnings}"
echo ""

if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    echo -e "${GREEN}✓ Système prêt pour l'installation${NC}"
    echo ""
    echo "Lancez l'installation avec:"
    echo "  sudo ./install_all.sh"
    echo ""
    exit 0
elif [ "$errors" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Système prêt avec avertissements${NC}"
    echo ""
    echo "Vous pouvez procéder à l'installation:"
    echo "  sudo ./install_all.sh"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Veuillez corriger les erreurs avant installation${NC}"
    echo ""
    exit 1
fi
