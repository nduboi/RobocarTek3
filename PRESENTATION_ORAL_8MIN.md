# 🚗 Présentation Orale RobocarTek3 - 8 Minutes

> **Challenge UTAC - Sélection Epitech**
> Équipe : [À compléter]
> Campus : [À compléter]

---

## 🎯 Axe Choisi : INTELLIGENCE ARTIFICIELLE

### Problématique IA

> **"Comment permettre à un véhicule de détecter et se garer dans une place de parking libre, même sans marquage au sol visible ?"**

Les parkings hospitaliers présentent des défis uniques :
- Marquage au sol souvent effacé ou absent
- Éclairage variable (sous-sols, extérieur)
- Obstacles dynamiques (piétons, chariots)
- Places de tailles non standardisées

### Notre Solution IA : Fusion Multi-Capteurs

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE IA MULTI-CAPTEURS                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CAMERA OAK-D              LiDAR LD19                         │
│   ┌───────────┐             ┌───────────┐                      │
│   │ YOLOv8n   │             │ Scan 360° │                      │
│   │ Véhicules │             │ Distances │                      │
│   │ Piétons   │             │           │                      │
│   └─────┬─────┘             └─────┬─────┘                      │
│         │                         │                             │
│   ┌─────▼─────┐             ┌─────▼─────┐                      │
│   │Segmentation│            │ Détection │                      │
│   │   Route   │             │   Gaps    │                      │
│   │ OpenVINO  │             │ (places)  │                      │
│   └─────┬─────┘             └─────┬─────┘                      │
│         │                         │                             │
│         └───────────┬─────────────┘                            │
│                     ▼                                           │
│            ┌───────────────┐                                   │
│            │    FUSION     │                                   │
│            │  Décision IA  │                                   │
│            └───────┬───────┘                                   │
│                    ▼                                            │
│         Place libre confirmée ?                                 │
│         OUI → Manœuvre parking                                  │
│         NON → Continuer recherche                               │
└─────────────────────────────────────────────────────────────────┘
```

### Pourquoi cette approche ?

| Approche classique | Notre approche IA |
|--------------------|-------------------|
| GPS RTK (±2-5m) | LiDAR centimétrique |
| Dépend du marquage | Détection de gaps physiques |
| Échoue en intérieur | Fonctionne partout |
| Pas de détection obstacles | YOLO temps réel |

---

## 📋 Structure de la Présentation

| Section | Durée | Cumul |
|---------|-------|-------|
| Accroche + Axe IA | 1:00 | 1:00 |
| Architecture matérielle | 1:00 | 2:00 |
| Architecture logicielle | 1:00 | 3:00 |
| Intégration capteurs (LiDAR + Caméra 3D) | 1:30 | 4:30 |
| Focus IA : Problématique & Solution | 1:30 | 6:00 |
| Machine à états autonome | 1:00 | 7:00 |
| Manœuvre de parking | 1:00 | 8:00 |

---

## 1. Accroche (30 sec)

> *"Imaginez : vous accompagnez un proche aux urgences. Vous êtes stressé, pressé, et le parking de l'hôpital est bondé. Avec notre solution, vous déposez votre passager à l'entrée, et la voiture se gare toute seule. Vous pouvez vous concentrer sur l'essentiel : votre proche."*

**Notre objectif** : Concevoir une voiture autonome capable de :
1. **Naviguer** dans les allées d'un parking hospitalier
2. **Détecter** une place de stationnement libre
3. **Exécuter** une manœuvre de parking en bataille de manière autonome

### Pourquoi l'hôpital ?

| Contexte | Problématique | Notre solution |
|----------|---------------|----------------|
| **Urgences** | Patient à déposer rapidement | Dépose à l'entrée, parking automatique |
| **Stress** | Conducteur pas en état de chercher une place | La voiture gère seule |
| **Accessibilité** | Personnes à mobilité réduite | Rapprochement automatique après stationnement |
| **Parking saturé** | Files d'attente, énervement | Optimisation des places disponibles |
| **Personnel soignant** | Horaires décalés, fatigue | Gain de temps et de charge mentale |

---

## 2. Architecture Matérielle (1 min)

### Schéma du Robot

```
                    ┌─────────────────────────────────┐
                    │         JETSON NANO             │
                    │   (4 Go RAM, 128 CUDA cores)    │
                    │         Cerveau embarqué        │
                    └───────────────┬─────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
   ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
   │   OAK-D       │       │   LD19        │       │   VESC        │
   │   Caméra 3D   │       │   LiDAR 360°  │       │   Contrôleur  │
   │   Stéréo      │       │               │       │   Moteur      │
   └───────────────┘       └───────────────┘       └───────────────┘
         │                        │                        ▲
         │ TCP:4488               │ UDP:15975              │ UDP:5000
         │ (vidéo JPEG)           │ (points 360°)          │ (commandes)
         ▼                        ▼                        │
   ┌──────────────────────────────────────────────────────────────┐
   │                    PC STATION SOL                            │
   │              Dashboard + Inférence IA temps réel             │
   └──────────────────────────────────────────────────────────────┘
