#!/bin/bash
################################################################################
# uninstall.sh - Désinstallation des services Robocar
# 
# Usage: sudo ./uninstall.sh
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICES=("robocar-controller" "robocar-camera" "robocar-lidar")

echo -e "${RED}========================================${NC}"
echo -e "${RED}   Désinstallation Robocar${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Vérifier root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERREUR]${NC} Ce script doit être exécuté avec sudo"
    exit 1
fi

echo -e "${YELLOW}Cette opération va:${NC}"
echo "  - Arrêter et désactiver tous les services"
echo "  - Supprimer les fichiers de service systemd"
echo "  - Supprimer les règles udev"
echo ""

read -p "Voulez-vous continuer? (oui/non) " -n 3 -r
echo
if [[ ! $REPLY =~ ^[Oo][Uu][Ii]$ ]]; then
    echo "Annulé"
    exit 1
fi

echo ""

################################################################################
# Arrêter et désactiver les services
################################################################################

echo -e "${BLUE}[1] Arrêt des services...${NC}"
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "  Arrêt de $service..."
        systemctl stop "$service"
    fi
    
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo "  Désactivation de $service..."
        systemctl disable "$service"
    fi
done

################################################################################
# Supprimer les fichiers de service
################################################################################

echo ""
echo -e "${BLUE}[2] Suppression des fichiers de service...${NC}"
for service in "${SERVICES[@]}"; do
    service_file="/etc/systemd/system/${service}.service"
    if [ -f "$service_file" ]; then
        echo "  Suppression de $service_file"
        rm -f "$service_file"
    fi
done

# Recharger systemd
echo "  Rechargement de systemd..."
systemctl daemon-reload

################################################################################
# Supprimer les règles udev
################################################################################

echo ""
echo -e "${BLUE}[3] Suppression des règles udev...${NC}"

udev_rules=("/etc/udev/rules.d/99-vesc.rules" 
            "/etc/udev/rules.d/99-lidar.rules" 
            "/etc/udev/rules.d/99-oak.rules")

for rule in "${udev_rules[@]}"; do
    if [ -f "$rule" ]; then
        echo "  Suppression de $rule"
        rm -f "$rule"
    fi
done

# Recharger udev
echo "  Rechargement des règles udev..."
udevadm control --reload-rules
udevadm trigger

################################################################################
# Nettoyage optionnel
################################################################################

echo ""
echo -e "${YELLOW}Nettoyage optionnel:${NC}"
echo ""
read -p "Supprimer l'environnement virtuel? (oui/non) " -n 3 -r
echo
if [[ $REPLY =~ ^[Oo][Uu][Ii]$ ]]; then
    VENV_DIR="$(dirname "$0")/venv"
    if [ -d "$VENV_DIR" ]; then
        echo "  Suppression de $VENV_DIR..."
        rm -rf "$VENV_DIR"
    fi
fi

################################################################################
# Fin
################################################################################

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Désinstallation terminée${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Note:${NC} Le code source n'a pas été supprimé."
echo "Pour supprimer complètement le projet:"
echo "  rm -rf $(dirname "$0")"
echo ""
