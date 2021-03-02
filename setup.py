# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
from setuptools import setup, find_packages

BASE_URL="https://github.com/LGE-ARC-AdvancedAI/auptimizer"

CONSOLE_SCRIPTS = []
CONSOLE_SCRIPTS.append('dashboard = aup.dashboard.dashboard:main')

def find_version():
    # based on https://packaging.python.org/guides/single-sourcing-package-version/
    # find version number
    import os
    import re
    file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src", "aup", "__init__.py")
    with open(file, 'r') as fp:
        content = fp.read()
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)
    else:
        raise RuntimeError("Failed to find version in __init__.py")


setup(
    name='Auptimizer',
    version=find_version(),
    author="LG Electronics Inc.",
    author_email="auptimizer@lge.com",
    scripts=['src/aup/profiler/profiler.sh', 'src/aup/profiler/statscript.sh'],
    license='SPDX-License-Identifier: GPL-3.0-or-later',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url=BASE_URL,
    project_urls={
        "Bug Tracker": BASE_URL+"/issues",
        "Documentation": "https://lge-arc-advancedai.github.io/auptimizer/",
        "Source Code": BASE_URL,
    },
    # install_requires=open("requirements.txt").readlines(),
    packages=find_packages("src", exclude=["tests"]),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': CONSOLE_SCRIPTS,
    },
    zip_safe=False,
    include_package_data=True
)
