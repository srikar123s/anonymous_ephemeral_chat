#!/usr/bin/env python3
"""
Setup script for Anonymous & Ephemeral Chat Application
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="anonymous-ephemeral-chat",
    version="1.0.0",
    author="Privacy Research Team",
    author_email="privacy@example.com",
    description="Anonymous & Ephemeral Chat Application - P2P secure messaging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/privacy-research/anonymous-ephemeral-chat",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Security :: Cryptography",
        "Topic :: Internet",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ephemeral-chat=src.ephemeral_chat:main",
        ],
    },
    keywords="privacy, encryption, p2p, chat, anonymous, ephemeral, security",
    project_urls={
        "Bug Reports": "https://github.com/privacy-research/anonymous-ephemeral-chat/issues",
        "Source": "https://github.com/privacy-research/anonymous-ephemeral-chat",
        "Documentation": "https://github.com/privacy-research/anonymous-ephemeral-chat/blob/main/README.md",
    },
)
