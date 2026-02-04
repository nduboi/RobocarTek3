#!/bin/bash
# Script pour configurer le lidar docker sur la Jetson

# 1. Vérifier que le docker est en train de tourner
echo "🔍 Docker lidar:"
docker ps | grep ldrobot

# 2. Voir les logs du docker
echo ""
echo "📋 Logs du docker (dernières 20 lignes):"
docker logs ldrobot-radar-udp 2>/dev/null | tail -20 || docker logs $(docker ps | grep ldrobot | awk '{print $1}') 2>/dev/null | tail -20

# 3. Voir les variables d'environnement/config
echo ""
echo "⚙️  Configuration du docker:"
docker inspect ldrobot-radar-udp 2>/dev/null | grep -E 'Env|Args|Cmd' || docker inspect $(docker ps | grep ldrobot | awk '{print $1}') 2>/dev/null | grep -E 'Env|Args|Cmd'

# 4. Vérifier les ports
echo ""
echo "🔌 Ports:"
netstat -uln | grep 15975 || ss -uln | grep 15975

# 5. Chercher la configuration du lidar
echo ""
echo "📂 Chercher lidar_config ou env files:"
find /home /root /opt 2>/dev/null | grep -E 'lidar|config.*udp' | head -20
