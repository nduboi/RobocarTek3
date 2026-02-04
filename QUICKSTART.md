# 🚀 Guide de Démarrage Rapide - RobocarTek3

## Installation en 5 minutes

### 1️⃣ Cloner le projet

```bash
cd ~/
git clone --recurse-submodules <URL_REPO> RobocarTek3
cd RobocarTek3
```

### 2️⃣ Vérifier le système (optionnel)

```bash
chmod +x pre_install_check.sh
./pre_install_check.sh
```

### 3️⃣ Installer

```bash
chmod +x install_all.sh
sudo ./install_all.sh
```

⏱️ Durée : 5-10 minutes

### 4️⃣ Vérifier l'installation

```bash
chmod +x check_health.sh
./check_health.sh
```

### 5️⃣ Activer les services

```bash
chmod +x manage_services.sh
sudo systemctl enable robocar-controller robocar-camera robocar-lidar
sudo systemctl start robocar-controller robocar-camera robocar-lidar
```

### 6️⃣ Vérifier que tout fonctionne

```bash
./manage_services.sh status
```

## ✅ C'est prêt !

Votre robot est maintenant configuré pour démarrer automatiquement au boot.

## 📋 Commandes utiles

```bash
# Démarrer/Arrêter
./manage_services.sh start
./manage_services.sh stop

# Voir les logs
./manage_services.sh logs

# Vérifier la santé
./check_health.sh

# Tester un module
./test_modules.sh controller
```

## ⚙️ Configuration par défaut

| Module | Port | Description |
|--------|------|-------------|
| Controller | 5000 | Commandes de pilotage (UDP) |
| Controller | 5001 | Télémétrie (UDP) |
| Camera | 4488 | Flux vidéo (TCP) |
| Lidar | 15975 | Données lidar (UDP) |

## 🆘 Problème ?

Consultez [DEPLOYMENT.md](DEPLOYMENT.md) pour le guide complet.

## 🔧 Personnalisation

Modifiez les services après installation :

```bash
sudo nano /etc/systemd/system/robocar-controller.service
sudo systemctl daemon-reload
sudo systemctl restart robocar-controller
```

---

**Prochaines étapes** : Lisez [DEPLOYMENT.md](DEPLOYMENT.md) et [README.md](README.md)
