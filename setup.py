"""
Setup script for VWS CLI.
"""

import os
from pathlib import Path
from typing import List

from setuptools import setup


def _get_dependencies(requirements_file: Path) -> List[str]:
    """
    Return requirements from a requirements file.

    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().strip().split('\n')
    return [line for line in lines if not line.startswith('#')]


INSTALL_REQUIRES = _get_dependencies(
    requirements_file=Path('requirements.txt'),
)

DEV_REQUIRES = _get_dependencies(
    requirements_file=Path('dev-requirements.txt'),
)

PACKAGING_REQUIRES = _get_dependencies(
    requirements_file=Path('packaging-requirements.txt'),
)

setup(
    use_scm_version={
        'write_to': 'src/vws_cli/_setuptools_scm_version.py',
        'fallback_version': os.environ.get('_SETUPTOOLS_SCM_VWS_CLI_FALLBACK'),
    },
    setup_requires=['setuptools_scm'],
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
        'packaging': PACKAGING_REQUIRES,
    },
)
