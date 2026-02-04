#!/usr/bin/env python3
"""
Application radar Pygame pour visualiser le LD19 en temps réel.
REFACTORISÉE: UDP Server (écoute) au lieu de Broadcast.
"""

import sys
import serial
import pygame
import math
import toml
from struct import unpack
from collections import deque
import time
import socket
import json

CrcTable = [
    0x00, 0x4d, 0x9a, 0xd7, 0x79, 0x34, 0xe3, 0xae, 0xf2, 0xbf, 0x68, 0x25, 0x8b, 0xc6, 0x11, 0x5c,
    0xa9, 0xe4, 0x33, 0x7e, 0xd0, 0x9d, 0x4a, 0x07, 0x5b, 0x16, 0xc1, 0x8c, 0x22, 0x6f, 0xb8, 0xf5,
    0x1f, 0x52, 0x85, 0xc8, 0x66, 0x2b, 0xfc, 0xb1, 0xed, 0xa0, 0x77, 0x3a, 0x94, 0xd9, 0x0e, 0x43,
    0xb6, 0xfb, 0x2c, 0x61, 0xcf, 0x82, 0x55, 0x18, 0x44, 0x09, 0xde, 0x93, 0x3d, 0x70, 0xa7, 0xea,
    0x3e, 0x73, 0xa4, 0xe9, 0x47, 0x0a, 0xdd, 0x90, 0xcc, 0x81, 0x56, 0x1b, 0xb5, 0xf8, 0x2f, 0x62,
    0x97, 0xda, 0x0d, 0x40, 0xee, 0xa3, 0x74, 0x39, 0x65, 0x28, 0xff, 0xb2, 0x1c, 0x51, 0x86, 0xcb,
    0x21, 0x6c, 0xbb, 0xf6, 0x58, 0x15, 0xc2, 0x8f, 0xd3, 0x9e, 0x49, 0x04, 0xaa, 0xe7, 0x30, 0x7d,
    0x88, 0xc5, 0x12, 0x5f, 0xf1, 0xbc, 0x6b, 0x26, 0x7a, 0x37, 0xe0, 0xad, 0x03, 0x4e, 0x99, 0xd4,
    0x7c, 0x31, 0xe6, 0xab, 0x05, 0x48, 0x9f, 0xd2, 0x8e, 0xc3, 0x14, 0x59, 0xf7, 0xba, 0x6d, 0x20,
    0xd5, 0x98, 0x4f, 0x02, 0xac, 0xe1, 0x36, 0x7b, 0x27, 0x6a, 0xbd, 0xf0, 0x5e, 0x13, 0xc4, 0x89,
    0x63, 0x2e, 0xf9, 0xb4, 0x1a, 0x57, 0x80, 0xcd, 0x91, 0xdc, 0x0b, 0x46, 0xe8, 0xa5, 0x72, 0x3f,
    0xca, 0x87, 0x50, 0x1d, 0xb3, 0xfe, 0x29, 0x64, 0x38, 0x75, 0xa2, 0xef, 0x41, 0x0c, 0xdb, 0x96,
    0x42, 0x0f, 0xd8, 0x95, 0x3b, 0x76, 0xa1, 0xec, 0xb0, 0xfd, 0x2a, 0x67, 0xc9, 0x84, 0x53, 0x1e,
    0xeb, 0xa6, 0x71, 0x3c, 0x92, 0xdf, 0x08, 0x45, 0x19, 0x54, 0x83, 0xce, 0x60, 0x2d, 0xfa, 0xb7,
    0x5d, 0x10, 0xc7, 0x8a, 0x24, 0x69, 0xbe, 0xf3, 0xaf, 0xe2, 0x35, 0x78, 0xd6, 0x9b, 0x4c, 0x01,
    0xf4, 0xb9, 0x6e, 0x23, 0x8d, 0xc0, 0x17, 0x5a, 0x06, 0x4b, 0x9c, 0xd1, 0x7f, 0x32, 0xe5, 0xa8
]

