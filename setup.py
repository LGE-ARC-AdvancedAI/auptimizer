from setuptools import setup, find_packages

BASE_URL="https://github.com/LGE-ARC-AdvancedAI/auptimizer"

setup(
    name='Auptimizer',
    version="1.0.1",
    author="LG Electronics Inc.",
    author_email="auptimizer@lge.com",
    
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
    package_dir={"": "src"}
)
