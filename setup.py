from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="idadv_dash_simulator",
    version="0.1.0",
    author="30mb1",
    author_email="your.email@example.com",
    description="Indonesian Adventure Simulator - Game mechanics simulation and analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/30mb1/idadv_dash_simulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "dash==2.14.0",
        "dash-core-components==2.0.0",
        "dash-html-components==2.0.0",
        "dash-table==5.0.0",
        "pandas==2.1.2",
        "plotly==5.18.0",
        "numpy==1.26.1",
    ],
    entry_points={
        "console_scripts": [
            "idadv-simulator=run_simulator:main",
            "idadv-dashboard=run_dashboard:main",
        ],
    },
    include_package_data=True,
    package_data={
        "assets": ["*"],
    },
) 