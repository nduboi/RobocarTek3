# 🚀 Guide de Démarrage Rapide - PC Dashboard

## Installation Express (3 étapes)

### 1️⃣ Aller dans le dossier

```bash
cd /home/roussierenoa/Projet/robocar/RobocarTek3/pc_dashboard
```

### 2️⃣ Installer (automatique)

```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

OU manuellement :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Lancer

```bash
# Avec l'IP par défaut (10.84.106.222)
python main_pc.py

# Avec une IP personnalisée
python main_pc.py --robot-ip 192.168.1.100
```

## 🎮 Contrôles Principaux

| Touche | Action |
|--------|--------|
| **Z** | Avancer |
| **S** | Reculer |
| **Q** | Gauche |
| **D** | Droite |
| **ESPACE** | ARRÊT D'URGENCE |
| **X** | Stop (neutre) |
| **K** | Klaxon |
| **ESC** | Quitter |

## 📡 Que fait le Dashboard ?

✅ Affiche le flux vidéo caméra (port 4488)  
✅ Affiche une vue top-down du lidar (port 15975)  
✅ Envoie les commandes de pilotage (port 5000)  
✅ Gère tout en multithreading (pas de lag)  
✅ Interface temps réel avec OpenCV

## 🔧 Dépannage Express

**Vidéo ne s'affiche pas ?**
```bash
# Sur le robot, vérifier :
systemctl status robocar-camera
```

**Robot ne bouge pas ?**
```bash
# Sur le robot, vérifier :
systemctl status robocar-controller
```

**Lidar vide ?**
```bash
# Sur le robot, vérifier :
systemctl status robocar-lidar
```

## 📖 Documentation Complète

Voir [README.md](README.md) pour tous les détails.

---

**Prêt à piloter ! 🏎️**
