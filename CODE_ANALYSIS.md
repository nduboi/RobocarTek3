# Analyse du Code et Configuration des Services

Ce document analyse le code existant pour documenter les arguments et configurations nécessaires aux services systemd.

## 📋 Résumé de l'Analyse

### ✅ Module Controller - COMPLET

**Fichier principal** : `controller/server/robocar_server.py`

**Point d'entrée** : Fonction `main()` avec argparse

**Arguments supportés** :
```python
--config <fichier.yaml>  # Défaut: config/server_config.yaml
```

**Configuration via YAML** (`controller/config/server_config.yaml`) :

```yaml
server:
  control_port: 5000          # Port UDP pour recevoir commandes
  telemetry_port: 5001        # Port UDP pour envoyer télémétrie
  bind_address: "0.0.0.0"     # Adresse d'écoute
  telemetry_rate_hz: 20       # Fréquence de publication

safety:
  watchdog_timeout_ms: 500
  emergency_stop_timeout_ms: 1000

robocar:
  port: "/dev/ttyACM0"        # Port série VESC
  baudrate: 115200
  throttle_max: 0.1
  steering_left: 0.0
  steering_right: 1.0
  steering_center: 0.5

logging:
  enable: true
  level: "INFO"
  log_file: "logs/server_{date}.log"
  log_commands: true
  session_log_file: "logs/session_{date}.jsonl"
```

**Service systemd** :
```ini
ExecStart=/path/to/venv/bin/python server/robocar_server.py --config config/server_config.yaml
WorkingDirectory=/path/to/controller
```

**Dépendances** (requirements.txt) :
- pygame>=2.6.0
- PyVESC (via git)
- pyserial>=3.5
- pythoncrc>=1.2
- pyyaml>=6.0
- pynput>=1.7.6

### ⚠️ Module Camera - À VÉRIFIER

**Fichier attendu** : `camera/video_sender.py` (ou `video.py`)

**⚠️ STATUT** : Les dossiers camera et lidar sont actuellement vides (sous-modules non initialisés)

**Arguments attendus** (à confirmer une fois les sous-modules initialisés) :
```bash
--host <adresse>   # Défaut suggéré: 0.0.0.0
--port <port>      # Défaut suggéré: 4488
```

**Service systemd** (provisoire) :
```ini
ExecStart=/path/to/venv/bin/python video_sender.py --host 0.0.0.0 --port 4488
WorkingDirectory=/path/to/camera
```

**Dépendances** (requirements.txt créé) :
- depthai>=2.20.0
- opencv-python (commenté - utiliser version système)
- numpy (commenté - utiliser version système)

**Action requise** :
1. Initialiser le sous-module : `git submodule update --init camera`
2. Vérifier le nom exact du fichier Python principal
3. Vérifier les arguments acceptés par le script
4. Ajuster le service systemd si nécessaire

### ⚠️ Module Lidar - À VÉRIFIER

**Fichier attendu** : `lidar/lidar_radar.py`

**⚠️ STATUT** : Les dossiers camera et lidar sont actuellement vides (sous-modules non initialisés)

**Arguments attendus** (à confirmer une fois les sous-modules initialisés) :
```bash
--port <port>      # Défaut suggéré: 15975 (port UDP)
--serial <device>  # Défaut suggéré: /dev/ttyUSB0
```

**Service systemd** (provisoire) :
```ini
ExecStart=/path/to/venv/bin/python lidar_radar.py --port 15975 --serial /dev/ttyUSB0
WorkingDirectory=/path/to/lidar
```

**Dépendances** (requirements.txt créé) :
- pyserial>=3.5
- numpy (commenté - utiliser version système)

**Action requise** :
1. Initialiser le sous-module : `git submodule update --init lidar`
2. Vérifier le nom exact du fichier Python principal
3. Vérifier les arguments acceptés par le script
4. Ajuster le service systemd si nécessaire

## 🔍 Vérification des Sous-modules

### État actuel

```bash
$ git submodule status
-b4fa6e4299048ad60d4e07efdcf761e0a2133505 camera
 45a87f8c5e3dc9c8f317156fe2265536206db09a controller (heads/network-control)
-dd285b7ba1b107b9b289a75cf81af9357dfcfe27 lidar
```

Le préfixe `-` indique que les sous-modules ne sont pas initialisés.

### Initialisation des sous-modules

```bash
git submodule update --init --recursive
```

Cette commande sera exécutée automatiquement par `install_all.sh`.

## 📝 Recommandations

### 1. Après installation

Une fois `install_all.sh` exécuté, vérifiez que les fichiers Python existent :

