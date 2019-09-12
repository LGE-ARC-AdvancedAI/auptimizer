from setuptools import setup, find_packages

BASE_URL="https://gitlab.lgsvl.net/Auptimizer/CTE"

setup(
    name='Auptimizer',
    version="1.0",
    author="LG Electronics Inc.",
    author_email="",
    
    license='SPDX-License-Identifier: BSD-3-Clause',
    long_description=open('README.md').read(),

    url=BASE_URL,
    project_urls={
        "Bug Tracker": BASE_URL+"/issues",
        "Documentation": BASE_URL+"/blob/master/README.md",
        "Source Code": BASE_URL,
    },
    # install_requires=open("requirements.txt").readlines(),
    packages=find_packages("src", exclude=["tests"]),
    package_dir={"": "src"}
)
