#!/usr/bin/env python3
"""Test simple UDP listener sur le port 15975"""
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 15975))
sock.settimeout(30)

print("🔍 En écoute sur 0.0.0.0:15975 (30s)...")

count = 0
try:
    while True:
        data, addr = sock.recvfrom(65535)
        count += 1
        print(f"✅ Paquet #{count} de {addr}: {len(data)} bytes")
        if count == 1:
            try:
                print(f"   Contenu: {data[:100].decode('utf-8', errors='ignore')}")
            except:
                print(f"   Hex: {data[:50].hex()}")
except socket.timeout:
    if count == 0:
        print("❌ TIMEOUT - Aucun paquet reçu")
        print("\n📋 Pour configurer le docker sur la Jetson:")
        print("   1. Docker envoie VERS quelle IP ? (default: localhost, 127.0.0.1, ou broadcast)")
        print("   2. Il faut changer pour envoyer vers votre IP PC")
        print("   3. Ou utiliser le paramètre LIDAR_IP=<votre_ip> au lancement du docker")
    else:
        print(f"\n✅ {count} paquets reçus!")
except KeyboardInterrupt:
    print(f"\n\nRésumé: {count} paquets")
finally:
    sock.close()
