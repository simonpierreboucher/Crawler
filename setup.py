from setuptools import setup, find_packages

setup(
    name="web-crawler",
    version="1.2.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
    ],
    entry_points={
        'console_scripts': [
            'crawler=src.run:main',
        ],
    },
)
