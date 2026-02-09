---
marp: true
theme: default
paginate: true
backgroundColor: #1e1e2e
color: #cdd6f4
---

<style>
section {
  font-family: 'Segoe UI', sans-serif;
}
h1 {
  color: #89b4fa;
}
h2 {
  color: #89b4fa;
}
h3 {
  color: #94e2d5;
}
strong {
  color: #a6e3a1;
}
code {
  background: #313244;
  color: #a6e3a1;
}
table th {
  background: #89b4fa;
  color: #1e1e2e;
}
table td {
  background: #313244;
}
blockquote {
  border-left: 4px solid #89b4fa;
  background: rgba(137, 180, 250, 0.1);
  padding: 10px 20px;
  font-style: italic;
}
</style>

# RobocarTek3

## Voiture Autonome pour Parking Hospitalier

**Challenge UTAC - Selection Epitech**

**Axe choisi : INTELLIGENCE ARTIFICIELLE**

---

# Axe IA : Problematique

> **"Comment detecter et se garer dans une place libre, meme sans marquage au sol visible ?"**

Defis des parkings hospitaliers :

- Marquage au sol efface ou absent
- Eclairage variable
- Obstacles dynamiques (pietons, chariots)
- Places non standardisees

---

# Axe IA : Notre Solution

**Fusion Multi-Capteurs**

```
   CAMERA OAK-D          LiDAR LD19
        |                     |
        v                     v
   +---------+          +---------+
   | YOLOv8n |          | Scan    |
   | + Segm. |          | 360°    |
   +---------+          +---------+
        |                     |
        +----------+----------+
                   |
                   v
            +-----------+
            |  FUSION   |
            |  Decision |
            +-----------+
                   |
                   v
          Place libre ? --> Parking
```

---

# Pourquoi pas GPS RTK ?

| Approche classique | Notre approche IA |
|--------------------|-------------------|
| GPS RTK (±2-5m) | LiDAR centimetrique |
| Depend du marquage | Detection de gaps |
| Echoue en interieur | Fonctionne partout |
| Pas de detection obstacles | YOLO temps reel |

**Place de parking = 2m de large** : GPS insuffisant

---

# Le Probleme

> *"Imaginez : vous accompagnez un proche aux urgences. Vous etes stresse, presse, et le parking est bonde..."*

**Notre solution** : Deposez votre passager, la voiture se gare **toute seule**.

---

## Contexte Hospitalier

| Situation | Probleme | Notre Solution |
|-----------|----------|----------------|
| **Urgences** | Patient a deposer vite | Depose + parking auto |
| **Stress** | Pas en etat de chercher | La voiture gere |
| **PMR** | Mobilite reduite | Rapprochement auto |
| **Personnel** | Horaires decales | Gain de temps |

---

## Objectifs Techniques

1. **Naviguer** dans les allees du parking
2. **Detecter** une place libre (LiDAR + Camera)
3. **Executer** une manoeuvre de parking autonome

---

# Architecture Materielle

---

## Vue d'Ensemble

```
              JETSON NANO (4 Go RAM, 128 CUDA)
                         |
         +---------------+---------------+
         |               |               |
      OAK-D           LD19            VESC
    Camera 3D      LiDAR 360       Controleur
      Stereo                         Moteur
         |               |               ^
    TCP:4488        UDP:15975       UDP:5000
         |               |               |
         v               v               |
    +------------------------------------+
    |          PC DASHBOARD              |
    |      Inference IA + Decision       |
    +------------------------------------+
```

---

## Composants Cles

| Composant | Role | Specification |
|-----------|------|---------------|
| **Jetson Nano** | Cerveau embarque | GPU Maxwell 128 cores |
| **OAK-D** | Vision stereo | 1280x720, DepthAI |
| **LD19** | Detection 360 | LiDAR, 230400 baud |
| **VESC** | Motricite | Brushless controller |

**Frequence de controle** : 20 Hz

---

# Pipeline de Perception

---

## Camera (OAK-D)

- **YOLOv8n** : detection vehicules, pietons, panneaux
- **Segmentation route** : modele OpenVINO Intel
- **Detection lignes** : Hough Transform
- **Fallback HSV** : si OpenVINO indisponible

---

## LiDAR (LD19)

- **Zones de securite** : scan 360 degres
- **Detection gaps** : places de parking libres
- **Emergency stop** : obstacle < 300mm = arret

```
        0° (AVANT)
           |
270° ------+------ 90°
   GAUCHE  |  DROITE
           |
       180° (ARRIERE)
```

