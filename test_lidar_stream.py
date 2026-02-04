#!/usr/bin/env python3
"""
Script simple pour recevoir et afficher le flux lidar depuis la Jetson.
Utilisation: python3 test_lidar_stream.py [jetson_ip]
"""

import socket
import json
import sys
import time

def stream_lidar(jetson_ip="10.84.106.222", port=15975):
    """
    Reçoit et affiche le flux lidar depuis la Jetson.
    """
    print(f"🔍 Connexion au serveur lidar {jetson_ip}:{port}...")
    
    # Créer socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(5.0)
    
    print(f"📡 Écoute sur 0.0.0.0:{port}")
    
    # S'enregistrer auprès du serveur
    try:
        sock.sendto(b"REGISTER", (jetson_ip, port))
        print(f"✅ Enregistré auprès de {jetson_ip}:{port}")
    except Exception as e:
        print(f"❌ Erreur enregistrement: {e}")
        return
    
    print("\n⏳ En attente de données... (Ctrl+C pour quitter)\n")
    
    packet_count = 0
    total_points = 0
    last_register = time.time()
    
    try:
        while True:
            try:
                # Renvoyer l'enregistrement tous les 2 secondes
                if time.time() - last_register > 2.0:
                    sock.sendto(b"REGISTER", (jetson_ip, port))
                    print("📤 Renvoi enregistrement...", flush=True)
                    last_register = time.time()
                data, addr = sock.recvfrom(65535)
                packet_count += 1
                
                # Parser JSON
                try:
                    packet = json.loads(data.decode('utf-8'))
                    
                    fragment = packet.get('fragment', 0)
                    total_fragments = packet.get('total_fragments', 1)
                    points = packet.get('points', [])
                    total_points += len(points)
                    
                    print(f"📦 Paquet #{packet_count} de {addr}: "
                          f"Fragment {fragment}/{total_fragments}, "
                          f"{len(points)} points (total: {total_points})")
                    
                    # Afficher un aperçu des points
                    if points:
                        print(f"   Exemples: ", end="")
                        for pt in points[:3]:
                            angle = pt.get('a', 0)
                            dist = pt.get('d', 0)
                            conf = pt.get('c', 0)
                            print(f"(a:{angle:.1f}° d:{dist}mm c:{conf}) ", end="")
                        print()
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur parsing JSON: {e}")
                    print(f"   Données reçues: {data[:100]}")
                
            except socket.timeout:
                print("⏱️  Timeout - en attente de données...")
                
    except KeyboardInterrupt:
        print(f"\n\n✅ Arrêt")
    finally:
        sock.close()
        print(f"\n📊 Résumé: {packet_count} paquets, {total_points} points reçus")

if __name__ == "__main__":
    jetson_ip = sys.argv[1] if len(sys.argv) > 1 else "10.84.106.222"
    stream_lidar(jetson_ip)
