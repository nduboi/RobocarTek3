# Robocar PC Dashboard - Station Sol de Pilotage

## 📋 Description

Application PC pour piloter le robot Robocar depuis une station sol. Interface graphique temps réel avec flux vidéo, visualisation lidar et contrôle clavier.

## 🏗️ Architecture

```
pc_dashboard/
├── main_pc.py              # Application principale
├── video_receiver.py       # Réception flux vidéo (TCP 4488)
├── lidar_receiver.py       # Réception lidar (UDP 15975)
├── controller_sender.py    # Envoi commandes (UDP 5000)
├── protocol_client.py      # Protocole de communication
├── requirements.txt        # Dépendances Python
└── README.md              # Ce fichier
```

## ⚡ Installation Rapide

### 1. Créer un environnement virtuel

```bash
cd pc_dashboard
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
python main_pc.py --robot-ip 10.84.106.222
```

## 🎮 Contrôles Clavier

### Contrôle du Robot

| Touche | Action |
|--------|--------|
| **Z** | Accélérer (throttle +) |
| **S** | Freiner/Reculer (throttle -) |
| **Q** | Tourner à gauche |
| **D** | Tourner à droite |
| **X** | Position neutre (arrêt) |
| **ESPACE** | Arrêt d'urgence |

### Commandes Sonores

| Touche | Son |
|--------|-----|
| **K** | Klaxon |
| **1** | Son Epitech |
| **2** | Son Satelisation |
| **3** | Son Peter |
| **4** | Son Polizia |

### Autres Commandes

| Touche | Action |
|--------|--------|
| **+** / **=** | Augmenter vitesse maximale |
| **-** | Diminuer vitesse maximale |
| **H** | Afficher/Masquer l'aide |
| **ESC** / **Q** | Quitter l'application |

## 📡 Protocoles de Communication

### Vidéo (TCP 4488)

**Format** : `[4 bytes taille big-endian] + [JPEG data]`

Le serveur robot envoie les frames encodées en JPEG haute qualité (90%).

### Lidar (UDP 15975)

**Format JSON** :
```json
{
  "timestamp": 1234567890.123,
  "fragment": 0,
  "total_fragments": 2,
  "points": [
    {"a": 45.5, "d": 1200, "c": 255},
    {"a": 46.0, "d": 1205, "c": 250}
  ]
}
```

- `a` : Angle en degrés (0-360)
- `d` : Distance en mm
- `c` : Confidence (0-255)

### Contrôle (UDP 5000)

**Format JSON** :
```json
{
  "version": "1.0",
  "timestamp": 1234567890.123,
  "source": "pc_dashboard",
  "type": "control",
  "data": {
    "throttle": 0.5,
    "steering": -0.3
  },
  "commands": ["horn"],
  "sequence": 42
}
```

- `throttle` : -1.0 (arrière max) à 1.0 (avant max)
- `steering` : -1.0 (gauche max) à 1.0 (droite max)
- `commands` : Liste de commandes ponctuelles optionnelles

## 🖥️ Interface Graphique

### Fenêtre Vidéo

- **Flux caméra** en temps réel
- **Overlay de contrôle** :
  - Barre de throttle (vert = avant, rouge = arrière)
  - Barre de steering avec indicateur de position
  - FPS du flux vidéo
  - Statut de connexion
- **Aide contextuelle** (toggle avec H)
- **Préparé pour YOLO** : Le flux peut être facilement intégré avec un modèle YOLO pour détection d'objets

### Fenêtre Lidar

- **Vue Top-Down** : Points lidar en temps réel
- **Grille circulaire** : Distances 0.5m, 1m, 1.5m, 2m, 2.5m, 3m
- **Robot au centre** : Triangle vert indiquant la position et l'orientation
- **Points blancs** : Obstacles détectés (intensité = confidence)
- **Info** : Nombre de points et statistiques

## 🔧 Architecture Technique

### Multithreading

L'application utilise 3 threads séparés pour éviter les blocages :

1. **VideoReceiver Thread** : Réception et décodage TCP des frames JPEG
2. **LidarReceiver Thread** : Réception et reconstruction UDP des points lidar
3. **ControllerSender Thread** : Envoi périodique des commandes avec heartbeat

### Thread-Safe

- Tous les modules utilisent des `threading.Lock` pour l'accès concurrent aux données
- Les callbacks sont gérés de manière sécurisée
- Arrêt propre de tous les threads avec `daemon=True` et `join()`

