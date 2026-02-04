# RobocarTek3 - Robot Autonome sur NVIDIA Jetson Nano

## 📋 Description

Projet de robot autonome basé sur NVIDIA Jetson Nano avec 3 modules indépendants:

- **🎥 Camera** : Flux vidéo OAK-D (Luxonis) via TCP
- **📡 Lidar** : Capteur LD19 avec broadcast UDP
- **🚗 Controller** : Pilotage moteurs VESC via réseau

## 🏗️ Architecture

```
RobocarTek3/
├── camera/                    # Module caméra OAK-D (git submodule)
│   ├── video_sender.py       # Script d'envoi vidéo TCP
│   └── requirements.txt
│
├── lidar/                     # Module lidar LD19 (git submodule)
│   ├── lidar_radar.py        # Script de broadcast UDP
│   └── requirements.txt
│
├── controller/                # Module contrôle VESC (git submodule)
│   ├── server/
│   │   └── robocar_server.py # Serveur de commande
│   ├── config/
│   │   └── server_config.yaml
│   └── requirements.txt
│
├── systemd/                   # Templates de services systemd
│   ├── robocar-controller.service
│   ├── robocar-camera.service
│   └── robocar-lidar.service
│
├── venv/                      # Environnement Python partagé (créé par install)
│
├── install_all.sh            # ⚙️ Installation automatique
├── manage_services.sh        # 🔧 Gestion des services
├── check_health.sh           # 🏥 Vérification santé système
├── uninstall.sh              # 🗑️ Désinstallation
│
├── DEPLOYMENT.md             # 📖 Guide de déploiement détaillé
└── README.md                 # Ce fichier
```

## 🚀 Installation Rapide

### Prérequis

- NVIDIA Jetson Nano (JetPack 4.x ou supérieur)
- Accès sudo
- Connexion Internet

### Installation en une commande

```bash
cd ~/
git clone --recurse-submodules <VOTRE_REPO_URL> RobocarTek3
cd RobocarTek3
sudo ./install_all.sh
```

Le script d'installation effectue automatiquement:

1. ✅ Mise à jour des sous-modules git
2. ✅ Installation des dépendances système (OpenCV, NumPy optimisés Jetson)
3. ✅ Configuration des règles udev pour VESC, Lidar, OAK-D
4. ✅ Création d'un environnement virtuel Python (`venv`)
5. ✅ Installation des dépendances Python de chaque module
6. ✅ Création des services systemd
7. ✅ Configuration des permissions

### Activation des services

Après installation, activez et démarrez les services:

```bash
# Activer au démarrage
sudo systemctl enable robocar-controller robocar-camera robocar-lidar

# Démarrer les services
sudo systemctl start robocar-controller robocar-camera robocar-lidar

# Vérifier l'état
./check_health.sh
```

## 📡 Ports et Protocoles

| Module | Port | Protocole | Description |
|--------|------|-----------|-------------|
| **Controller** | 5000 | UDP | Réception des commandes de pilotage |
| **Controller** | 5001 | UDP | Broadcast de télémétrie |
| **Camera** | 4488 | TCP | Envoi du flux vidéo |
| **Lidar** | 15975 | UDP | Broadcast des données lidar |

## 🔧 Scripts Utilitaires

### `manage_services.sh` - Gestion des services

```bash
./manage_services.sh start      # Démarrer tous les services
./manage_services.sh stop       # Arrêter tous les services
./manage_services.sh restart    # Redémarrer tous les services
./manage_services.sh status     # Afficher l'état
./manage_services.sh logs       # Logs en temps réel
./manage_services.sh errors     # Afficher les erreurs
```

### `check_health.sh` - Vérification de santé

```bash
./check_health.sh
```

Vérifie:
- État des services systemd
- Ports réseau ouverts
- Périphériques série (VESC, Lidar)
- Périphériques USB (OAK-D)
- Environnement Python
- Erreurs récentes
- Ressources système (CPU, RAM, température)

### `uninstall.sh` - Désinstallation

```bash
sudo ./uninstall.sh
```

Supprime les services et règles udev (conserve le code source).

## 📖 Documentation

### Documentation détaillée

Consultez [DEPLOYMENT.md](DEPLOYMENT.md) pour:
- Guide d'installation pas à pas
- Configuration détaillée des services
- Arguments des scripts Python
- Dépannage
- Monitoring et logs

### Documentation des modules

- **Controller** : [controller/README.md](controller/README.md)
- **Camera** : Voir `camera/` (à documenter)
- **Lidar** : Voir `lidar/` (à documenter)

