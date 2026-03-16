"""Vercel giriş noktası."""
import sys
import os

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.dirname(__file__))

from backend.main import app  # noqa: F401
