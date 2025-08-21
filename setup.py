"""
PyScheduler - Setup Script
===========================

Script d'installation pour PyScheduler.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lire le README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Lire la version depuis __init__.py
def get_version():
    """Extrait la version depuis __init__.py"""
    init_file = this_directory / "pyscheduler" / "__init__.py"
    content = init_file.read_text(encoding='utf-8')
    
    for line in content.splitlines():
        if line.startswith('__version__'):
            return line.split('"')[1]
    
    raise RuntimeError("Version non trouvée dans __init__.py")

setup(
    name="pyscheduler",
    version=get_version(),
    author="Fox",
    author_email="donfackarthur750@gmail.com",
    description="A powerful yet simple Python task scheduler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tiger-Foxx/PyScheduler",
    
    packages=find_packages(),
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    
    # Dépendances optionnelles mais recommandées
    install_requires=[],  # Aucune dépendance obligatoire !
    
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
            "mypy>=1.0.0"
        ]
    },
    
    # Points d'entrée pour CLI (futur)
    entry_points={
        "console_scripts": [
            "pyscheduler=pyscheduler.cli.main:main",
        ],
    },
    
    # Métadonnées supplémentaires
    project_urls={
        "Bug Reports": "https://github.com/Tiger-Foxx/PyScheduler/issues",
        "Source": "https://github.com/Tiger-Foxx/PyScheduler",
        "Documentation": "https://pyscheduler.readthedocs.io/",
    },
    
    keywords="scheduler, task, cron, async, threading, automation, jobs",
    
    # Inclure les fichiers supplémentaires
    include_package_data=True,
    zip_safe=False,
)