PKG_HEADER = 0x54
PKG_VER_LEN = 0x2C
POINTS_PER_PACK = 12
PACKET_SIZE = 47

class LidarRadar:
    def __init__(self, config_file="radar_config.toml"):
        try:
            with open(config_file, 'r') as f:
                self.config = toml.load(f)
        except FileNotFoundError:
            print(f"Fichier de configuration {config_file} non trouvé. Utilisation des valeurs par défaut.")
            self.config = {
                'serial': {'port': '/dev/ttyUSB0', 'baudrate': 230400},
                'display': {'width': 800, 'height': 800, 'fps': 30},
                'radar': {'max_distance': 12000, 'min_distance': 30, 'noise_filter': True, 'min_confidence': 50}
            }

        self.serial_port = self.config['serial']['port']
        self.baudrate = self.config['serial']['baudrate']

        self.width = self.config['display']['width']
        self.height = self.config['display']['height']
        self.fps = self.config['display']['fps']

        self.max_distance = self.config['radar']['max_distance']
        self.min_distance = self.config['radar']['min_distance']
        self.noise_filter = self.config['radar']['noise_filter']
        self.min_confidence = self.config['radar']['min_confidence']

        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.points_history = []
        self.max_history_frames = 5
        self.current_points = set()

        if (not sys.argv.__contains__("--no-window")):
            self.isWindow = True
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("LD19 Radar View")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 24)

            self.BLACK = (0, 0, 0)
            self.WHITE = (255, 255, 255)
            self.GREEN = (0, 255, 0)
            self.RED = (255, 0, 0)
            self.BLUE = (0, 0, 255)
            self.YELLOW = (255, 255, 0)
        else:
            self.isWindow = False

        # UDP Server Mode (refactorisé)
        if (sys.argv.__contains__("-u")):
            self.enableUDP = True
            self.udp_port = 15975
            
            # Parser custom port si spécifié
            if (sys.argv.__contains__("--port")):
                try:
                    port_idx = sys.argv.index("--port") + 1
                    if port_idx < len(sys.argv):
                        self.udp_port = int(sys.argv[port_idx])
                except (ValueError, IndexError):
                    pass
            
            # Créer socket serveur UDP (écoute)
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            self.udp_socket.bind(('0.0.0.0', self.udp_port))
            self.udp_socket.setblocking(False)  # Non-bloquant
            
            self.last_client_addr = None
            print(f"UDP Server listening on 0.0.0.0:{self.udp_port}", flush=True)
        else:
            self.enableUDP = False

        self.ser = None
        self.last_data_time = 0
        self.data_timeout = 2.0
        self.connection_start_time = 0
        self.connect_serial()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(
                self.serial_port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            try:
                self.ser.write(b'')
                print(f"Connecté au port {self.serial_port} à {self.baudrate} bps")
            except:
                self.ser.close()
                self.ser = None
                print(f"Erreur: Port {self.serial_port} n'est pas accessible. Vérifiez que le lidar est connecté.")
        except serial.SerialException as e:
            if "Permission denied" in str(e):
                print(f"Erreur: Permission refusée sur {self.serial_port}. Exécutez: sudo usermod -a -G dialout $USER")
            elif "No such file" in str(e):
                print(f"Erreur: Port {self.serial_port} n'existe pas. Vérifiez que le lidar est connecté.")
            else:
                print(f"Erreur de connexion série: {e}")
            self.ser = None
        except Exception as e:
            print(f"Erreur inattendue lors de la connexion série: {e}")
            self.ser = None

    def calc_crc8(self, data_bytes):
        crc = 0
        for b in data_bytes:
            crc = CrcTable[(crc ^ b) & 0xff]
        return crc

    def parse_packet(self, pkt):
        if len(pkt) != PACKET_SIZE:
            return None

        calculated_crc = self.calc_crc8(pkt[:-1])
        if calculated_crc != pkt[-1]:
            return None

        header = pkt[0]
        ver_len = pkt[1]
        speed = int.from_bytes(pkt[2:4], 'little')
        start_angle = int.from_bytes(pkt[4:6], 'little') / 100.0

        points = []
        idx = 6
        for i in range(POINTS_PER_PACK):
            dist = int.from_bytes(pkt[idx:idx+2], 'little')
            conf = pkt[idx+2]
            points.append((dist, conf))
            idx += 3

        end_angle = int.from_bytes(pkt[idx:idx+2], 'little') / 100.0
        timestamp = int.from_bytes(pkt[idx+2:idx+4], 'little')

        if start_angle > end_angle:
            end_angle += 360.0

        angle_step = (end_angle - start_angle) / (POINTS_PER_PACK - 1)

        parsed_points = []
        for i, (dist, conf) in enumerate(points):
            angle = start_angle + i * angle_step
            if angle >= 360.0:
                angle -= 360.0
            parsed_points.append((angle, dist, conf))

        return parsed_points

    def read_serial_data(self):
        if not self.ser:
            return

        data_received = False
        try:
            while self.ser.in_waiting > 0:
                b = self.ser.read(1)
                if not b:
                    continue

                if b[0] == PKG_HEADER:
                    b2 = self.ser.read(1)
                    if b2 and b2[0] == PKG_VER_LEN:
                        remaining = self.ser.read(PACKET_SIZE - 2)
                        if len(remaining) == PACKET_SIZE - 2:
                            packet = b + b2 + remaining
                            parsed_points = self.parse_packet(packet)
                            if parsed_points:
                                data_received = True
                                for angle, dist, conf in parsed_points:
                                    if (self.min_distance <= dist <= self.max_distance and
                                        (not self.noise_filter or conf >= self.min_confidence)):
                                        self.current_points.add((angle, dist, conf))

        except Exception as e:
            print(f"Erreur lecture série: {e}")
            self.connect_serial()

        if data_received:
            self.last_data_time = time.time()

    def handle_udp_clients(self):
        """Reçoit les paquets d'enregistrement des clients"""
        if not self.enableUDP:
            return
        
        try:
            # Recevoir paquet d'enregistrement (non-bloquant)
            data, addr = self.udp_socket.recvfrom(1024)
            self.last_client_addr = addr
            print(f"✅ Client enregistré: {addr}", flush=True)
        except BlockingIOError:
            # Aucun paquet reçu, c'est normal
            pass
        except Exception as e:
            print(f"❌ Erreur UDP receptionclients: {e}", flush=True)

    def send_lidar_data_to_client(self):
        """Envoie les données lidar vers le client enregistré"""
        if not self.enableUDP or not self.last_client_addr:
            return

        try:
            points_list = list(self.current_points)

            # Fragmenter les points (50 par paquet)
            POINTS_PER_PACKET = 50
            total_fragments = (len(points_list) + POINTS_PER_PACKET - 1) // POINTS_PER_PACKET
            
            for fragment_idx in range(total_fragments):
                start_idx = fragment_idx * POINTS_PER_PACKET
                end_idx = min(start_idx + POINTS_PER_PACKET, len(points_list))
                chunk = points_list[start_idx:end_idx]
                
                points_data = {
                    "timestamp": time.time(),
                    "fragment": fragment_idx,
                    "total_fragments": total_fragments,
                    "points": [
                        {"a": angle, "d": dist, "c": conf}
                        for angle, dist, conf in chunk
                    ]
                }
                
                json_data = json.dumps(points_data).encode('utf-8')
                self.udp_socket.sendto(json_data, self.last_client_addr)
                
        except Exception as e:
            print(f"Erreur envoi UDP: {e}", flush=True)
            self.last_client_addr = None

    def update_points_history(self):
        """Met à jour l'historique et envoie les données"""
        # Envoyer vers le client UDP s'il existe
        self.send_lidar_data_to_client()

        self.points_history.append(self.current_points.copy())

        if len(self.points_history) > self.max_history_frames:
            self.points_history.pop(0)

        self.current_points.clear()

    @property
    def points(self):
        """Retourne tous les points de l'historique (union de toutes les frames)"""
        if not self.points_history:
            return set()
        return set.union(*self.points_history)

    def polar_to_cartesian(self, angle, distance):
        scale = min(self.center_x, self.center_y) / self.max_distance
        x = self.center_x + distance * scale * math.cos(math.radians(angle - 90))
        y = self.center_y + distance * scale * math.sin(math.radians(angle - 90))
        return int(x), int(y)

    def draw_radar(self):
        self.screen.fill(self.BLACK)

        for r in range(1000, self.max_distance + 1, 1000):
            radius = r * min(self.center_x, self.center_y) / self.max_distance
            pygame.draw.circle(self.screen, self.BLUE, (self.center_x, self.center_y), int(radius), 1)

        for angle in range(0, 360, 30):
            x = self.center_x + min(self.center_x, self.center_y) * math.cos(math.radians(angle - 90))
            y = self.center_y + min(self.center_x, self.center_y) * math.sin(math.radians(angle - 90))
            pygame.draw.line(self.screen, self.BLUE, (self.center_x, self.center_y), (x, y), 1)

        for angle, distance, confidence in self.points:
            x, y = self.polar_to_cartesian(angle, distance)
            if confidence > 200:
                color = self.GREEN
            elif confidence > 100:
                color = self.YELLOW
            else:
                color = self.RED

            pygame.draw.circle(self.screen, color, (x, y), 2)

        status = "CONNECTÉ" if self.ser else "DÉCONNECTÉ"
        udp_status = f"UDP: {self.last_client_addr}" if self.last_client_addr else "UDP: En attente"
        info_text = [
            f"Port: {self.serial_port} ({status})",
            f"Points: {len(self.points)}",
            udp_status,
            f"Filtre bruit: {'ON' if self.noise_filter else 'OFF'}",
            "Appuyez sur F pour toggle filtre, Q pour quitter"
        ]

        for i, text in enumerate(info_text):
            surface = self.font.render(text, True, self.WHITE)
            self.screen.blit(surface, (10, 10 + i * 25))

    def run(self):
        running = True
        while running:
            if (self.isWindow):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            running = False
                        elif event.key == pygame.K_f:
                            self.noise_filter = not self.noise_filter
                            print(f"Filtre bruit: {'ON' if self.noise_filter else 'OFF'}")

            self.read_serial_data()
            self.handle_udp_clients()  # Écouter les enregistrements clients
            self.update_points_history()

            current_time = time.time()
            if current_time - self.last_data_time > self.data_timeout:
                self.points_history.clear()
                self.current_points.clear()

            if (self.isWindow):
                self.draw_radar()
                pygame.display.flip()
                self.clock.tick(self.fps)

    def __del__(self):
        if self.ser:
            print("Closing serial port")
            self.ser.close()
        if (self.isWindow):
            print("Closing app Window")
            pygame.quit()
        if (self.enableUDP):
            print("Closing UDP socket")
            self.udp_socket.close()

if __name__ == '__main__':
    config_file = "radar_config.toml"

    if (sys.argv.__contains__("--help") or sys.argv.__contains__("-h")):
        print("Usage: python3 lidar_radar.py [--no-window] [-u] [--port <udp_port>] [--help]")
        print("  --no-window : Execute without opening a Pygame window")
        print("  -u : Enable UDP Server on port 15975 (responds to clients)")
        print("  --port <udp_port> : Specify UDP port (default: 15975)")
        sys.exit(0)

    radar = LidarRadar(config_file)
    radar.run()
