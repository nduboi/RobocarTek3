# Déploiement Robocar - NVIDIA Jetson Nano

## 📋 Vue d'ensemble

Ce document décrit le processus de déploiement complet du système Robocar sur une NVIDIA Jetson Nano. Le système est composé de 3 modules autonomes gérés par systemd :

- **Controller** : Contrôle des moteurs via VESC (port 5000)
- **Camera** : Flux vidéo OAK-D via TCP (port 4488)
- **Lidar** : Données LD19 via UDP (port 15975)

## 🏗️ Architecture du Déploiement

```
/home/user/robocar/RobocarTek3/
├── camera/              # Sous-module git (OAK-D)
│   ├── video_sender.py
│   └── requirements.txt
├── lidar/               # Sous-module git (LD19)
│   ├── lidar_radar.py
│   └── requirements.txt
├── controller/          # Sous-module git (VESC)
│   ├── server/robocar_server.py
│   ├── config/server_config.yaml
│   └── requirements.txt
├── venv/                # Environnement Python partagé
├── systemd/             # Templates de services
│   ├── robocar-controller.service
│   ├── robocar-camera.service
│   └── robocar-lidar.service
└── install_all.sh       # Script d'installation
```

## 🚀 Installation

### Prérequis

- NVIDIA Jetson Nano avec JetPack 4.x ou supérieur
- Accès sudo
- Connexion Internet

### Étape 1 : Clone du dépôt

```bash
cd ~
git clone --recurse-submodules https://github.com/votre-repo/RobocarTek3.git
cd RobocarTek3
```

### Étape 2 : Exécution de l'installation

```bash
sudo ./install_all.sh
```

Le script effectue automatiquement :

1. ✅ Mise à jour des sous-modules git
2. ✅ Installation des dépendances système (OpenCV, NumPy système)
3. ✅ Configuration des règles udev (VESC, Lidar, OAK-D)
4. ✅ Création d'un venv avec `--system-site-packages`
5. ✅ Installation des requirements.txt de chaque module
6. ✅ Création des services systemd
7. ✅ Configuration des permissions

### Étape 3 : Vérification des scripts Python

**IMPORTANT** : Avant d'activer les services, vérifiez que les fichiers Python principaux existent :

```bash
# Camera
ls -la camera/video_sender.py

# Lidar
ls -la lidar/lidar_radar.py

# Controller
ls -la controller/server/robocar_server.py
```

Si ces fichiers n'existent pas, vous devez les créer ou ajuster les chemins dans les services systemd.

### Étape 4 : Adaptation des services (si nécessaire)

Les services sont créés avec des arguments par défaut. Vérifiez et adaptez si besoin :

#### Controller

```bash
sudo nano /etc/systemd/system/robocar-controller.service
```

Arguments par défaut :
- `--config config/server_config.yaml`

Configuration dans [controller/config/server_config.yaml](controller/config/server_config.yaml):
- Port contrôle : 5000 (UDP)
- Port télémétrie : 5001 (UDP)
- Port série VESC : /dev/ttyACM0

#### Camera

```bash
sudo nano /etc/systemd/system/robocar-camera.service
```

Arguments par défaut :
- `--host 0.0.0.0` : Écoute sur toutes les interfaces
- `--port 4488` : Port TCP pour flux vidéo

#### Lidar

```bash
sudo nano /etc/systemd/system/robocar-lidar.service
```

Arguments par défaut :
- `--port 15975` : Port UDP pour broadcast des données
- `--serial /dev/ttyUSB0` : Port série du lidar

### Étape 5 : Activer et démarrer les services

```bash
# Activer les services au démarrage
sudo systemctl enable robocar-controller
sudo systemctl enable robocar-camera
sudo systemctl enable robocar-lidar

# Démarrer les services
sudo systemctl start robocar-controller
sudo systemctl start robocar-camera
sudo systemctl start robocar-lidar
```

### Étape 6 : Vérifier l'état

```bash
# État global
sudo systemctl status robocar-controller
sudo systemctl status robocar-camera
sudo systemctl status robocar-lidar

# Logs en temps réel
journalctl -u robocar-controller -f
journalctl -u robocar-camera -f
journalctl -u robocar-lidar -f
```

## 🔧 Configuration des Ports et Arguments

### Module Controller

**Fichier** : `controller/server/robocar_server.py`

**Arguments supportés** :
```python
parser.add_argument('--config', default='config/server_config.yaml',
                    help='Fichier de configuration YAML')
```

**Configuration via YAML** (`config/server_config.yaml`) :
```yaml
server:
  control_port: 5000        # Port UDP pour commandes
  telemetry_port: 5001      # Port UDP pour télémétrie
  bind_address: "0.0.0.0"   # Adresse d'écoute

robocar:
  port: "/dev/ttyACM0"      # Port série VESC
  baudrate: 115200
  throttle_max: 0.1
```

