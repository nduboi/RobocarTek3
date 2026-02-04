# 🤖 Intelligence Artificielle - Dashboard Robocar

Ce module ajoute des capacités d'IA au dashboard pour la vision autonome.

## ✨ Fonctionnalités

### 1. Segmentation de Route 🛣️
- **Modèle**: OpenVINO `road-segmentation-adas-0001`
- **Fonction**: Identifie la route praticable en temps réel
- **Overlay**: Zone de route colorée en bleu semi-transparent

### 2. Détection d'Objets 🚗👤
- **Modèle**: YOLOv8n (nano, optimisé pour la vitesse)
- **Classes détectées**:
  - 🚗 Véhicules (voiture, moto, bus, camion) - Orange
  - 👤 Piétons - Rouge
  - 🚦 Feux de signalisation - Cyan
  - 🛑 Panneaux stop - Cyan
- **Informations**: Bounding box + confidence score

### 3. Détection de Places de Parking 🅿️
- **Méthode**: Analyse morphologique + détection de zones libres
- **Critères**:
  - Zone rectangulaire sur la route (ratio 1.2:4.0)
  - Pas de véhicule présent dans la zone
  - Taille entre 2000 et 50000 pixels²
- **Overlay**: Zone verte + marquage "P"

## 📦 Installation

### Prérequis
```bash
# Installer les dépendances système (Fedora/RHEL)
sudo dnf install python3-opencv

# Ou Ubuntu/Debian
sudo apt install python3-opencv
```

### Installation automatique
```bash
cd pc_dashboard
./setup_ai_models.sh
```

Ce script va:
1. Installer `openvino`, `ultralytics`, etc.
2. Télécharger YOLOv8n (~6 MB)
3. Télécharger et convertir road-segmentation-adas-0001 (~25 MB)

### Installation manuelle

```bash
# Installer les packages Python
pip install openvino openvino-dev ultralytics opencv-python numpy

# Télécharger YOLOv8n
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Télécharger le modèle OpenVINO
cd pc_dashboard
omz_downloader --name road-segmentation-adas-0001 --output_dir models
omz_converter --name road-segmentation-adas-0001 --download_dir models --output_dir models
```

## 🚀 Utilisation

### Lancer le dashboard avec IA
```bash
cd pc_dashboard
./run_dashboard.sh  # L'IA est activée par défaut
```

### Lancer sans IA
```bash
python3 main_pc.py --robot-ip 10.84.106.222 --no-ai
```

### Affichage

La fenêtre vidéo affichera:
- 🛣️ **Route segmentée**: Overlay bleu semi-transparent
- 🚗 **Véhicules détectés**: Rectangles orange avec labels
- 👤 **Piétons**: Rectangles rouges
- 🅿️ **Places de parking**: Zones vertes avec "P"
- 📊 **Stats en temps réel**:
  - `Objets: X` - Nombre d'objets détectés
  - `Parking: Y` - Nombre de places disponibles
  - `AI: Z ms` - Temps d'inférence

## ⚙️ Configuration

### Désactiver certaines fonctionnalités

Éditez `main_pc.py`:
```python
self.ai_inference = AIInference(
    enable_segmentation=True,   # False pour désactiver segmentation
    enable_detection=True        # False pour désactiver YOLOv8
)
```

### Ajuster les seuils de détection

Éditez `ai_inference.py`:
```python
# Ligne 104: Confidence YOLOv8
results = self.yolo_model(frame, verbose=False, conf=0.4)  # 0.4 = 40% minimum

# Ligne 198: Taille minimale place de parking
if area < 2000 or area > 50000:  # Ajuster selon besoin
```

## 📊 Performances

### Configuration testée
- **CPU**: Intel i5/i7 ou AMD Ryzen 5/7
- **RAM**: 4 GB minimum
- **Résolution**: 640x480 (dashboard)

### Temps d'inférence typiques
- **Road Segmentation**: ~30-50 ms
- **YOLOv8n**: ~20-40 ms
- **Total pipeline**: ~50-90 ms (~10-20 FPS)

### Optimisations possibles
1. **Utiliser GPU**: Modifier `ie.compile_model(model, "GPU")` si disponible
2. **Réduire résolution**: Traiter frames à 320x240 puis upscale
3. **Skip frames**: Ne traiter qu'1 frame sur 2 ou 3

## 🔧 Dépannage

### "OpenVINO non disponible"
```bash
pip install openvino openvino-dev
```

### "YOLOv8 non disponible"
```bash
pip install ultralytics
```

### "Modèle road-segmentation non trouvé"
```bash
cd pc_dashboard
./setup_ai_models.sh
```

### Inférence trop lente
Essayez:
```python
# Dans ai_inference.py, ligne 54
self.yolo_model = YOLO('yolov8n.pt')  # déjà nano, le plus rapide

# Ou désactiver la segmentation (plus coûteuse)
self.ai_inference = AIInference(enable_segmentation=False)
```

## 📁 Structure des fichiers

```
pc_dashboard/
├── ai_inference.py           # Module principal IA
├── main_pc.py               # Dashboard (intégration IA)
├── setup_ai_models.sh       # Script d'installation
├── AI_README.md            # Ce fichier
└── models/                 # Modèles téléchargés
    └── intel/
        └── road-segmentation-adas-0001/
            └── FP32/
                ├── road-segmentation-adas-0001.xml
                └── road-segmentation-adas-0001.bin
```

## 🎯 Cas d'usage

### 1. Navigation autonome
- Segmentation de route pour path planning
- Détection d'obstacles pour évitement
- Distance estimée via bounding box size

### 2. Parking assisté
- Détection automatique de places libres
- Coloration verte pour aide visuelle
- Future intégration: manœuvre automatique

### 3. Sécurité
- Détection de piétons
- Alerte véhicules proches
- Feux et panneaux de signalisation

## 📚 Références

- **OpenVINO**: https://docs.openvino.ai/
- **YOLOv8**: https://docs.ultralytics.com/
- **Open Model Zoo**: https://github.com/openvinotoolkit/open_model_zoo
- **road-segmentation-adas-0001**: https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/intel/road-segmentation-adas-0001

## 🔮 Améliorations futures

- [ ] Tracking multi-objets (DeepSORT)
- [ ] Distance estimation précise
- [ ] Lane detection (lignes de voie)
- [ ] Traffic sign recognition
- [ ] Intégration avec lidar pour fusion capteurs
- [ ] Mode nuit avec enhancement
