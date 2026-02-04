#!/usr/bin/env python3
"""
test_ai_inference.py

Script de test pour vérifier le bon fonctionnement des modèles IA.
Teste la segmentation, détection et parking sur une image de test.

Usage: 
    source venv/bin/activate  # Activer le venv d'abord
    ./test_ai_inference.py
"""

import cv2
import numpy as np
import sys
import os

# Ajouter le chemin du module
sys.path.insert(0, os.path.dirname(__file__))

from ai_inference import AIInference


def create_test_image():
    """Crée une image de test simulant une route"""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 100  # Fond gris
    
    # Dessiner une route (gris foncé)
    cv2.rectangle(img, (0, 300), (640, 480), (60, 60, 60), -1)
    
    # Ligne blanche centrale
    cv2.line(img, (320, 300), (320, 480), (255, 255, 255), 2)
    
    # Simuler quelques "voitures" (rectangles)
    cv2.rectangle(img, (100, 350), (180, 420), (0, 0, 180), -1)  # Voiture 1
    cv2.rectangle(img, (450, 360), (520, 410), (180, 0, 0), -1)  # Voiture 2
    
    # Zone de parking potentielle (espace vide)
    cv2.rectangle(img, (250, 380), (350, 450), (80, 80, 80), 2)  # Marquage parking
    
    return img


def main():
    """Test des fonctionnalités IA"""
    print("🧪 Test du module AI Inference")
    print("=" * 50)
    
    # Initialiser l'IA
    print("\n📦 Initialisation des modèles...")
    try:
        ai = AIInference(enable_segmentation=True, enable_detection=True)
        print("✅ Modèles chargés avec succès")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\nVeuillez lancer: ./setup_ai_models.sh")
        return 1
    
    # Créer image de test
    print("\n🖼️ Création image de test...")
    test_img = create_test_image()
    cv2.imwrite("test_input.jpg", test_img)
    print("   Sauvegardé: test_input.jpg")
    
    # Traiter l'image
    print("\n🤖 Traitement avec IA...")
    result_img, info = ai.process_frame(test_img)
    
    # Afficher les résultats
    print("\n📊 Résultats:")
    print(f"   • Route détectée: {'✓' if info.get('road_detected') else '✗'}")
    print(f"   • Objets détectés: {len(info.get('objects', []))}")
    print(f"   • Places de parking: {len(info.get('parking_spots', []))}")
    print(f"   • Temps d'inférence: {info.get('inference_time_ms', 0):.1f} ms")
    
    # Détails des objets
    if info.get('objects'):
        print("\n🎯 Objets détectés:")
        for i, obj in enumerate(info['objects'][:5]):
            print(f"   {i+1}. {obj['class_name']} ({obj['confidence']:.2f})")
    
    # Sauvegarder résultat
    cv2.imwrite("test_output.jpg", result_img)
    print(f"\n💾 Résultat sauvegardé: test_output.jpg")
    
    # Afficher les images
    print("\n👁️ Appuyez sur une touche pour voir les résultats...")
    cv2.imshow("Test Input", test_img)
    cv2.imshow("Test Output avec IA", result_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n✅ Test terminé avec succès!")
    
    # Stats finales
    stats = ai.get_stats()
    print(f"\n📈 Statistiques:")
    print(f"   • Segmentation: {'✓' if stats['segmentation_enabled'] else '✗'}")
    print(f"   • Détection: {'✓' if stats['detection_enabled'] else '✗'}")
    print(f"   • FPS estimé: {stats['fps']:.1f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
