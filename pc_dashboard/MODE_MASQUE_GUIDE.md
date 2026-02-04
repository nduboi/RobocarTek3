# 🎭 Mode Masque & Détection de Parking Améliorée

## Nouvelles fonctionnalités ajoutées

### 1. Mode Masque (Touche M)

Appuyez sur **M** pour basculer entre:
- **Mode Normal**: Overlay des détections sur la vidéo
- **Mode Masque**: Affichage uniquement des zones détectées sur fond noir

#### Mode Masque - Affichage
- 🟦 **Route**: Bleu/cyan (si segmentation active)
- 🟧 **Véhicules**: Orange vif (rempli)
- 🟥 **Piétons**: Rouge (rempli)
- 🟨 **Signalisation**: Cyan (rempli)
- 🟩 **Places de parking**: Vert brillant avec "P" géant
- ⬜ **Bordures**: Blanches pour tous les objets

#### Utilisation
```
Pendant l'exécution du dashboard:
- Appuyez sur M → Active le mode masque
- Appuyez sur M → Retour au mode normal
```

Le message apparaît en haut: `MODE MASQUE (M pour quitter)`

### 2. Détection de Parking Améliorée

#### Anciennes limites
- ❌ Détection basée uniquement sur la segmentation de route
- ❌ Dépendait du modèle OpenVINO (pas disponible)
- ❌ Taux de faux positifs élevé

#### Nouvelles capacités ✅

**Méthode 1: Détection de lignes de marquage**
- Analyse la zone au sol (60-100% de la hauteur d'image)
- Détecte les lignes de marquage verticales (Canny + HoughLinesP)
- Identifie les paires de lignes délimitant une place (80-200 pixels)
- Vérifie qu'aucun véhicule n'occupe la zone

**Méthode 2: Analyse de zones vides (fallback)**
- Seuillage adaptatif pour détecter les marquages au sol
- Recherche de contours rectangulaires (3000-30000 px²)
- Ratio aspect compatible parking (0.5:2.5)
- Validation absence de véhicule

#### Paramètres ajustables

Dans `ai_inference.py`, ligne ~280:
```python
# Zone d'analyse
roi_y_start = int(h * 0.6)  # 60% de l'image (ajuster 0.5-0.8)

# Largeur de place
if 80 < width < 200:  # pixels (ajuster selon caméra)

# Taille contours
if 3000 < area < 30000:  # pixels² (ajuster sensibilité)
```

## 🎮 Commandes complètes

### Contrôle véhicule
- `Z/S` - Throttle avant/arrière
- `Q/D` - Direction gauche/droite
- `X` - Position neutre
- `ESPACE` - Arrêt d'urgence

### Fonctions
- `K` - Klaxon
- `1-4` - Sons (Epitech, Satelisation, Peter, Polizia)
- `+/-` - Ajuster vitesse max

### Interface
- `M` - **Toggle mode masque** 🎭
- `H` - Afficher/masquer aide
- `ESC` - Quitter

## 📊 HUD

### Mode Normal
```
┌──────────────┐
│ FPS: 25      │
│ Objets: 3    │  ← Voitures + piétons détectés
│ Parking: 2   │  ← Places libres trouvées
│ AI: 45.2ms   │  ← Temps inférence
│ VIDEO: ✓     │
└──────────────┘
```

### Mode Masque
- Texte blanc en haut: `MODE MASQUE (M pour quitter)`
- Fond noir avec zones colorées uniquement
- Labels blancs sur les objets
- Meilleure visibilité des détections

## 🔍 Conseils d'utilisation

### Pour améliorer la détection de parking

1. **Conditions d'éclairage**
   - Meilleure détection en journée
   - Marquages blancs bien visibles

2. **Distance idéale**
   - 3-10 mètres des places
   - Angle légèrement plongeant

3. **Marquages requis**
   - Lignes verticales blanches/jaunes
   - Contraste avec le sol

4. **Utiliser le mode masque**
   - Appuyez sur M pour voir ce que l'IA détecte vraiment
   - Les zones vertes = places trouvées
   - Ajustez votre position si rien n'apparaît

### Débogage

Si les places ne sont pas détectées:

1. **Vérifier avec mode masque (M)**
   - Si rien en vert → Pas de marquages détectés
   - Si orange/rouge → Véhicules bloquent la zone

2. **Ajuster paramètres**
   ```python
   # ai_inference.py ligne 282
   roi_y_start = int(h * 0.5)  # Plus haut = zone plus grande
   
   # ligne 304
   if 60 < width < 250:  # Élargir plage de détection
   ```

3. **Méthode manuelle**
   - Les véhicules détectés excluent leurs zones
   - Cherchez les espaces vides entre véhicules oranges

## 🚀 Lancer

```bash
cd ~/Projet/robocar/RobocarTek3
./run.sh
```

Pendant l'exécution:
1. Vérifiez les détections normales
2. Appuyez sur **M** pour le mode masque
3. Observez les zones vertes (parking)
4. Appuyez sur **M** pour revenir au mode normal

Profitez! 🎭🅿️
