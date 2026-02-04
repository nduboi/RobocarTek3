#!/usr/bin/env python3
"""
test_road_segmentation.py

Test de la segmentation de route avec fallback HSV.
"""

import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from ai_inference import AIInference


def create_test_road_image():
    """Crée une image de test avec une route"""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 150  # Ciel gris
    
    # Herbe verte en haut
    cv2.rectangle(img, (0, 0), (640, 200), (34, 139, 34), -1)
    
    # Route grise
    cv2.rectangle(img, (50, 200), (590, 480), (100, 100, 100), -1)
    
    # Lignes blanches
    cv2.line(img, (320, 200), (320, 480), (255, 255, 255), 3)
    
    # Marquages
    for y in range(220, 480, 40):
        cv2.line(img, (100, y), (100, y+20), (255, 255, 255), 2)
        cv2.line(img, (580, y), (580, y+20), (255, 255, 255), 2)
    
    # Quelques voitures (rectangles noirs)
    cv2.rectangle(img, (150, 250), (250, 320), (0, 0, 0), -1)
    cv2.rectangle(img, (400, 350), (520, 420), (0, 0, 0), -1)
    
    return img


def main():
    """Test de segmentation"""
    print("🧪 Test Segmentation de Route")
    print("=" * 50)
    
    # Initialiser l'IA
    print("\n📦 Initialisation...")
    ai = AIInference(enable_segmentation=True, enable_detection=False)
    
    # Créer image de test
    print("🖼️ Création image de test...")
    test_img = create_test_road_image()
    cv2.imwrite("road_test_input.jpg", test_img)
    
    # Tester la segmentation
    print("🔍 Test segmentation...")
    mask = ai._segment_road(test_img)
    
    if mask is not None:
        print("✅ Segmentation réussie!")
        print(f"   Mask shape: {mask.shape}")
        print(f"   Pixels route détectés: {np.sum(mask > 0)}")
        
        # Visualiser
        result = test_img.copy()
        result[mask > 0] = result[mask > 0] * 0.6 + np.array([100, 100, 255]) * 0.4
        
        cv2.imwrite("road_test_output.jpg", result.astype(np.uint8))
        print("   Résultat: road_test_output.jpg")
        
        # Afficher
        cv2.imshow("Input", test_img)
        cv2.imshow("Segmentation", mask)
        cv2.imshow("Output", result.astype(np.uint8))
        
        print("\n✅ Test réussi! Appuyez sur une touche...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return 0
    else:
        print("❌ Segmentation échouée")
        return 1


if __name__ == "__main__":
    sys.exit(main())
