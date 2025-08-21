"""
PyScheduler - Setup Script
===========================

Professional setup script for PyScheduler.
"""

from setuptools import setup, find_packages
from pathlib import Path
import re

# Lire le README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

def get_version():
    """Extrait la version depuis __init__.py"""
    init_file = this_directory / "pyscheduler" / "__init__.py"
    content = init_file.read_text(encoding='utf-8')
    
    version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if version_match:
        return version_match.group(1)
    
    raise RuntimeError("Version non trouvée dans __init__.py")

# Lire les dépendances optionnelles
def get_requirements(filename):
    """Lit les requirements depuis un fichier"""
    requirements_file = this_directory / filename
    if requirements_file.exists():
        return [
            line.strip() 
            for line in requirements_file.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')
        ]
    return []

setup(
    name="pyscheduler",
    version=get_version(),
    author="Fox",
    author_email="donfackarthur750@gmail.com",
    description="A powerful yet simple Python task scheduler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tiger-Foxx/PyScheduler",
    
    # Packages
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "scripts.*"]),
    
    # Classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8", 
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Intended Audience :: System Administrators",
        "Environment :: Console",
        "Framework :: AsyncIO",
    ],
    
    # Requirements
    python_requires=">=3.7",
    install_requires=[],  # Zero dependencies par défaut !
    
    # Optional dependencies
    extras_require={
        "full": [
            "pyyaml>=5.1.0",
            "pytz>=2021.1", 
            "croniter>=1.0.0"
        ],
        "yaml": ["pyyaml>=5.1.0"],
        "timezone": ["pytz>=2021.1"],
        "cron": ["croniter>=1.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "build>=0.8.0",
            "twine>=4.0.0"
        ]
    },
    
    # Métadonnées
    project_urls={
        "Homepage": "https://github.com/Tiger-Foxx/PyScheduler",
        "Documentation": "https://github.com/Tiger-Foxx/PyScheduler/blob/main/docs/",
        "Repository": "https://github.com/Tiger-Foxx/PyScheduler",
        "Bug Reports": "https://github.com/Tiger-Foxx/PyScheduler/issues",
        "Changelog": "https://github.com/Tiger-Foxx/PyScheduler/blob/main/docs/changelog.md",
        "Examples": "https://github.com/Tiger-Foxx/PyScheduler/tree/main/examples"
    },
    
    keywords=[
        "scheduler", "task", "cron", "async", "threading", "automation", 
        "jobs", "background", "periodic", "interval", "daemon", "service"
    ],
    
    # Package data
    include_package_data=True,
    zip_safe=False,
    
    # Entry points (CLI vient plus tard)
    # entry_points={
    #     "console_scripts": [
    #         "pyscheduler=pyscheduler.cli.main:main",
    #     ],
    # },
)