```

### Composants Clés

| Composant | Spécifications | Rôle |
|-----------|----------------|------|
| **Jetson Nano** | 4 Go RAM, GPU Maxwell 128 cores | Acquisition capteurs, communication |
| **OAK-D** | Stéréo 1280x720, DepthAI SDK | Vision, segmentation route |
| **LD19** | LiDAR 360°, 230400 baud | Détection obstacles, gaps parking |
| **VESC** | Contrôleur brushless | Throttle [-1,1] et Steering [-1,1] |
| **PC** | GPU dédié (optionnel) | IA, décision, dashboard |

**Point clé** : Architecture distribuée → le robot capture, le PC analyse et décide, les commandes reviennent au robot à **20 Hz**.

---

## 3. Architecture Logicielle (1 min 30)

### Communication Multi-Protocoles

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           JETSON NANO                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ camera.service│   │ lidar.service │   │controller.service│          │
│  │   (systemd)  │    │   (systemd)  │    │   (systemd)  │              │
│  └──────┬───────┘    └──────┬───────┘    └──────▲───────┘              │
│         │                   │                   │                       │
└─────────┼───────────────────┼───────────────────┼───────────────────────┘
          │                   │                   │
          │ TCP:4488          │ UDP:15975         │ UDP:5000
          │ [4B taille][JPEG] │ JSON fragments    │ JSON {throttle, steering}
          │                   │                   │
          ▼                   ▼                   │
┌─────────────────────────────────────────────────┴───────────────────────┐
│                           PC DASHBOARD                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ VideoReceiver  │  │ LidarReceiver  │  │ControllerSender│            │
│  │ (Thread 1)     │  │ (Thread 2)     │  │ (Thread 3)     │            │
│  └───────┬────────┘  └───────┬────────┘  └───────▲────────┘            │
│          │                   │                   │                      │
│          ▼                   ▼                   │                      │
│  ┌───────────────────────────────────────────────┴──────────────────┐  │
│  │                      main_pc.py (Thread 4)                       │  │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌───────────────────┐    │  │
│  │  │ AIInference │  │ AutonomousDriver│  │ OpenCV Display    │    │  │
│  │  │ YOLOv8n     │  │ SafetyMonitor   │  │ Vidéo + LiDAR     │    │  │
│  │  │ OpenVINO    │  │ PathFollower    │  │ + Overlays        │    │  │
│  │  │             │  │ ParkingPlanner  │  │                   │    │  │
│  │  └─────────────┘  └─────────────────┘  └───────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Protocoles de Communication

| Canal | Port | Protocole | Direction | Format | Fréquence |
|-------|------|-----------|-----------|--------|-----------|
| Vidéo | 4488 | TCP | Jetson → PC | `[4B size][JPEG]` | ~20-30 FPS |
| LiDAR | 15975 | UDP | Jetson → PC | JSON fragments | ~10 Hz |
| Commandes | 5000 | UDP | PC → Jetson | JSON `{throttle, steering}` | 20 Hz |
| Heartbeat | 5000 | UDP | PC → Jetson | Keep-alive | 5 Hz |

### Sécurités Réseau

- **Watchdog 500ms** : le robot s'arrête automatiquement si perte de signal
- **Thread-safe** : mutex sur toutes les données partagées
- **Graceful shutdown** : envoi de commandes finales avant fermeture

---

## 4. Intégration Capteurs : LiDAR + Caméra 3D (1 min 30)

### LiDAR LD19 - Évitement d'Obstacles

#### Convention Angulaire

```
                    0° (AVANT)
                       │
                       │
        330°───────────┼───────────30°
                       │
                       │
    270° (GAUCHE) ─────┼───── 90° (DROITE)
                       │
                       │
        210°───────────┼───────────150°
                       │
                       │
                   180° (ARRIÈRE)
