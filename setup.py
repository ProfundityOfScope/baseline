from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="baseline",
    version="0.1.0",
    author="ProfundityOfScope",
    author_email="ProfundityOfScope@users.noreply.github.com",
    description="Turn VLBI data into Earth rotation parameters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ProfundityOfScope/baseline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.18.0",
        "pandas>=1.0.0",
        "xarray>=0.16.0",
    ],
    extras_require={
        "plotting": ["matplotlib>=3.0.0"],
        "dev": ["pytest>=6.0", "black", "flake8"],
    },
    keywords="vlbi geodesy earth-rotation astronomy interferometry",
    project_urls={
        "Bug Reports": "https://github.com/ProfundityOfScope/baseline/issues",
        "Source": "https://github.com/ProfundityOfScope/baseline",
    },
)