### Performance

- **Fréquence d'envoi** : 20Hz (50ms) pour les commandes de contrôle
- **Heartbeat** : 5Hz (200ms) quand aucune commande active
- **Vidéo** : Limité par le flux du robot (généralement 20-30 FPS)
- **Lidar** : Reconstruction des fragments en temps réel

## 📊 Statistiques en Temps Réel

Le dashboard affiche et log périodiquement :

- **Vidéo** : Frames reçues, MB transférés, FPS
- **Lidar** : Paquets reçus, nombre de points actifs
- **Contrôleur** : Messages envoyés, throttle/steering actuels, erreurs

```
=== Statistiques ===
Video: 1234 frames, 45.6 MB
Lidar: 567 packets, 890 points
Controller: 234 messages, throttle=0.50, steering=-0.30
```

## 🚀 Utilisation Avancée

### Changer l'IP du robot

```bash
python main_pc.py --robot-ip 192.168.1.100
```

### Mode debug

```bash
python main_pc.py --log-level DEBUG
```

### Tester sans robot (mode simulation)

Si le robot n'est pas connecté :
- La vidéo affichera "En attente du flux video..."
- Le lidar affichera une vue vide
- Les commandes seront envoyées mais sans réponse

## 🔮 Intégration YOLO (Préparation)

Le code est préparé pour intégrer un modèle YOLO :

```python
# Dans video_receiver.py, modifier le callback:
def yolo_callback(frame):
    # Inférence YOLO
    results = model(frame)
    
    # Dessiner bounding boxes
    annotated_frame = results.render()[0]
    
    # Afficher
    cv2.imshow("YOLO Detection", annotated_frame)
```

Dé-commenter dans `requirements.txt` :
```
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0
```

## 🐛 Dépannage

### Problème de connexion vidéo

```
❌ Erreur de connexion: [Errno 111] Connection refused
```

**Solutions** :
1. Vérifier que le service caméra tourne sur le robot : `systemctl status robocar-camera`
2. Vérifier l'IP du robot : `ping 10.84.106.222`
3. Vérifier le firewall : `sudo ufw allow 4488/tcp`

### Lidar ne reçoit rien

```
Lidar: 0 packets, 0 points
```

**Solutions** :
1. Vérifier le service lidar : `systemctl status robocar-lidar`
2. Vérifier le port UDP : `ss -tuln | grep 15975`
3. S'assurer d'être sur le même réseau que le robot

### Robot ne répond pas aux commandes

**Solutions** :
1. Vérifier le service controller : `systemctl status robocar-controller`
2. Vérifier les logs du robot : `journalctl -u robocar-controller -f`
3. Tester avec heartbeat uniquement (ne pas bouger, juste observer les logs)

## 📝 Développement

### Ajouter un nouveau type de commande

1. Ajouter dans `protocol_client.py` :
```python
def create_custom_command(source: str, command: str):
    # ...
```

2. Ajouter le raccourci clavier dans `main_pc.py` :
```python
elif key == ord('y'):
    self.controller_sender.send_command("custom_command")
```

### Personnaliser l'affichage

Modifier les méthodes `_render_*` dans `main_pc.py` :
- `_render_video_frame()` : Overlay vidéo
- `_render_lidar_view()` : Vue lidar
- `_render_help_overlay()` : Aide

## 🔐 Sécurité

- **Arrêt d'urgence** : Toujours disponible avec ESPACE
- **Timeout** : Le robot a un watchdog qui arrête le robot si aucune commande reçue pendant 500ms
- **Valeurs clampées** : Throttle et steering limités à [-1.0, 1.0]
- **Arrêt propre** : L'application envoie `emergency_stop` avant de se fermer

## 📞 Support

- **Logs détaillés** : `python main_pc.py --log-level DEBUG`
- **Vérifier les threads** : Tous les modules loggent leur démarrage/arrêt
- **Statistiques** : Appuyez sur les logs pour voir l'activité réseau

## 🎯 Roadmap

- [ ] Intégration YOLO pour détection d'objets
- [ ] Enregistrement du flux vidéo
- [ ] Replay des sessions de conduite
- [ ] Interface Pygame pour plus de contrôle
- [ ] Support manette de jeu (gamepad)
- [ ] Mode autonome avec navigation

---

**Version** : 1.0  
**Date** : 2026-02-04  
**Compatible** : RobocarTek3 v1.0