```

#### Zones de Sécurité Surveillées

| Zone | Plage Angulaire | Rôle |
|------|-----------------|------|
| **Avant** (critique) | [-30°, +30°] | Emergency stop |
| **Droite** | [60°, 120°] | Détection places parking |
| **Gauche** | [240°, 300°] | Évitement latéral |
| **Arrière** | [135°, 225°] | Manœuvres recul |

#### Safety Monitor - Logique de Sécurité

```
Distance obstacle (mm)    Action
─────────────────────────────────────
    < 300 mm         →   EMERGENCY STOP (speed_factor = 0.0)
    300 - 800 mm     →   Ralentissement progressif
    > 800 mm         →   Vitesse normale (speed_factor = 1.0)
```

**Formule** : `speed_factor = (distance - 300) / 500` (clamped [0, 1])

### Caméra OAK-D - Suivi de Trajectoire

#### Pipeline de Segmentation Route

```
Frame 1280x720
      │
      ▼
┌─────────────────┐
│ Resize 512x896  │
└────────┬────────┘
         ▼
┌─────────────────────────────────┐
│ OpenVINO road-segmentation-adas │  ← Modèle Intel optimisé
│         (ou fallback HSV)       │
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Masque binaire (route = blanc)  │
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Extraction ROI (bottom 40%)     │  ← Zone proche = plus pertinente
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Calcul centroïde route          │
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ PID Controller → steering       │
│ Kp=1.5, Ki=0.0, Kd=0.3         │
└─────────────────────────────────┘
```

### Pourquoi PAS de GPS RTK ?

| Critère | GPS RTK | Notre approche LiDAR+Vision |
|---------|---------|----------------------------|
| Précision en parking | ±2-5 mètres | **Centimétrique** |
| Fonctionnement indoor/couvert | ❌ Signal dégradé | ✅ Fonctionne partout |
| Coût | ~500-2000€ | Inclus dans capteurs existants |
| Détection obstacles | ❌ Non | ✅ Oui |

**Conclusion** : Pour un parking de hôpital avec places de ~2m de large, le GPS est insuffisant. Notre approche perception est plus adaptée.

---

## 5. Focus IA : Pipeline d'Inférence (1 min 30)

### 3 Modèles en Cascade

```
              Frame 1280x720
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────────┐
│   YOLOv8n     │       │ Road Segmentation │
│   (~30ms)     │       │     (~40ms)       │
│               │       │                   │
│ • Voitures    │       │ • OpenVINO        │
│ • Piétons     │       │   (primary)       │
│ • Panneaux    │       │                   │
│ • Motos       │       │ • HSV Fallback    │
│               │       │   (si indispo)    │
└───────┬───────┘       └─────────┬─────────┘
        │                         │
        ▼                         ▼