```bash
ls -la camera/video_sender.py
ls -la lidar/lidar_radar.py
ls -la controller/server/robocar_server.py
```

### 2. Si les noms de fichiers diffèrent

Ajustez les services systemd :

```bash
sudo nano /etc/systemd/system/robocar-camera.service
sudo nano /etc/systemd/system/robocar-lidar.service
sudo systemctl daemon-reload
```

### 3. Test des modules individuels

Utilisez le script de test pour vérifier chaque module :

```bash
./test_modules.sh controller
./test_modules.sh camera
./test_modules.sh lidar
```

### 4. Vérification des arguments

Pour camera et lidar, vérifiez les arguments supportés :

```bash
source venv/bin/activate
cd camera
python video_sender.py --help
cd ../lidar
python lidar_radar.py --help
```

## 🔧 Ajustements Potentiels

### Si le script camera s'appelle autrement

Par exemple, si c'est `video.py` au lieu de `video_sender.py` :

```bash
sudo nano /etc/systemd/system/robocar-camera.service
# Modifier la ligne ExecStart:
ExecStart=/path/to/venv/bin/python video.py --host 0.0.0.0 --port 4488
```

### Si les arguments sont différents

Exemple : si camera n'utilise pas `--host` et `--port` mais juste `--tcp-port` :

```bash
ExecStart=/path/to/venv/bin/python video_sender.py --tcp-port 4488
```

### Si le port série du lidar est différent

Vérifier les ports disponibles :

```bash
ls -la /dev/ttyUSB*
ls -la /dev/ttyLIDAR  # Symlink créé par règle udev
```

Ajuster dans le service :

```bash
ExecStart=/path/to/venv/bin/python lidar_radar.py --port 15975 --serial /dev/ttyLIDAR
```

## 🎯 Structure des Ports (Par Défaut)

| Service | Type | Port | Description |
|---------|------|------|-------------|
| Controller | UDP IN | 5000 | Réception commandes de pilotage |
| Controller | UDP OUT | 5001 | Broadcast télémétrie |
| Camera | TCP OUT | 4488 | Envoi flux vidéo |
| Lidar | UDP OUT | 15975 | Broadcast données lidar |

## 📊 Dépendances Système vs Pip

### OpenCV et NumPy

**Stratégie** : Utiliser les versions système (optimisées Jetson)

Installation :
```bash
sudo apt-get install python3-opencv python3-numpy
```

Avantages :
- Optimisation CUDA/GPU pour Jetson
- Performances supérieures
- Pas de compilation

Le venv est créé avec `--system-site-packages` pour accéder à ces paquets.

### Vérification

```bash
source venv/bin/activate
python -c "import cv2; print(cv2.__version__, cv2.getBuildInformation())"
python -c "import numpy; print(numpy.__version__)"
```

## 🔐 Permissions et Groupes

### Groupes requis

L'utilisateur doit appartenir à :
- `dialout` : Accès ports série (VESC, Lidar)
- `plugdev` : Accès USB (OAK-D)
- `video` : Accès caméra

Ajout automatique par `install_all.sh` :
```bash
usermod -a -G dialout,plugdev $USER
```

### Règles udev

Créées automatiquement dans `/etc/udev/rules.d/` :
- `99-vesc.rules` : VESC → /dev/ttyVESC
- `99-lidar.rules` : Lidar → /dev/ttyLIDAR
- `99-oak.rules` : OAK-D permissions

## 🚨 Points d'Attention

### 1. Chemins absolus

Les services systemd utilisent des chemins absolus générés dynamiquement :
- `USER_PLACEHOLDER` remplacé par l'utilisateur
- `INSTALL_DIR_PLACEHOLDER` remplacé par le chemin d'installation
- `VENV_DIR_PLACEHOLDER` remplacé par le chemin du venv

### 2. WorkingDirectory

Crucial pour que les imports Python et les fichiers de config relatifs fonctionnent.

### 3. PYTHONPATH

Défini dans les services pour garantir l'import des modules locaux.

### 4. Restart=always

Les services redémarrent automatiquement en cas de crash (délai : 5s).

## 📖 Documentation Complémentaire

- [DEPLOYMENT.md](DEPLOYMENT.md) : Guide complet de déploiement
- [README.md](README.md) : Vue d'ensemble du projet
- [QUICKSTART.md](QUICKSTART.md) : Installation en 5 minutes
- [controller/README.md](controller/README.md) : Documentation du module controller

---

**Note** : Ce document sera à mettre à jour une fois les sous-modules camera et lidar initialisés et leur code analysé.
