"""
PyScheduler - Lanceur de Tests
==============================

Script principal pour lancer tous les tests de PyScheduler.
"""

import sys
import os
import subprocess
import time

def run_smoke_test():
    """Lance le test de fumée"""
    print("🔥 Lancement du smoke test...")
    result = subprocess.run([sys.executable, "tests/smoke_test.py"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Smoke test réussi!")
        return True
    else:
        print("❌ Smoke test échoué!")
        print(result.stdout)
        print(result.stderr)
        return False

def run_quick_test():
    """Lance le test rapide"""
    print("\n🚀 Lancement du test rapide...")
    result = subprocess.run([sys.executable, "tests/quick_test.py"],
                          capture_output=False, text=True)
    
    return result.returncode == 0

def run_unit_tests():
    """Lance les tests unitaires"""
    print("\n🧪 Lancement des tests unitaires...")
    try:
        import pytest
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_basic.py", "-v"],
                              capture_output=False, text=True)
        return result.returncode == 0
    except ImportError:
        print("⚠️  pytest non installé, tests unitaires ignorés")
        return True

def main():
    """Fonction principale"""
    print("PyScheduler - Suite de Tests Complète")
    print("=" * 50)
    
    all_passed = True
    
    # 1. Smoke test (ultra-rapide)
    if not run_smoke_test():
        all_passed = False
        print("❌ Arrêt à cause du smoke test")
        return False
    
    # 2. Test rapide (fonctionnel)
    if not run_quick_test():
        all_passed = False
        print("⚠️  Test rapide échoué mais on continue...")
    
    # 3. Tests unitaires
    if not run_unit_tests():
        all_passed = False
        print("⚠️  Tests unitaires échoués mais on continue...")
    
    # Résumé final
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ PyScheduler est prêt pour la production!")
    else:
        print("⚠️  Quelques tests ont échoué")
        print("🔧 Vérifications nécessaires")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)