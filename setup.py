from setuptools import setup, find_packages

setup(
    name="py_backup",
    version="0.1.0",
    description="A Python module for backing up files and folders",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Andreas Thorén",
    author_email="at.lakarkonsult@gmail.com",
    url="https://github.com/andreas-thoren/py-backup",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        # Trove classifiers
        # Full list at https://pypi.org/classifiers/
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Match with your license
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.10",  # Minimum version requirement of Python for modern type hints
)