┌───────────────────────────────────────────┐
│           Fusion des résultats            │
│                                           │
│  • Bounding boxes YOLO sur frame          │
│  • Masque route en overlay bleu           │
│  • Vérification places libres             │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
              Décision autonome
```

### Détails des Modèles

| Modèle | Taille | Classes | Seuil | Temps |
|--------|--------|---------|-------|-------|
| **YOLOv8n** | ~6.5 MB | person, car, motorcycle, bus, truck, traffic light, stop sign | 0.4 | ~30ms |
| **road-segmentation-adas-0001** | ~2 MB | route (binaire) | - | ~40ms |
| **Parking Detection** (custom) | - | gaps LiDAR + Hough lines | - | ~10ms |

### Pipeline Total

```
Perception : 50-90ms
     +
Réseau     : ~50ms
     =
─────────────────────
Latence    : 100-150ms  →  10-20 FPS (suffisant à vitesse lente)
```

### Problématique IA Résolue

> **Comment détecter une place de parking sans marquage au sol visible ?**

**Solution** : Détection de "gaps" LiDAR entre véhicules garés

```python
# Algorithme simplifié
1. Scanner le côté droit [60°-120°]
2. Regrouper par bins de 2°
3. Détecter transitions : proche→loin (début gap) / loin→proche (fin gap)
4. Valider si largeur gap ≥ 600mm (place utilisable)
5. Vérifier avec YOLO qu'aucun véhicule n'est dans le gap
```

### Robustesse : Fallback HSV

Si OpenVINO est indisponible :

```python
# Détection asphalte par couleur
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, (0, 0, 40), (180, 50, 120))  # Gris foncé = route
```

---

## 6. Machine à États Autonome (1 min)

### Diagramme d'États

```
                              ┌──────────────────────────────────────┐
                              │                                      │
                              ▼                                      │
                        ┌──────────┐                                 │
           Touche 'A' → │   IDLE   │ ←───────────────────────────────┤
                        └────┬─────┘                                 │
                             │                                       │
                             │ Activation mode autonome              │
                             ▼                                       │
                        ┌──────────┐                                 │
                        │  CRUISE  │ ← Suivi de route (PID)          │
                        │          │   throttle = 0.15               │
                        └────┬─────┘                                 │
                             │                                       │
                             │ Après CRUISE_DURATION secondes        │
                             ▼                                       │
                     ┌──────────────┐                                │
                     │ SEARCH_SPOT  │ ← Scan LiDAR côté droit        │
                     │              │   throttle = 0.10              │
                     └──────┬───────┘                                │
                            │                                        │
                            │ Gap détecté (largeur ≥ 600mm)          │
                            ▼                                        │
                       ┌──────────┐                                  │
                       │ APPROACH │ ← Alignement avec la place       │
                       └────┬─────┘                                  │
                            │                                        │
                            │ Position alignée                       │
                            ▼                                        │
                    ┌───────────────┐                                │
                    │ PARK_MANEUVER │ ← Manœuvre en 5 phases         │
                    │               │   (voir section suivante)      │
                    └───────┬───────┘                                │
                            │                                        │
                            │ Manœuvre terminée                      │
                            ▼                                        │
                       ┌──────────┐                                  │
                       │  PARKED  │ ← Succès ! Moteur coupé          │
                       └──────────┘                                  │
                                                                     │
     ╔═══════════════════════════════════════════════════════════╗   │
     ║  EMERGENCY STOP (SPACE) → Annule tout, retour à IDLE  ────╫───┘
     ╚═══════════════════════════════════════════════════════════╝
