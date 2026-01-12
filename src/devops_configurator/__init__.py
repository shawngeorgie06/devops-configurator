"""
DevOps Pipeline Configurator

Generate production-ready CI/CD configurations from plain English descriptions.
"""

__version__ = "1.0.0"
__author__ = "Georg"

from .parser import RequirementsParser, ProjectRequirements, parse_requirements
from .generators import ConfigGenerator

__all__ = [
    "RequirementsParser",
    "ProjectRequirements",
    "parse_requirements",
    "ConfigGenerator",
    "__version__",
]
