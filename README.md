# Baseline

A Python toolkit for VLBI analysis - from vgosDB files to Earth orientation parameters.

## What it does

- Reads vgosDB files (the standard VLBI data format)
- Extracts observational data and calibrations
- Estimates Earth orientation parameters (EOPs)

## Quick example

```python
from baseline import VgosDBReader, AnalysisInterface, EOPEstimator

# Load a vgosDB file
with VgosDBReader('session.tgz') as reader:
    # Set up analysis
    analysis = AnalysisInterface(reader)
    estimator = EOPEstimator(analysis)
    
    # Estimate EOPs
    results = estimator.estimate_eop()
    
    # Print results
    print(f"UT1-UTC: {results['eop_values']['UT1']:.6f} seconds")
    print(f"Polar motion: X={results['eop_values']['x_pole']:.3f}, Y={results['eop_values']['y_pole']:.3f} mas")
```

## Installation

```bash
git clone https://github.com/ProfundityOfScope/baseline.git
cd baseline
pip install -e .
```

## What you need

- Python 3.7+
- A vgosDB file (`.tgz` format from IVS data centers)
- Basic packages: numpy, pandas, xarray

## Status

🚧 **Early development** - Basic EOP estimation works, more features coming!