```

### Paramètres de Throttle par État

| État | Throttle | Steering | Description |
|------|----------|----------|-------------|
| IDLE | 0.0 | 0.0 | Arrêt complet |
| CRUISE | 0.15 | PID | Suivi de route normal |
| SEARCH_SPOT | 0.10 | PID | Recherche place (plus lent) |
| APPROACH | 0.08 | Calculé | Alignement précis |
| PARK_MANEUVER | Variable | Variable | Voir détail ci-dessous |
| PARKED | 0.0 | 0.0 | Mission accomplie |

### Sécurité Permanente

- **Safety Monitor** actif dans TOUS les états
- **speed_factor** appliqué à tous les throttle
- **Emergency stop** prioritaire sur tout
- **Override clavier** : le manuel a toujours priorité

---

## 7. Manœuvre de Parking - 5 Phases (1 min)

### Séquence Complète

```
    ═══════════════════════════════════════════════════════════════════

    PHASE 1: ALIGN_ALONGSIDE (1.5s)
    ─────────────────────────────────

         ┌─────┐      ┌─────┐
         │ Car │      │ Car │
         │  A  │      │  B  │
         └─────┘      └─────┘
              ↑ GAP ↑

         ══►══►══►══►  Robot avance droit
         Steering: 0.0 | Throttle: 0.10

    ═══════════════════════════════════════════════════════════════════

    PHASE 2: TURN_INTO_SPOT (2.0s)
    ───────────────────────────────

         ┌─────┐      ┌─────┐
         │ Car │      │ Car │
         │  A  │      │  B  │
         └─────┘      └─────┘

                 ╭──→
               ╭─╯
         ════╭─╯   Robot braque à droite
         Steering: 0.9 | Throttle: 0.08

    ═══════════════════════════════════════════════════════════════════

    PHASE 3: STRAIGHTEN (1.5s)
    ─────────────────────────────

         ┌─────┐      ┌─────┐
         │ Car │      │ Car │
         │  A  │      │  B  │
         └─────┘      └─────┘

              │
              │   Robot redresse les roues
              ▼
         Steering: 0.0 | Throttle: 0.05

    ═══════════════════════════════════════════════════════════════════

    PHASE 4: FINAL_ADJUST (1.0s)
    ─────────────────────────────

         ┌─────┐ ┌───┐ ┌─────┐
         │ Car │ │ R │ │ Car │
         │  A  │ │ o │ │  B  │
         └─────┘ │ b │ └─────┘
                 └───┘

         Positionnement final
         Steering: 0.0 | Throttle: 0.0

    ═══════════════════════════════════════════════════════════════════

    PHASE 5: DONE
    ─────────────

         ✅ Manœuvre terminée avec succès
         État → PARKED
