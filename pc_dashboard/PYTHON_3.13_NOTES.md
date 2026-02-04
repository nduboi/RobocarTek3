# 🎯 Guide Rapide - IA avec Python 3.13

## ✅ Installation réussie!

Votre environnement est configuré avec:
- ✅ **YOLOv8n** - Détection d'objets (voitures, piétons, etc.)
- ✅ **OpenVINO** - Runtime d'inférence
- ⚠️ **Road Segmentation** - Non installé (Python 3.13 incompatible avec omz_downloader)

## 🚀 Utilisation

### Lancer le dashboard avec IA (YOLOv8 uniquement)

```bash
cd ~/Projet/robocar/RobocarTek3
./run.sh
```

Le dashboard va:
- ✅ Détecter les **véhicules** (rectangles orange)
- ✅ Détecter les **piétons** (rectangles rouges)
- ✅ Détecter les **feux et panneaux** (rectangles cyan)
- ✅ Détecter les **places de parking** (zones vertes avec "P")
- ⚠️ Pas de segmentation de route (modèle OpenVINO manquant)

## 📊 Ce que vous verrez

```
HUD en haut à droite:
┌──────────────┐
│ FPS: 25      │
│ Objets: 3    │  ← Voitures, piétons détectés
│ Parking: 1   │  ← Places libres détectées
│ AI: 35.2ms   │  ← Temps d'inférence
│ VIDEO: ✓     │
└──────────────┘
```

## 🔧 Pour activer la segmentation de route

Option 1: **Installer Python 3.11 ou 3.12** (recommandé)
```bash
# Fedora
sudo dnf install python3.11
python3.11 -m venv venv311
source venv311/bin/activate
./setup_ai_models.sh  # Réinstaller avec Python 3.11
```

Option 2: **Désactiver temporairement**
La segmentation est déjà optionnelle. Le dashboard fonctionnera sans elle.

## 🧪 Tester l'IA

```bash
cd pc_dashboard
source venv/bin/activate
./test_ai_inference.py
```

## 🎮 Lancer maintenant

```bash
cd ~/Projet/robocar/RobocarTek3
./run.sh
```

Profitez de la détection d'objets en temps réel! 🚗👤🅿️
