from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="py_backup",
    version="0.1.0",
    description="A Python module for backing up files and folders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Andreas Thorén",
    author_email="at.lakarkonsult@gmail.com",
    url="https://github.com/andreas-thoren/py-backup",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "py-backup=py_backup.cli:main",
        ],
    },
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.11",
)
