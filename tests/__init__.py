"""
PyScheduler - Package de Tests
==============================

Package contenant tous les tests pour PyScheduler.
"""

# Imports pour faciliter les tests
from .smoke_test import smoke_test
from .quick_test import main as quick_test

__all__ = ['smoke_test', 'quick_test']