
````markdown
# Caffeine PK Modeling with Public PK-DB Data

This project builds a machine learning workflow for caffeine pharmacokinetic concentration-time prediction using publicly available data from PK-DB.

The goal is to demonstrate how public pharmacokinetic data can be extracted, cleaned, standardized, and used for baseline machine learning modeling.

## Project Overview

Caffeine is widely used in pharmacokinetic studies related to liver metabolism and CYP1A2 activity. This repository focuses on caffeine concentration-time prediction, not CYP1A2 activity prediction or liver disease diagnosis.

The workflow includes:

- Searching caffeine-related studies in PK-DB
- Extracting caffeine concentration-time records
- Standardizing concentration units to ng/mL
- Extracting caffeine dose from intervention metadata
- Training baseline ML regression models
- Comparing performance with and without dose information

## Data Source

This project uses public pharmacokinetic data from PK-DB.

The published caffeine PK-DB dataset described by Grzegorzewski et al. includes 141 publications, 500 groups, 4,714 individuals, 387 interventions, 24,571 pharmacokinetic outputs, and 846 time-courses.

Reference:

Grzegorzewski J, Bartsch F, Köller A, König M.  
**Pharmacokinetics of Caffeine: A Systematic Analysis of Reported Data for Application in Metabolic Phenotyping and Liver Function Testing.**  
Frontiers in Pharmacology. 2022.

## Current Dataset

This repository currently uses a curated subset of the full public caffeine dataset:

- 504 caffeine concentration-time records
- 5 public PK-DB studies
- Plasma and saliva measurements
- Concentration standardized to ng/mL
- 193 rows with extractable caffeine dose information

Included studies:

- Jost1987
- Lenuzza2016
- PVLDrugs
- He2017
- Edwards2017

## Machine Learning Task

Input features:

- Time
- Caffeine dose
- Study name
- Tissue
- Assay method

Target:

- Caffeine concentration in ng/mL

## Models Used

- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor
- Support Vector Regression

## Results

Adding caffeine dose as a structured feature improved model performance on the dose-available subset.

Best model:

```text
Gradient Boosting Regressor
R² ≈ 0.90
MAE ≈ 347 ng/mL
RMSE ≈ 443 ng/mL
Rows used: 193
````

## Important Note

This project does not predict CYP1A2 activity, liver function, or disease status.

The current model predicts caffeine concentration from pharmacokinetic metadata such as time, dose, tissue, study name, and assay method.

The high R² result applies only to the dose-available subset, not the full PK-DB caffeine dataset. This is a portfolio-scale ML demonstration, not a clinical dosing model.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── 27_build_selected_caffeine_master_dataset.py
├── data/
└── reports/
```

## Future Work

* Expand extraction to more caffeine publications
* Improve dose extraction from non-standard intervention labels
* Add subject-level covariates such as age, weight, smoking status, and health status
* Use study-aware validation
* Build an interactive Streamlit app

