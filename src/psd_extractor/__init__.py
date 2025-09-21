"""
PSD Character Extractor

Automated character extraction from Photoshop PSD files for VTubers,
game development, and animation workflows.
"""

__version__ = "0.1.0"
__author__ = "PSD Character Extractor Contributors"
__email__ = "contact@example.com"

from .extractor import CharacterExtractor
from .analyzer import PSDAnalyzer
from .optimizer import ImageOptimizer
from .batch import BatchProcessor

__all__ = [
    "CharacterExtractor",
    "PSDAnalyzer",
    "ImageOptimizer",
    "BatchProcessor",
]