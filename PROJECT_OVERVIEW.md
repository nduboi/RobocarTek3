# 🤖 RobocarTek3 - Projet Complet

## 📋 Vue d'Ensemble du Projet

Ce projet contient **DEUX parties distinctes** :

### 🔧 1. Système Robot (Jetson Nano)
**Localisation** : Racine du projet + sous-modules  
**Déploiement** : `install_all.sh`

Services systemd déployés sur le robot :
- **robocar-camera** : Flux vidéo OAK-D (TCP 4488)
- **robocar-lidar** : Données LD19 (UDP 15975)
- **robocar-controller** : Réception commandes (UDP 5000)

### 💻 2. Station Sol PC (Dashboard)
**Localisation** : `pc_dashboard/`  
**Exécution** : `python main_pc.py`

Application Python qui :
- Reçoit le flux vidéo
- Reçoit les données lidar
- Envoie les commandes de pilotage
- Affiche tout en temps réel

---

## 🚀 Démarrage Complet du Système

### ÉTAPE 1 : Configurer le Robot (UNE FOIS)

Sur la Jetson Nano :

```bash
cd ~/RobocarTek3
sudo ./install_all.sh
sudo systemctl enable robocar-controller robocar-camera robocar-lidar
sudo systemctl start robocar-controller robocar-camera robocar-lidar
sudo reboot
```

Après reboot, vérifier :
```bash
./check_health.sh
```

### ÉTAPE 2 : Lancer le Dashboard PC (À CHAQUE SESSION)

Sur votre PC :

```bash
cd RobocarTek3/pc_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_pc.py --robot-ip 10.84.106.222
```

---

## 📁 Structure Complète du Projet

```
RobocarTek3/
│
├── camera/                      # 📷 Sous-module caméra OAK-D
│   ├── video_sender.py         # Envoie flux TCP
│   └── requirements.txt
│
├── lidar/                       # 📡 Sous-module lidar LD19
│   ├── lidar_radar.py          # Broadcast UDP
│   └── requirements.txt
│
├── controller/                  # 🎮 Sous-module contrôle VESC
│   ├── server/
│   │   └── robocar_server.py   # Serveur de commande
│   ├── config/
│   │   └── server_config.yaml  # Configuration
│   └── requirements.txt
│
├── systemd/                     # 🔧 Services systemd (robot)
│   ├── robocar-controller.service
│   ├── robocar-camera.service
│   └── robocar-lidar.service
│
├── pc_dashboard/                # 💻 Application PC (NOUVEAU)
│   ├── main_pc.py              # Application principale
│   ├── video_receiver.py       # Module vidéo
│   ├── lidar_receiver.py       # Module lidar
│   ├── controller_sender.py    # Module contrôle
│   ├── protocol_client.py      # Protocole
│   ├── requirements.txt        # Dépendances PC
│   ├── README.md               # Doc complète
│   ├── QUICKSTART.md           # Démarrage rapide
│   └── run_dashboard.sh        # Script de lancement
│
├── install_all.sh               # 🛠️ Installation robot
├── manage_services.sh           # 🔧 Gestion services
├── check_health.sh              # 🏥 Vérification santé
├── test_modules.sh              # 🧪 Test modules
├── uninstall.sh                 # 🗑️ Désinstallation
│
├── README.md                    # 📖 Documentation générale
├── DEPLOYMENT.md                # 📚 Guide déploiement robot
├── CODE_ANALYSIS.md             # 🔍 Analyse technique
└── QUICKSTART.md                # ⚡ Guide rapide
```

---

## 🔌 Ports et Protocoles

| Service | Type | Port | Protocole | Description |
|---------|------|------|-----------|-------------|
| **Camera** | TCP | 4488 | `[4B size][JPEG]` | Flux vidéo haute qualité |
| **Lidar** | UDP | 15975 | JSON fragments | Points 3D du lidar |
| **Controller** | UDP | 5000 | JSON | Commandes de pilotage |
| **Telemetry** | UDP | 5001 | JSON | Télémétrie robot (optionnel) |

---

## 📊 Flux de Données

```
┌─────────────────────┐
│   ROBOT (Jetson)    │
│                     │
│  ┌───────────────┐  │
│  │ Camera Sender │──┼──TCP 4488──► PC Dashboard
│  └───────────────┘  │              (video_receiver)
│                     │
│  ┌───────────────┐  │
│  │ Lidar Sender  │──┼──UDP 15975─► PC Dashboard
│  └───────────────┘  │              (lidar_receiver)
│                     │
│  ┌───────────────┐  │
│  │  Controller   │◄─┼──UDP 5000──┐ PC Dashboard
│  │   Receiver    │  │             │ (controller_sender)
│  └───────────────┘  │             │
│                     │             │
│  ┌───────────────┐  │             │
│  │   🤖 VESC     │  │             │
│  │   Motors      │  │             │
│  └───────────────┘  │             │
└─────────────────────┘             │
                                    │
┌─────────────────────┐             │
│   PC DASHBOARD      │             │
│                     │             │
│  ┌──────────────┐   │             │
│  │ Video Window │   │             │
│  │ + Overlay    │   │             │
│  └──────────────┘   │             │
│                     │             │
│  ┌──────────────┐   │             │
│  │ Lidar View   │   │             │
│  │ (Top-Down)   │   │             │
│  └──────────────┘   │             │
│                     │             │
│  ┌──────────────┐   │             │
│  │   Keyboard   │───┼─────────────┘
│  │   Control    │   │
│  └──────────────┘   │
└─────────────────────┘
```

