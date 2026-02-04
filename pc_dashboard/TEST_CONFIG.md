# Configuration Exemple pour Tests

## Test en Local (Sans Robot)

### Simuler le serveur vidéo (TCP 4488)

```python
# test_video_server.py
import socket
import cv2
import struct
import time

def serve_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 4488))
    sock.listen(1)
    print("Serveur vidéo en attente sur port 4488...")
    
    conn, addr = sock.accept()
    print(f"Client connecté: {addr}")
    
    # Capturer depuis webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Encoder JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        if ret:
            data = buffer.tobytes()
            size = struct.pack(">L", len(data))
            try:
                conn.sendall(size + data)
            except:
                break
        
        time.sleep(0.033)  # ~30 FPS
    
    cap.release()
    conn.close()

if __name__ == "__main__":
    serve_video()
```

### Simuler le serveur lidar (UDP 15975)

```python
# test_lidar_server.py
import socket
import json
import time
import math

def serve_lidar():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Serveur lidar broadcast sur port 15975...")
    
    angle = 0
    while True:
        # Générer points simulés (cercle)
        points = []
        for i in range(360):
            a = (angle + i) % 360
            d = 1000 + 500 * math.sin(math.radians(a * 2))  # Pattern sinusoïdal
            c = 200 + int(50 * math.cos(math.radians(a)))
            points.append({"a": a, "d": d, "c": c})
        
        # Fragmenter
        chunk_size = 50
        total_fragments = (len(points) + chunk_size - 1) // chunk_size
        
        for frag_id in range(total_fragments):
            chunk = points[frag_id * chunk_size:(frag_id + 1) * chunk_size]
            packet = {
                "timestamp": time.time(),
                "fragment": frag_id,
                "total_fragments": total_fragments,
                "points": chunk
            }
            data = json.dumps(packet).encode('utf-8')
            sock.sendto(data, ('127.0.0.1', 15975))
            sock.sendto(data, ('<broadcast>', 15975))
        
        angle = (angle + 5) % 360
        time.sleep(0.1)  # 10 Hz

if __name__ == "__main__":
    serve_lidar()
```

### Tester le controller (UDP 5000)

```python
# test_controller_server.py
import socket
import json

def serve_controller():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 5000))
    print("Serveur controller en attente sur port 5000...")
    
    while True:
        data, addr = sock.recvfrom(4096)
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type')
            
            if msg_type == 'control':
                throttle = message['data']['throttle']
                steering = message['data']['steering']
                print(f"[{addr}] Throttle: {throttle:+.2f}, Steering: {steering:+.2f}")
                
                commands = message.get('commands', [])
                if commands:
                    print(f"  Commands: {commands}")
            
            elif msg_type == 'heartbeat':
                print(f"[{addr}] Heartbeat")
        
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    serve_controller()
```

## Tests Recommandés

### Test 1 : Vidéo seule

Terminal 1:
```bash
python test_video_server.py
```

Terminal 2:
```bash
cd pc_dashboard
python main_pc.py --robot-ip 127.0.0.1
```

### Test 2 : Lidar seul

Terminal 1:
```bash
python test_lidar_server.py
```

Terminal 2:
```bash
cd pc_dashboard
python main_pc.py --robot-ip 127.0.0.1
```

### Test 3 : Contrôle seul

Terminal 1:
```bash
python test_controller_server.py
```

Terminal 2:
```bash
cd pc_dashboard
python main_pc.py --robot-ip 127.0.0.1
# Appuyer sur Z/S/Q/D et observer les logs
```

### Test 4 : Complet

Lancer les 3 serveurs de test dans 3 terminaux séparés, puis le dashboard.

## Configuration Réseau

### Trouver l'IP du robot

```bash
# Sur le robot
hostname -I

# Depuis le PC
nmap -sn 10.84.106.0/24
```

### Tester connectivité

```bash
# Ping
ping 10.84.106.222

# Test ports
nc -zv 10.84.106.222 4488   # Vidéo
nc -zuv 10.84.106.222 15975 # Lidar
nc -zuv 10.84.106.222 5000  # Controller
```

### Capturer trafic

```bash
# Sur le robot
sudo tcpdump -i any port 4488 or port 15975 or port 5000 -w capture.pcap

# Analyser avec Wireshark
wireshark capture.pcap
```

## Variables d'Environnement

Créer un fichier `.env` dans `pc_dashboard/` :

```bash
ROBOT_IP=10.84.106.222
VIDEO_PORT=4488
LIDAR_PORT=15975
CONTROL_PORT=5000
LOG_LEVEL=INFO
```

Puis dans le code :

```python
import os
from dotenv import load_dotenv

load_dotenv()

robot_ip = os.getenv('ROBOT_IP', '10.84.106.222')
```

## Performance Tuning

### Réduire latence vidéo

Dans `video_receiver.py` :
```python
self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
```

### Augmenter buffer UDP

```python
self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
```

### Priorité threads

```python
import os
os.nice(-10)  # Augmenter priorité (nécessite sudo)
```
