import setuptools


setuptools.setup(
    name="environment-secrets-store",
    version="0.1.0",
    author="NovaVision AI",
    author_email="info@novavision.ai",
    description=(
        "Securely retrieves explicitly requested environment variables and "
        "exposes them to NovaVision workflow components."
    ),
    url=(
        "https://github.com/zozoselim/"
        "pre-environment-secrets-store-package-v2"
    ),
    license="MIT",
    install_requires=[
        "python-dotenv>=1.0,<2.0",
        "requests>=2.31,<3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8,<9",
        ],
    },
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
    include_package_data=True,
    zip_safe=False,
)