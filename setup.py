import setuptools


setuptools.setup(
    name="environment-secrets-store",
    version="0.4.0",
    author="NovaVision AI",
    author_email="info@novavision.ai",
    description=(
        "Validates requested environment secrets and exposes only safe "
        "environment-variable references to downstream components."
    ),
    url=(
        "https://github.com/zozoselim/"
        "pre-environment-secrets-store-package-v2"
    ),
    license="MIT",
    install_requires=[],
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
