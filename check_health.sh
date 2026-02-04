#!/bin/bash
################################################################################
# check_health.sh - Script de vérification de santé du système Robocar
# 
# Vérifie l'état des services, ports, et périphériques
################################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICES=("robocar-controller" "robocar-camera" "robocar-lidar")

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Vérification de santé Robocar${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

################################################################################
# 1. Services systemd
################################################################################

echo -e "${GREEN}[1] État des services systemd${NC}"
echo ""

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "  ${GREEN}✓${NC} $service : ${GREEN}ACTIF${NC}"
        uptime=$(systemctl show -p ActiveEnterTimestamp "$service" --value)
        echo -e "    Démarré : $uptime"
    else
        echo -e "  ${RED}✗${NC} $service : ${RED}INACTIF${NC}"
    fi
done

echo ""

################################################################################
# 2. Ports réseau
################################################################################

echo -e "${GREEN}[2] Ports réseau${NC}"
echo ""

check_port() {
    local port=$1
    local name=$2
    if ss -tuln | grep -q ":$port "; then
        echo -e "  ${GREEN}✓${NC} Port $port ($name) : ${GREEN}OUVERT${NC}"
    else
        echo -e "  ${YELLOW}⚠${NC} Port $port ($name) : ${YELLOW}FERMÉ${NC}"
    fi
}

check_port 5000 "Controller Control"
check_port 5001 "Controller Telemetry"
check_port 4488 "Camera TCP"
check_port 15975 "Lidar UDP"

echo ""

################################################################################
# 3. Périphériques série
################################################################################

echo -e "${GREEN}[3] Périphériques série${NC}"
echo ""

check_serial() {
    local device=$1
    local name=$2
    if [ -e "$device" ]; then
        echo -e "  ${GREEN}✓${NC} $device ($name) : ${GREEN}PRÉSENT${NC}"
        ls -l "$device"
    else
        echo -e "  ${YELLOW}⚠${NC} $device ($name) : ${YELLOW}ABSENT${NC}"
    fi
}

check_serial "/dev/ttyACM0" "VESC"
check_serial "/dev/ttyUSB0" "Lidar"
check_serial "/dev/ttyVESC" "VESC (symlink)"
check_serial "/dev/ttyLIDAR" "Lidar (symlink)"

echo ""

################################################################################
# 4. Périphériques USB
################################################################################

echo -e "${GREEN}[4] Périphériques USB${NC}"
echo ""

if lsusb | grep -iq "03e7"; then
    echo -e "  ${GREEN}✓${NC} OAK-D : ${GREEN}DÉTECTÉ${NC}"
    lsusb | grep "03e7"
else
    echo -e "  ${YELLOW}⚠${NC} OAK-D : ${YELLOW}NON DÉTECTÉ${NC}"
fi

echo ""

################################################################################
# 5. Environnement Python
################################################################################

echo -e "${GREEN}[5] Environnement Python${NC}"
echo ""

VENV_DIR="$(dirname "$0")/venv"

if [ -d "$VENV_DIR" ]; then
    echo -e "  ${GREEN}✓${NC} Virtualenv : ${GREEN}PRÉSENT${NC}"
    echo -e "    Chemin : $VENV_DIR"
    
    # Activer et tester
    source "$VENV_DIR/bin/activate"
    
    # Version Python
    python_version=$(python --version 2>&1)
    echo -e "    Python : $python_version"
    
    # Test des modules critiques
    if python -c "import cv2" 2>/dev/null; then
        cv_version=$(python -c "import cv2; print(cv2.__version__)")
        echo -e "    ${GREEN}✓${NC} OpenCV $cv_version"
    else
        echo -e "    ${RED}✗${NC} OpenCV : ERREUR"
    fi
    
    if python -c "import numpy" 2>/dev/null; then
        np_version=$(python -c "import numpy; print(numpy.__version__)")
        echo -e "    ${GREEN}✓${NC} NumPy $np_version"
    else
        echo -e "    ${RED}✗${NC} NumPy : ERREUR"
    fi
    
    if python -c "import serial" 2>/dev/null; then
        serial_version=$(python -c "import serial; print(serial.__version__)")
        echo -e "    ${GREEN}✓${NC} PySerial $serial_version"
    else
        echo -e "    ${RED}✗${NC} PySerial : ERREUR"
    fi
    
    if python -c "import depthai" 2>/dev/null; then
        depthai_version=$(python -c "import depthai; print(depthai.__version__)")
        echo -e "    ${GREEN}✓${NC} DepthAI $depthai_version"
    else
        echo -e "    ${YELLOW}⚠${NC} DepthAI : NON INSTALLÉ"
    fi
    
    deactivate
else
    echo -e "  ${RED}✗${NC} Virtualenv : ${RED}ABSENT${NC}"
fi

echo ""

################################################################################
# 6. Logs récents
################################################################################

echo -e "${GREEN}[6] Erreurs récentes (dernières 24h)${NC}"
echo ""

error_count=0
for service in "${SERVICES[@]}"; do
    count=$(journalctl -u "$service" -p err --since "24 hours ago" --no-pager | wc -l)
    if [ "$count" -gt 0 ]; then
        echo -e "  ${RED}✗${NC} $service : $count erreur(s)"
        error_count=$((error_count + count))
    else
        echo -e "  ${GREEN}✓${NC} $service : Aucune erreur"
    fi
done

echo ""

################################################################################
# 7. Ressources système
################################################################################

echo -e "${GREEN}[7] Ressources système${NC}"
echo ""

# CPU
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo -e "  CPU : ${cpu_usage}%"

# Mémoire
mem_info=$(free -h | awk 'NR==2{printf "  Mémoire : %s / %s (%.0f%%)\n", $3,$2,$3*100/$2 }')
echo -e "$mem_info"

# Température (si disponible)
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    temp_c=$((temp / 1000))
    if [ "$temp_c" -gt 80 ]; then
        echo -e "  ${RED}⚠${NC} Température : ${RED}${temp_c}°C${NC}"
    else
        echo -e "  ${GREEN}✓${NC} Température : ${temp_c}°C"
    fi
fi

# Uptime
uptime_info=$(uptime -p)
echo -e "  Uptime : $uptime_info"

echo ""

################################################################################
# Résumé
################################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Résumé${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

active_services=0
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        active_services=$((active_services + 1))
    fi
done

echo -e "Services actifs : ${active_services}/${#SERVICES[@]}"
echo -e "Erreurs (24h) : $error_count"

if [ "$active_services" -eq "${#SERVICES[@]}" ] && [ "$error_count" -eq 0 ]; then
    echo -e "\n${GREEN}✓ Système opérationnel${NC}\n"
    exit 0
elif [ "$active_services" -gt 0 ]; then
    echo -e "\n${YELLOW}⚠ Système partiellement opérationnel${NC}\n"
    exit 1
else
    echo -e "\n${RED}✗ Système non opérationnel${NC}\n"
    exit 2
fi
