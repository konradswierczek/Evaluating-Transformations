# USING IRRELEVANT MUSICAL TRANSFORMATIONS TO EVALUATE THE ROBUSTNESS OF AUDIO FEATURES WITHOUT GROUND TRUTH

Data and reproducible analysis for "Using Irrelevant Musical Transformations to Evaluate the Robustness of Audio Features Without Ground Truth" by Konrad Swierczek & Michael Schutz submitted in Psychology of Music. This repository is roughly split into two halves: file generation and MIR analysis, run in Python (and a little bit of MATLAB for MIRtoolbox), and statistical analysis and data visualization, run in R.

## Organization
```
.
├── data # SQLite3 database, metadata, inference, etc.
├── docker # Dockerfile for Python.
│   └── python
├── etc
│   ├── audio # Generated Audio Files (not committed due to size).
│   └── seed_midi # Original MIDI files.
├── img # All figures.
├── renv
└── src
    ├── matlab # MIRtoolbox as git submodule.
    ├── python # File Generation and MIR Analysis.
    │   ├── experiment # Scripts to run the experiment.
    └── R # Statistical Analysis and Data Visualization.
        ├── figures # Individual scripts for each figure in paper.
        └── supplementary # Extra analyses and figures.

```

## Docker
Most of the analyses are reproducible with docker compose. For instance, to generate all the audio files simple run the following from project root:
```
docker compose --rm generate-audio
```

To generate all the main visualizations:
```
docker compose --rm generate-figures
```

At the time of writing, we are unable to make the MATLAB analyses reproducible in Docker. Since MATLAB requires authentication, and we were unable to non-interactively authenticate, using MATLAB engine for Python in a container appears at the least challenging. However, we have provided the script for recreating the MATLAB analysis with Python locally. Assuming that package versions are matched and no OS level dependencies are impacting the process, you should be able to reproduce it locally. If you have any suggestions on making MATLAB engine for Python analyses reproducible with Docker, please open an issue!

Assuming you have an enviornment loaded up, audio files generated, and matlab all setup, you can reproduce the MIRtoolbox analyses with:
```
python3 -m src.python.experiment.extract_features_matlab
```

## TODO:
- SQL runs aren't super "smart": could check if a task has already been completed in db.
- Shiny app summary figure could use more work
- Deploy Shiny app
- Expand on GH Pages
- Calculate RDB once (not that important)
- Move python to remir