```

### Tableau Récapitulatif

| Phase | Durée | Steering | Throttle | Action |
|-------|-------|----------|----------|--------|
| **ALIGN_ALONGSIDE** | 1.5s | 0.0 | 0.10 | Avancer le long de la place |
| **TURN_INTO_SPOT** | 2.0s | 0.9 | 0.08 | Braquer fort à droite |
| **STRAIGHTEN** | 1.5s | 0.0 | 0.05 | Redresser les roues |
| **FINAL_ADJUST** | 1.0s | 0.0 | 0.0 | Positionnement final |
| **DONE** | - | - | - | Terminé |

### Conditions d'Abort (Sécurité)

| Phase | Condition | Action |
|-------|-----------|--------|
| TURN_INTO_SPOT | Obstacle < 600mm devant | STOP immédiat |
| STRAIGHTEN | Obstacle < 400mm devant | STOP immédiat |
| Toutes | Emergency stop (SPACE) | Retour à IDLE |

---

## 8. Démonstration Prévue

### Ce que vous verrez

1. **Dashboard temps réel**
   - Flux vidéo avec overlays YOLO (bounding boxes)
   - Masque de segmentation route (overlay bleu)
   - Visualisation LiDAR 360° (vue du dessus)
   - Indicateurs throttle/steering

2. **Contrôle manuel**
   - ZQSD pour diriger le robot
   - Réactivité du système

3. **Mode autonome**
   - Activation avec touche 'A'
   - Suivi de trajectoire automatique
   - Transition entre états visible à l'écran

4. **Parking automatique**
   - Détection d'une place libre
   - Exécution de la manœuvre complète
   - Arrêt dans la place

---

## 9. Statistiques du Projet

### Code

| Métrique | Valeur |
|----------|--------|
| **Total Python LoC** | ~2,861 lignes |
| **Modules autonomes** | 4 (safety, path, parking, driver) |
| **Modèles IA** | 2 (YOLOv8n, road-segmentation) |
| **Threads** | 4 (vidéo, lidar, commandes, main) |
| **Protocoles** | 2 (TCP, UDP) |

### Architecture

| Composant | Fichier | Lignes |
|-----------|---------|--------|
| Dashboard principal | `main_pc.py` | 609 |
| Inférence IA | `ai_inference.py` | 580 |
| Pilote autonome | `autonomous_driver.py` | 191 |
| Planificateur parking | `parking_planner.py` | 184 |
| Moniteur sécurité | `safety_monitor.py` | 98 |
| Suiveur de chemin | `path_follower.py` | 94 |

---

## 10. Points Forts / Différenciateurs

| Innovation | Description |
|------------|-------------|
| **Parking autonome complet** | Pas seulement du lane-keeping, mais une vraie manœuvre de stationnement |
| **LiDAR-first** | Détection robuste sans dépendre du marquage au sol |
| **Fallback IA** | HSV si OpenVINO indisponible → fonctionne toujours |
| **Architecture modulaire** | Chaque module testable indépendamment |
| **Dashboard pro** | Visualisation temps réel pour debug et démo |
| **Sécurité multicouche** | Watchdog + emergency stop + speed_factor |

---

## 11. Préparation Q&A (4 minutes)

### Questions Probables

| Question | Réponse Suggérée |
|----------|------------------|
| **"Pourquoi pas de GPS RTK ?"** | Précision insuffisante en parking (±2-5m) vs places de 2m. Notre approche LiDAR+Vision offre une précision centimétrique et fonctionne en intérieur/couvert. |
| **"Latence totale du système ?"** | ~100-150ms (50-90ms perception + 50ms réseau). Suffisant car vitesse lente (throttle 0.1-0.15). |
| **"Que se passe-t-il si WiFi coupe ?"** | Watchdog 500ms → le robot s'arrête automatiquement. Sécurité intrinsèque. |
| **"Aspects cybersécurité ?"** | Réseau local isolé, watchdog, emergency stop physique. Pour production : ajouter authentification et chiffrement. |
| **"Simulation utilisée ?"** | Tests sur données réelles, itération rapide sur le robot. Pas de simulateur type Gazebo/CARLA. |
| **"Portage Jetson prévu ?"** | Safety layer à porter sur Jetson pour latence minimale sur l'urgence. Reste de la décision sur PC. |
| **"PID bien tuné ?"** | Valeurs initiales Kp=1.5, Kd=0.3. À affiner expérimentalement lors des tests terrain. |
| **"Comment gérez-vous les piétons ?"** | YOLOv8 détecte les personnes → Safety Monitor peut être étendu pour emergency stop sur détection piéton proche. |

---

## 12. Checklist Matériel pour la Démo

- [ ] Robot complet (châssis + électronique)
- [ ] Jetson Nano avec carte SD flashée
- [ ] Batterie chargée
- [ ] PC portable avec dashboard installé
- [ ] Câble Ethernet (backup si WiFi instable)
- [ ] Routeur WiFi (réseau dédié)
- [ ] Obstacles pour démo (cônes, cartons)
- [ ] Marquage au sol (scotch) pour simuler places de parking

---

## 13. Contacts

| Rôle | Nom | Email |
|------|-----|-------|
| Chef de projet | | |
| Développeur IA | | |
| Développeur embarqué | | |
| Intégrateur système | | |

---

*Document généré le 9 février 2026 pour la sélection Challenge UTAC*
