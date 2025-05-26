#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Primary modeling testing file for now
"""


from reader import VgosDBReader


with VgosDBReader('20250520-p2025140.tgz') as ds:
    ds.summary()
    print("\n")
    ds.pretty_print(2)
    
    # Now you can access data without specifying root directory
    try:
        antenna_data = ds['Apriori']['Antenna.nc']
        print(f"\nAntenna data shape: {antenna_data.dims}")
    except KeyError as e:
        print(f"Could not access antenna data: {e}")