#!/usr/bin/env python3
"""
Script de test simple pour écouter sur le port UDP 15975
et afficher les paquets qui arrivent en temps réel.
"""

import socket
import sys

def listen_udp(port=15975, timeout=60):
    """
    Écoute sur le port UDP et affiche les paquets.
    
    Args:
        port: Port d'écoute
        timeout: Délai d'attente en secondes
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(timeout)
    
    print(f"🔍 En écoute sur 0.0.0.0:{port} (timeout: {timeout}s)...")
    print(f"⏳ En attente de paquets UDP...")
    print("-" * 60)
    
    packet_count = 0
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(65535)
                packet_count += 1
                
                print(f"\n✅ PAQUET #{packet_count} reçu de {addr}")
                print(f"   Taille: {len(data)} bytes")
                
                # Afficher les premiers 200 caractères
                try:
                    text = data.decode('utf-8')
                    preview = text[:200]
                    print(f"   Contenu: {preview}{'...' if len(text) > 200 else ''}")
                except:
                    print(f"   Contenu (hex): {data[:50].hex()}...")
                    
            except socket.timeout:
                if packet_count == 0:
                    print(f"\n❌ TIMEOUT - Aucun paquet reçu après {timeout}s")
                    print("\n📋 DIAGNOSTIQUE:")
                    print("  1. Vérifier que le service lidar est lancé sur la Jetson:")
                    print("     ssh jetson 'systemctl status robocar-lidar'")
                    print("  2. Vérifier l'IP de destination du lidar:")
                    print("     ssh jetson 'cat lidar/config.yaml | grep ip'")
                    print("  3. Vérifier que les paquets UDP partent bien:")
                    print("     ssh jetson 'netstat -uln | grep 15975'")
                else:
                    print(f"\n✅ {packet_count} paquets reçus avec succès!")
                break
                
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Arrêt")
    finally:
        sock.close()
        print(f"\nRésumé: {packet_count} paquets lidar reçus")

if __name__ == "__main__":
    listen_udp()
