from setuptools import setup, find_packages

setup(
    name="siko-auction-monitor",
    version="0.1.0",
    description="Monitor sikoauktioner.se for auctions with search word filtering and Home Assistant notifications",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.0",
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "aiohttp>=3.8.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "siko-monitor=src.main:main",
        ],
    },
)