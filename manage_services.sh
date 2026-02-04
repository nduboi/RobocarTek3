#!/bin/bash
################################################################################
# manage_services.sh - Script de gestion des services Robocar
# 
# Usage: ./manage_services.sh {start|stop|restart|status|enable|disable|logs}
################################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICES=("robocar-controller" "robocar-camera" "robocar-lidar")

print_usage() {
    echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|errors}"
    echo ""
    echo "Commandes:"
    echo "  start    - Démarrer tous les services"
    echo "  stop     - Arrêter tous les services"
    echo "  restart  - Redémarrer tous les services"
    echo "  status   - Afficher l'état de tous les services"
    echo "  enable   - Activer au démarrage"
    echo "  disable  - Désactiver au démarrage"
    echo "  logs     - Afficher les logs en temps réel"
    echo "  errors   - Afficher uniquement les erreurs"
}

start_services() {
    echo -e "${BLUE}Démarrage des services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${GREEN}► ${service}${NC}"
        sudo systemctl start "$service"
    done
    echo ""
    status_services
}

stop_services() {
    echo -e "${BLUE}Arrêt des services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}■ ${service}${NC}"
        sudo systemctl stop "$service"
    done
    echo ""
    status_services
}

restart_services() {
    echo -e "${BLUE}Redémarrage des services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}⟳ ${service}${NC}"
        sudo systemctl restart "$service"
    done
    echo ""
    status_services
}

status_services() {
    echo -e "${BLUE}État des services:${NC}"
    echo ""
    for service in "${SERVICES[@]}"; do
        sudo systemctl status "$service" --no-pager -l | head -n 10
        echo ""
    done
}

enable_services() {
    echo -e "${BLUE}Activation au démarrage...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${GREEN}✓ ${service}${NC}"
        sudo systemctl enable "$service"
    done
}

disable_services() {
    echo -e "${BLUE}Désactivation au démarrage...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}✗ ${service}${NC}"
        sudo systemctl disable "$service"
    done
}

show_logs() {
    echo -e "${BLUE}Logs en temps réel (Ctrl+C pour quitter):${NC}"
    echo ""
    sudo journalctl -u robocar-controller -u robocar-camera -u robocar-lidar -f
}

show_errors() {
    echo -e "${RED}Erreurs récentes:${NC}"
    echo ""
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}=== ${service} ===${NC}"
        sudo journalctl -u "$service" -p err --since "24 hours ago" --no-pager
        echo ""
    done
}

# Main
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    enable)
        enable_services
        ;;
    disable)
        disable_services
        ;;
    logs)
        show_logs
        ;;
    errors)
        show_errors
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
