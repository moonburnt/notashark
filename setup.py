from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="notashark",
    version="1.1.1",
    description="notashark - a discord bot for King Arthur's Gold",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moonburnt/notashark",
    author="moonburnt",
    author_email="moonburnt@disroot.org",
    license="GPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    packages=find_packages(),
    install_requires=[
        "pykagapi==0.2.1",
        "discord.py==2.1.0",
        "requests==2.28.1",
    ],
    entry_points={
        "console_scripts": ["notashark = notashark:cli.main"],
    },
)
