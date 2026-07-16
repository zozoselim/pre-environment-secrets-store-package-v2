import setuptools


setuptools.setup(
    name="environment-secrets-store",
    version="0.0.1",
    author="NovaVision AI",
    author_email="info@novavision.ai",
    description=(
        "Securely retrieves environment variables and exposes "
        "them to NovaVision workflow components."
    ),
    url=(
        "https://github.com/zozoselim/"
        "pre-environment-secrets-store-package-v2"
    ),
    license="MIT",
    install_requires=[
        "sdk",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=[
        "novavision.package",
        "novavision.package.executors",
        "novavision.package.models",
        "novavision.package.utils",
    ],
    package_dir={
        "novavision.package": "src",
    },
    python_requires=">=3.8",
)