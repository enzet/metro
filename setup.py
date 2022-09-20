"""Dynamic metadata."""
from pathlib import Path

from setuptools import setup
from metro import __author__, __description__, __email__, __doc_url__, __url__, __version__

with Path("README.md").open(encoding="utf-8") as input_file:
    long_description: str = input_file.read()

setup(
    name="metro",
    version=__version__,
    packages=["metro", "metro.core", "metro.geometry", "metro.harvest"],
    url=__url__,
    project_urls={"Bug Tracker": f"{__url__}/issues"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license="MIT",
    author=__author__,
    author_email=__email__,
    description=__description__,
    long_description=f"Python Wikidata transport system parser.\n\nSee [full documentation]({__doc_url__}).",
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": ["metro=metro.__main__:main"],
    },
    python_requires=">=3.9",
    install_requires=[
        "numpy~=1.23.3",
        "urllib3~=1.26.12",
    ],
)