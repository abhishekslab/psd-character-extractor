#!/usr/bin/env python3
"""Setup script for PSD Character Extractor."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version from package
def get_version():
    """Get version from package __init__.py"""
    version_file = os.path.join("src", "psd_extractor", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="psd-character-extractor",
    version=get_version(),
    author="PSD Character Extractor Contributors",
    author_email="contact@example.com",
    description="Automated character extraction from Photoshop PSD files for VTubers and game development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/psd-character-extractor",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/psd-character-extractor/issues",
        "Documentation": "https://psd-character-extractor.readthedocs.io/",
        "Source Code": "https://github.com/yourusername/psd-character-extractor",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "psd-extract=psd_extractor.cli:extract_command",
            "psd-analyze=psd_extractor.cli:analyze_command",
            "psd-batch=psd_extractor.cli:batch_command",
            "psd-list-expressions=psd_extractor.cli:list_expressions",
            "psd-create-mapping=psd_extractor.cli:create_mapping",
            "psd-character-extractor=psd_extractor.cli:cli",
        ],
    },
    keywords=[
        "psd", "photoshop", "character", "extraction", "vtuber",
        "game-development", "animation", "sprite", "image-processing"
    ],
    include_package_data=True,
    zip_safe=False,
)