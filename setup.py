#!/usr/bin/env python


"""The setup script"""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

with open("requirements.txt") as req:
    requirements = req.split()

with open("requirements_dev.txt") as dev_req:
    dev_requirements = dev_req.split()

setup(
    author="Shiladitya Bose",
    author_email='shiladitya.31.z@gmail.com',
    maintainer="Shiladitya Bose",
    maintainer_email="shiladitya.31.z@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Wandern is a small database migration tool for python.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords=["wandern", "migration"],
    name="wandern",
    packages=find_packages(include=["wandern", "wandern.*"]),
    test_suite="tests",
    tests_require=dev_requirements,
    url="https://github.com/s-bose/wandern",
    version="0.0.1",
    zip_safe=False,
)
