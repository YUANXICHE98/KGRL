"""
KGRL: Knowledge Graph Enhanced Reinforcement Learning
Setup configuration for the research project.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kgrl-research",
    version="1.0.0",
    author="KGRL Research Team",
    author_email="research@example.com",
    description="Knowledge Graph Enhanced Reinforcement Learning for Complex Decision Making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/kgrl-research",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
            "pre-commit>=3.3.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=2.0.0",
        ],
        "viz": [
            "plotly>=5.14.0",
            "dash>=2.10.0",
            "streamlit>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kgrl-train=scripts.train.train_unified:main",
            "kgrl-eval=scripts.evaluate.run_evaluation:main",
            "kgrl-viz=scripts.utils.visualize_traces:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.txt", "*.md"],
    },
    zip_safe=False,
    keywords="reinforcement-learning knowledge-graph nlp ai research",
    project_urls={
        "Bug Reports": "https://github.com/your-username/kgrl-research/issues",
        "Source": "https://github.com/your-username/kgrl-research",
        "Documentation": "https://kgrl-research.readthedocs.io/",
    },
)
