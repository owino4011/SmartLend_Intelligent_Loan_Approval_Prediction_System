from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="smart_lend_loan_prediction_system",
    version="1.0.0",
    author="SmartLend AI Team",
    author_email="support@smartlend.ai",
    description="Intelligent Loan Approval Predictor with Streamlit UI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/owino4011/Smart_Lend_Loan_Prediction_System", 
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "streamlit>=1.30.0",
        "pandas>=2.0",
        "joblib>=1.3",
        "numpy>=1.25",
        "scikit-learn>=1.3",
        "matplotlib>=3.8",
        "seaborn>=0.12"
    ],
    entry_points={
        "console_scripts": [
            # Optional CLI commands pointing to scripts in src/scripts
            "train_model=scripts.train_model:main",
            "evaluate_model=scripts.evaluate_model:main",
            "run_app=app:main"  # Wrap app.py in a main() function
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Streamlit",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
