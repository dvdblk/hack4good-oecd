# Hack4Good - OECD

* https://hackmd.io/g5AYgepnQrqrk4V26DrQMg

* https://docs.google.com/spreadsheets/d/1pKb_1Je4hD2X8IfYrFXYqBhWfPg5lgPY/edit?usp=sharing&ouid=110500414719598262605&rtpof=true&sd=true

## Getting started

### Conda Environment
To run the pipeline (jupyter notebooks) you need to create a conda environment with the required dependencies.

> Requirements: [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

To **create** a conda environment after cloning the repo:
```
# from the root of the repo
conda env create -f environment.yml
# to activate the environment
conda activate hack4good
# to deactivate the environment (when you're done)
conda deactivate
```

## Contributing
1. Install [pre-commit](https://pre-commit.com/#installation).
2. `pre-commit install`
3. Add changes, commit and pull request to `main` branch.