### Module Camera

**Fichier** : `camera/video_sender.py` (à vérifier)

**Arguments attendus** :
```bash
--host 0.0.0.0    # Adresse d'écoute
--port 4488       # Port TCP pour envoi vidéo
```

### Module Lidar

**Fichier** : `lidar/lidar_radar.py` (à vérifier)

**Arguments attendus** :
```bash
--port 15975              # Port UDP pour broadcast
--serial /dev/ttyUSB0     # Port série du lidar
```

## 📝 Règles udev

Les règles udev sont configurées automatiquement par `install_all.sh` :

### VESC (Controller)

```
/etc/udev/rules.d/99-vesc.rules
```
- Symlink : `/dev/ttyVESC`
- Permissions : 0666

### Lidar LD19

```
/etc/udev/rules.d/99-lidar.rules
```
- Symlink : `/dev/ttyLIDAR`
- Permissions : 0666

### OAK-D (Camera)

```
/etc/udev/rules.d/99-oak.rules
```
- Group : plugdev
- Permissions : 0666

**IMPORTANT** : Redémarrez après installation pour que les règles prennent effet :

```bash
sudo reboot
```

## 🐛 Dépannage

### Service ne démarre pas

```bash
# Vérifier les logs
journalctl -u robocar-controller -n 50

# Vérifier la syntaxe du service
systemd-analyze verify /etc/systemd/system/robocar-controller.service

# Tester manuellement
cd /home/user/RobocarTek3/controller
/home/user/RobocarTek3/venv/bin/python server/robocar_server.py
```

### Problème de port série

```bash
# Lister les ports série
ls -la /dev/tty*

# Vérifier les permissions
groups  # Doit contenir 'dialout'

# Recharger les règles udev
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Import OpenCV échoue

Le système utilise OpenCV optimisé pour Jetson (installé via apt).

```bash
# Vérifier OpenCV système
python3 -c "import cv2; print(cv2.__version__)"

# Réinstaller si nécessaire
sudo apt-get install --reinstall python3-opencv
```

### Module camera/lidar vide

Si les sous-modules ne sont pas initialisés :

```bash
cd /home/user/RobocarTek3
git submodule update --init --recursive
```

## 🔄 Gestion des services

### Arrêter un service

```bash
sudo systemctl stop robocar-controller
```

### Désactiver le démarrage automatique

```bash
sudo systemctl disable robocar-controller
```

### Redémarrer un service

```bash
sudo systemctl restart robocar-controller
```

### Recharger la configuration

Après modification d'un fichier .service :

```bash
sudo systemctl daemon-reload
sudo systemctl restart robocar-controller
```

## 📊 Monitoring

### Vérifier l'uptime

```bash
systemctl status robocar-* --no-pager
```

### Logs des 24 dernières heures

```bash
journalctl -u robocar-controller --since "24 hours ago"
```

### Erreurs uniquement

```bash
journalctl -u robocar-controller -p err
```

## 🔐 Sécurité

Les services s'exécutent avec l'utilisateur qui a lancé l'installation (via `sudo`). Ils n'ont **pas** les privilèges root.

Groupes requis :
- `dialout` : Accès aux ports série (VESC, Lidar)
- `plugdev` : Accès USB (OAK-D)
- `video` : Accès caméra

## 📦 Mise à jour

Pour mettre à jour le code :

```bash
cd /home/user/RobocarTek3

# Arrêter les services
sudo systemctl stop robocar-*

# Mettre à jour
git pull
git submodule update --remote --merge

# Mettre à jour les dépendances si nécessaire
source venv/bin/activate
pip install -r controller/requirements.txt --upgrade
pip install -r camera/requirements.txt --upgrade
pip install -r lidar/requirements.txt --upgrade

# Redémarrer
sudo systemctl start robocar-*
```

## ⚙️ Variables d'environnement

Configurées dans les fichiers .service :

- `PYTHONUNBUFFERED=1` : Logs en temps réel
- `PYTHONPATH` : Chemin du module

## 🎯 Ordre de démarrage

Les services démarrent après `network-online.target`, garantissant que :
1. Le réseau est prêt
2. Les interfaces sont configurées
3. Les services peuvent binder leurs sockets

## 📞 Support

Pour toute question :
- Consulter les logs : `journalctl -u robocar-controller -f`
- Vérifier [controller/README.md](controller/README.md)
- GitHub Issues : https://github.com/votre-repo/RobocarTek3/issues

---

**Auteur** : Système de déploiement automatisé pour Robocar  
**Version** : 1.0  
**Date** : 2026-02-04