---

## 🎯 Workflow Typique

### Jour 1 : Installation Robot

1. Cloner le repo avec sous-modules
2. Lancer `sudo ./install_all.sh` sur la Jetson
3. Activer les services
4. Rebooter
5. Vérifier avec `./check_health.sh`

### Jour 2+ : Session de Pilotage

1. S'assurer que le robot est allumé et connecté au réseau
2. Vérifier l'IP du robot : `ping 10.84.106.222`
3. Sur le PC : `cd pc_dashboard && python main_pc.py`
4. Piloter avec Z/S/Q/D
5. Appuyer sur ESC pour quitter proprement

---

## 🎮 Contrôles PC Dashboard

**Déplacement**
- `Z` : Avancer
- `S` : Reculer  
- `Q` : Gauche
- `D` : Droite
- `X` : Neutre (arrêt)
- `ESPACE` : Arrêt d'urgence

**Sons**
- `K` : Klaxon
- `1-4` : Sons personnalisés

**Vitesse**
- `+` : Augmenter vitesse max
- `-` : Diminuer vitesse max

**Interface**
- `H` : Toggle aide
- `ESC` / `Q` : Quitter

---

## 🔍 Vérification et Debugging

### Sur le Robot

```bash
# État des services
./manage_services.sh status

# Logs en temps réel
./manage_services.sh logs

# Santé complète
./check_health.sh

# Logs spécifiques
journalctl -u robocar-camera -f
journalctl -u robocar-lidar -f
journalctl -u robocar-controller -f
```

### Sur le PC

```bash
# Mode debug
python main_pc.py --log-level DEBUG

# Tester réception vidéo seule
python -c "from video_receiver import VideoReceiver; vr = VideoReceiver('10.84.106.222'); vr.start(); import time; time.sleep(10)"
```

---

## 📚 Documentation Détaillée

- **Robot** :
  - [README.md](README.md) - Vue générale
  - [DEPLOYMENT.md](DEPLOYMENT.md) - Déploiement détaillé
  - [CODE_ANALYSIS.md](CODE_ANALYSIS.md) - Analyse technique
  - [QUICKSTART.md](QUICKSTART.md) - Démarrage rapide robot

- **PC Dashboard** :
  - [pc_dashboard/README.md](pc_dashboard/README.md) - Documentation complète
  - [pc_dashboard/QUICKSTART.md](pc_dashboard/QUICKSTART.md) - Démarrage rapide PC

---

## 🚨 Problèmes Courants

### ❌ Dashboard ne se connecte pas au robot

**Symptômes** : "En attente du flux video..." ou Lidar vide

**Solutions** :
1. Vérifier IP : `ping 10.84.106.222`
2. Vérifier services robot : `./manage_services.sh status`
3. Vérifier firewall : `sudo ufw status`
4. Redémarrer services : `./manage_services.sh restart`

### ❌ Robot ne bouge pas

**Symptômes** : Commandes envoyées mais robot immobile

**Solutions** :
1. Vérifier logs controller : `journalctl -u robocar-controller -f`
2. Vérifier VESC connecté : `ls -la /dev/ttyACM*`
3. Tester manuellement : `./test_modules.sh controller`
4. Vérifier watchdog timeout

### ❌ Vidéo laggy

**Solutions** :
1. Réduire qualité JPEG dans `camera/video_sender.py` (90 → 80)
2. Vérifier bande passante réseau
3. Utiliser connexion filaire au lieu de WiFi

---

## 🎓 Pour Aller Plus Loin

### Intégration YOLO

Le dashboard est préparé pour YOLO :

```bash
cd pc_dashboard
pip install torch torchvision ultralytics
```

Modifier `main_pc.py` pour ajouter l'inférence sur le flux vidéo.

### Enregistrement de Sessions

Ajouter dans `main_pc.py` :

```python
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('session.avi', fourcc, 20.0, (640, 480))
```

### Mode Autonome

Créer un nouveau sender qui :
1. Analyse le flux vidéo (YOLO)
2. Analyse les données lidar
3. Prend des décisions automatiques
4. Envoie les commandes au controller

---

## 🤝 Contribution

Le projet est modulaire :

- **Robot** : Ajouter des capteurs, améliorer les protocoles
- **Dashboard** : Nouvelles visualisations, contrôle gamepad, IA
- **Protocole** : Extensions pour plus de télémétrie

---

## 📞 Support

- **Robot** : Consulter logs avec `./manage_services.sh logs`
- **Dashboard** : Mode debug avec `--log-level DEBUG`
- **Réseau** : `tcpdump -i any port 4488 or port 15975 or port 5000`

---

**Version Système** : 1.0  
**Version Dashboard** : 1.0  
**Date** : 2026-02-04  
**Statut** : ✅ Opérationnel

🎉 **Prêt à rouler !**
