# 🚀 Démarrage Rapide - IA Dashboard

## Installation (une seule fois)

```bash
cd ~/Projet/robocar/RobocarTek3/pc_dashboard

# Lancer l'installation automatique
./setup_ai_models.sh
```

Cela va installer:
- ✅ OpenVINO + openvino-dev
- ✅ Ultralytics (YOLOv8)
- ✅ Modèle road-segmentation-adas-0001
- ✅ Modèle YOLOv8n

**⏱️ Durée**: ~5-10 minutes selon votre connexion internet

## Test rapide

```bash
# Tester les modèles sur une image de test
./test_ai_inference.py
```

Vous devriez voir:
- Image d'entrée simulée
- Image de sortie avec overlays IA
- Statistiques d'inférence

## Lancer le dashboard avec IA

```bash
# Méthode 1: Script run.sh depuis la racine
cd ~/Projet/robocar/RobocarTek3
./run.sh  # L'IA est automatiquement activée

# Méthode 2: Directement
cd pc_dashboard
python3 main_pc.py --robot-ip 10.84.106.222
```

## Ce que vous verrez

### Fenêtre Vidéo
- 🛣️ **Route segmentée**: Bleu transparent sur la zone praticable
- 🚗 **Véhicules**: Rectangles orange + label + confidence
- 👤 **Piétons**: Rectangles rouges
- 🚦 **Signalisation**: Rectangles cyan
- 🅿️ **Parking**: Zones vertes avec "P"

### HUD (en haut à droite)
```
FPS: 30
Objets: 3
Parking: 1
AI: 45.2ms
VIDEO: ✓
```

## Performance attendue

| Composant | Temps | Notes |
|-----------|-------|-------|
| Segmentation route | 30-50ms | OpenVINO CPU |
| Détection YOLOv8n | 20-40ms | Ultralytics |
| **Total** | **50-90ms** | **~10-20 FPS** |

## Désactiver l'IA

Si les performances sont insuffisantes:

```bash
# Option 1: Argument --no-ai
python3 main_pc.py --robot-ip 10.84.106.222 --no-ai

# Option 2: Éditer main_pc.py ligne 35
self.ai_inference = AIInference(
    enable_segmentation=False,  # Désactiver segmentation
    enable_detection=True        # Garder détection
)
```

## Dépannage

### "Module openvino not found"
```bash
pip install openvino openvino-dev
```

### "Module ultralytics not found"
```bash
pip install ultralytics
```

### "Modèle road-segmentation non trouvé"
```bash
cd pc_dashboard
./setup_ai_models.sh
```

### Inférence trop lente (<10 FPS)
1. Désactiver la segmentation (plus lourde)
2. Réduire conf threshold YOLOv8 (ligne 104 ai_inference.py)
3. Traiter 1 frame sur 2 (skip frames)

## Commandes utiles

```bash
# Vérifier installation OpenVINO
python3 -c "from openvino.runtime import Core; print('OpenVINO OK')"

# Vérifier installation YOLOv8
python3 -c "from ultralytics import YOLO; print('YOLOv8 OK')"

# Lister modèles disponibles
ls -lh models/intel/road-segmentation-adas-0001/FP32/

# Taille modèles
du -sh models/
du -sh ~/.cache/torch/hub/checkpoints/yolov8n.pt
```

## Prochaines étapes

Une fois l'IA fonctionnelle, vous pouvez:
1. Ajuster les seuils de détection (ai_inference.py)
2. Modifier les couleurs d'overlay
3. Ajouter d'autres classes YOLOv8
4. Implémenter le tracking multi-objets
5. Fusionner avec les données lidar

📖 Voir [AI_README.md](AI_README.md) pour la documentation complète.