## 🛠️ Configuration

### Module Controller

Configuration via `controller/config/server_config.yaml`:

```yaml
server:
  control_port: 5000
  telemetry_port: 5001
  bind_address: "0.0.0.0"

robocar:
  port: "/dev/ttyACM0"  # Port série VESC
  baudrate: 115200
  throttle_max: 0.1
```

### Module Camera

Arguments dans `/etc/systemd/system/robocar-camera.service`:
- `--host 0.0.0.0` : Écoute sur toutes les interfaces
- `--port 4488` : Port TCP

### Module Lidar

Arguments dans `/etc/systemd/system/robocar-lidar.service`:
- `--port 15975` : Port UDP
- `--serial /dev/ttyUSB0` : Port série du lidar

## 🔍 Vérification et Monitoring

### Logs en temps réel

```bash
# Tous les services
./manage_services.sh logs

# Service spécifique
journalctl -u robocar-controller -f
journalctl -u robocar-camera -f
journalctl -u robocar-lidar -f
```

### État des services

```bash
systemctl status robocar-controller
systemctl status robocar-camera
systemctl status robocar-lidar
```

### Vérification santé complète

```bash
./check_health.sh
```

## 🔌 Périphériques

### Règles udev

Les règles udev sont configurées automatiquement:

- **VESC** : `/dev/ttyACM0` → `/dev/ttyVESC`
- **Lidar LD19** : `/dev/ttyUSB0` → `/dev/ttyLIDAR`
- **OAK-D** : Permissions group `plugdev`

### Groupes utilisateur

L'utilisateur doit appartenir aux groupes:
- `dialout` : Accès ports série
- `plugdev` : Accès USB
- `video` : Accès caméra

## 🐛 Dépannage

### Service ne démarre pas

```bash
# Vérifier les logs
journalctl -u robocar-controller -n 50

# Tester manuellement
cd controller
../venv/bin/python server/robocar_server.py
```

### Port série introuvable

```bash
# Lister les ports
ls -la /dev/tty*

# Recharger udev
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Sous-modules vides

```bash
git submodule update --init --recursive
```

## 🔄 Mise à jour

```bash
# Arrêter les services
./manage_services.sh stop

# Mettre à jour le code
git pull
git submodule update --remote --merge

# Mettre à jour les dépendances
source venv/bin/activate
pip install -r controller/requirements.txt --upgrade
pip install -r camera/requirements.txt --upgrade
pip install -r lidar/requirements.txt --upgrade
deactivate

# Redémarrer
./manage_services.sh start
```

## ⚡ Démarrage Automatique au Boot

Les services sont configurés pour démarrer automatiquement si activés:

```bash
sudo systemctl enable robocar-controller
sudo systemctl enable robocar-camera
sudo systemctl enable robocar-lidar
```

Ordre de démarrage:
1. Réseau disponible (`network-online.target`)
2. Les 3 services démarrent en parallèle
3. Redémarrage automatique en cas de crash

## 📊 Spécifications Techniques

### Matériel supporté

- **Contrôleur** : NVIDIA Jetson Nano
- **Contrôle moteur** : VESC (via USB/série)
- **Caméra** : Luxonis OAK-D
- **Lidar** : LD19

### Dépendances principales

- Python 3.6+
- OpenCV (version système optimisée Jetson)
- NumPy (version système)
- DepthAI SDK
- PySerial
- PyVESC
- PyYAML

## 📝 Structure des Sous-modules

Ce projet utilise git submodules pour organiser le code:

```bash
# Voir l'état des sous-modules
git submodule status

# Mettre à jour
git submodule update --remote --merge
```

## 🤝 Contribution

Pour contribuer au projet:

1. Forkez le dépôt
2. Créez une branche (`git checkout -b feature/amazing`)
3. Committez vos changements
4. Poussez sur la branche
5. Ouvrez une Pull Request

## 📄 Licence

À définir

## 📞 Support

- **Documentation** : [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues** : GitHub Issues
- **Logs** : `journalctl -u robocar-* -f`

## ✨ Fonctionnalités

- ✅ Déploiement automatisé
- ✅ Services systemd avec redémarrage automatique
- ✅ Monitoring de santé intégré
- ✅ Logs centralisés (journald)
- ✅ Configuration via YAML
- ✅ Environnement Python isolé (venv)
- ✅ Optimisé pour NVIDIA Jetson

---

**Version** : 1.0  
**Date** : 2026-02-04  
**Auteur** : RobocarTek3 Team
