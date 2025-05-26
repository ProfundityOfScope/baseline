#!/usr/bin/env python3
"""
Basic EOP estimation example using vgosdb-toolkit
"""

import sys
from pathlib import Path

# Add the package to path if running from repo
sys.path.insert(0, str(Path(__file__).parent.parent))

from baseline import VgosDBReader, AnalysisInterface, EOPEstimator

def main():
    # Path to your data file
    data_file = "20250520-p2025140.tgz"  # User provides this
    
    if not Path(data_file).exists():
        print(f"Please download a vgosDB file and place it here: {data_file}")
        return
    
    # Load and analyze
    with VgosDBReader(data_file) as reader:
        # Get analysis interface
        analysis = AnalysisInterface(reader)
        
        # Quick summary
        summary = analysis.summary()
        print(f"Session has {summary['n_observations']} observations")
        print(f"Stations: {summary['stations']}")
        
        # Estimate EOPs
        estimator = EOPEstimator(analysis)
        results = estimator.estimate_eop(['UT1', 'x_pole', 'y_pole'])
        
        # Print results
        print(f"\nEOP Results:")
        print(f"UT1-UTC: {results['eop_values']['UT1']:.6f} ± {results['uncertainties']['UT1']:.6f} s")
        print(f"X-pole: {results['eop_values']['x_pole']:.3f} ± {results['uncertainties']['x_pole']:.3f} mas")
        print(f"Y-pole: {results['eop_values']['y_pole']:.3f} ± {results['uncertainties']['y_pole']:.3f} mas")

if __name__ == "__main__":
    main()