---

## Pipeline IA

```
        Frame 1280x720
              |
    +---------+---------+
    |                   |
    v                   v
 YOLOv8n         Segmentation
  ~30ms           Route ~40ms
    |                   |
    v                   v
+-------------------------------+
|     Fusion + Decision         |
+-------------------------------+
              |
              v
       Commandes moteur
```

---

## Detection Place de Parking

**Methode LiDAR** (fonctionne sans marquage au sol) :

```
Voiture A    |    GAP    |    Voiture B
  < 1500mm   |  > 2500mm |    < 1500mm
           DEBUT       FIN
```

**Validation** : Largeur gap >= 600mm

---

# Machine a Etats

---

## Cycle Autonome

```
IDLE --> CRUISE --> SEARCH_SPOT --> APPROACH
                                       |
                                       v
                               PARK_MANEUVER
                                       |
                                       v
                                   PARKED
```

**EMERGENCY STOP** : Retour IDLE depuis n'importe quel etat

---

## Parametres par Etat

| Etat | Throttle | Steering | Action |
|------|----------|----------|--------|
| CRUISE | 0.15 | PID | Suivi de route |
| SEARCH_SPOT | 0.10 | PID | Recherche place |
| APPROACH | 0.08 | Calcule | Alignement |
| PARK_MANEUVER | Variable | Variable | Manoeuvre |
| PARKED | 0.0 | 0.0 | Termine |

---

# Manoeuvre de Parking

---

## Phase 1 : ALIGN_ALONGSIDE

```
     [Car A]         [Car B]
        |     GAP      |
        |              |
   ════════════►  Robot avance droit
```

**Steering: 0.0** | **Throttle: 0.10** | **Duree: 1.5s**

---

## Phase 2 : TURN_INTO_SPOT

```
     [Car A]         [Car B]
        |              |
        |    ╭──►      |
        |  ╭─╯         |
   ════╭─╯    Robot braque a droite
```

**Steering: 0.9** | **Throttle: 0.08** | **Duree: 2.0s**

---

## Phase 3 : STRAIGHTEN

```
     [Car A]         [Car B]
        |      |       |
        |      |       |
        |      v       |
               Robot redresse
```

**Steering: 0.0** | **Throttle: 0.05** | **Duree: 1.5s**

---

## Tableau Recapitulatif

| Phase | Duree | Steering | Throttle |
|-------|-------|----------|----------|
| ALIGN_ALONGSIDE | 1.5s | 0.0 | 0.10 |
| TURN_INTO_SPOT | 2.0s | 0.9 | 0.08 |
| STRAIGHTEN | 1.5s | 0.0 | 0.05 |
| FINAL_ADJUST | 1.0s | 0.0 | 0.0 |

---

# Securite

---

## Protection Multicouche

| Couche | Mecanisme | Effet |
|--------|-----------|-------|
| **LiDAR** | Distance < 300mm | Emergency stop |
| **Watchdog** | Timeout 500ms | Arret auto si perte WiFi |
| **Clavier** | SPACE | Stop immediat |
| **Override** | ZQSD | Manuel prioritaire |

---

## Pourquoi pas GPS RTK ?

| Critere | GPS RTK | Notre approche |
|---------|---------|----------------|
| Precision | ±2-5m | **Centimetrique** |
| Indoor/couvert | Non | **Oui** |
| Cout | 500-2000 EUR | Inclus |
| Detection obstacles | Non | **Oui** |

---

# Demo

---

## Ce que vous verrez

1. **Dashboard temps reel**
   - Flux video + overlays YOLO
   - Masque segmentation route
   - Vue LiDAR 360 degres

2. **Mode manuel** : ZQSD

3. **Mode autonome** : Touche 'A'

---

## Statistiques Projet

| Metrique | Valeur |
|----------|--------|
| **Lignes de code** | ~2,900 |
| **Modules autonomes** | 4 |
| **Modeles IA** | 2 |
| **Threads** | 4 |
| **Latence totale** | 100-150ms |

---

# Points Forts

---

## Differenciateurs

| Innovation | Description |
|------------|-------------|
| **Parking complet** | Pas juste lane-keeping |
| **LiDAR-first** | Fonctionne sans marquage |
| **Fallback HSV** | Toujours operationnel |
| **Modulaire** | Tests independants |
| **Dashboard pro** | Debug + demo |

---

# Merci !

## Questions ?

**RobocarTek3** - Challenge UTAC
