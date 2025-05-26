"""
Analysis interface for vgosDB data access
Provides convenient methods for extracting data needed for EOP estimation
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class AnalysisInterface:
    """
    High-level interface for accessing vgosDB data for analysis
    
    This class wraps a VgosDBReader to provide convenient access to the
    specific data needed for VLBI analysis and EOP estimation.
    """
    
    def __init__(self, reader):
        """
        Initialize with a VgosDBReader instance
        
        Parameters
        ----------
        reader : VgosDBReader
            An opened vgosDB reader instance
        """
        self.reader = reader
    
    def get_observations(self, band: str = 'X') -> pd.DataFrame:
        """
        Get clean observation data for analysis
        
        Parameters
        ----------
        band : str, default 'X'
            Frequency band ('X' or 'S')
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: time, baseline, source, delay_obs, delay_sigma, delay_theo
        """
        try:
            # Get time tags
            time_data = self.reader['Observables']['TimeUTC.nc']
            times = self._convert_time_to_mjd(time_data)
            
            # Get baseline and source info
            baseline_data = self.reader['Observables']['Baseline.nc']
            source_data = self.reader['Observables']['Source.nc']
            
            # Get delay observables
            delay_full = self.reader['ObsEdit'][f'GroupDelayFull_b{band}.nc']
            delay_sigma = self.reader['Observables'][f'GroupDelay_b{band}.nc']
            delay_theo = self.reader['ObsTheoretical']['DelayTheoretical.nc']
            
            # Create DataFrame
            obs_df = pd.DataFrame({
                'time_mjd': times,
                'baseline_1': baseline_data.Baseline.values[:, 0],
                'baseline_2': baseline_data.Baseline.values[:, 1], 
                'source': source_data.Source.values,
                'delay_obs': delay_full.GroupDelayFull.values,
                'delay_sigma': delay_sigma.GroupDelaySig.values,
                'delay_theo': delay_theo.DelayTheoretical.values
            })
            
            # Add baseline name for convenience
            obs_df['baseline'] = obs_df['baseline_1'] + '-' + obs_df['baseline_2']
            
            return obs_df
            
        except KeyError as e:
            raise ValueError(f"Required data not found in vgosDB: {e}")
    
    def get_eop_partials(self) -> Dict[str, np.ndarray]:
        """
        Get EOP partial derivatives
        
        Returns
        -------
        dict
            Dictionary with keys 'ut1_partials', 'xpole_partials', 'ypole_partials'
            Each contains partial derivatives [delay_partial, rate_partial] for each obs
        """
        try:
            partials = self.reader['ObsPart']['Part-EOP.nc']
            
            return {
                'ut1_partials': partials.UT1Part.values,        # [2, N_obs] (delay, rate)
                'xpole_partials': partials.WobblePart.values[0], # [2, N_obs] 
                'ypole_partials': partials.WobblePart.values[1]  # [2, N_obs]
            }
            
        except KeyError as e:
            raise ValueError(f"EOP partials not found in vgosDB: {e}")
    
    def get_station_positions(self) -> Dict[str, np.ndarray]:
        """
        Get station coordinates
        
        Returns
        -------
        dict
            Dictionary with 'names' and 'xyz' arrays
        """
        try:
            stations = self.reader['Apriori']['StationApriori.nc']
            
            return {
                'names': stations.StationNameApriori.values,
                'xyz': stations.StationXYZ.values.T  # [N_stations, 3]
            }
            
        except KeyError as e:
            raise ValueError(f"Station data not found in vgosDB: {e}")
    
    def get_a_priori_eop(self) -> Dict[str, np.ndarray]:
        """
        Get a priori EOP values used in theoretical calculations
        
        Returns
        -------
        dict
            Dictionary with scan times and EOP values
        """
        try:
            eop = self.reader['Scan']['ERPApriori.nc']
            time_data = self.reader['Scan']['TimeUTC.nc']
            
            return {
                'time_mjd': self._convert_time_to_mjd(time_data),
                'ut1': eop.UT1.values,
                'x_pole': eop.PolarMotion.values[0, :],  # X component
                'y_pole': eop.PolarMotion.values[1, :]   # Y component  
            }
            
        except KeyError as e:
            raise ValueError(f"A priori EOP data not found in vgosDB: {e}")
    
    def get_baseline_info(self) -> pd.DataFrame:
        """
        Get baseline information with station coordinates
        
        Returns
        -------
        pd.DataFrame
            DataFrame with baseline info and coordinates
        """
        obs_df = self.get_observations()
        stations = self.get_station_positions()
        
        # Create station lookup
        station_coords = dict(zip(stations['names'], stations['xyz']))
        
        # Add coordinates for each baseline
        baseline_info = []
        for _, obs in obs_df.iterrows():
            sta1, sta2 = obs['baseline_1'], obs['baseline_2']
            if sta1 in station_coords and sta2 in station_coords:
                baseline_info.append({
                    'baseline': obs['baseline'],
                    'station_1': sta1,
                    'station_2': sta2,
                    'xyz_1': station_coords[sta1],
                    'xyz_2': station_coords[sta2],
                    'baseline_vector': station_coords[sta2] - station_coords[sta1]
                })
        
        return pd.DataFrame(baseline_info)
    
    def _convert_time_to_mjd(self, time_data) -> np.ndarray:
        """
        Convert vgosDB time format to Modified Julian Date
        
        Parameters
        ----------
        time_data : xarray.Dataset
            Time data from TimeUTC.nc file
            
        Returns
        -------
        np.ndarray
            Time in Modified Julian Date format
        """
        # vgosDB stores time as YMDHM + seconds
        ymdhm = time_data.YMDHM.values  # [5, N_obs] or [N_obs, 5]
        seconds = time_data.Second.values
        
        # Ensure correct shape
        if ymdhm.ndim == 2 and ymdhm.shape[0] == 5:
            ymdhm = ymdhm.T  # Convert to [N_obs, 5]
        
        mjd_times = []
        for i in range(len(seconds)):
            year, month, day, hour, minute = ymdhm[i]
            
            # Convert to MJD (simplified - you might want a more robust converter)
            # MJD = JD - 2400000.5
            # This is a basic implementation
            if month <= 2:
                year -= 1
                month += 12
            
            a = year // 100
            b = 2 - a + a // 4
            
            jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
            mjd = jd - 2400000.5
            
            # Add time of day
            mjd += (hour + minute/60.0 + seconds[i]/3600.0) / 24.0
            mjd_times.append(mjd)
            
        return np.array(mjd_times)
    
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of available data for analysis
        
        Returns
        -------
        dict
            Summary information about the session
        """
        try:
            obs_df = self.get_observations()
            stations = self.get_station_positions()
            
            return {
                'n_observations': len(obs_df),
                'n_stations': len(stations['names']),
                'stations': list(stations['names']),
                'sources': list(obs_df['source'].unique()),
                'baselines': list(obs_df['baseline'].unique()),
                'time_range': {
                    'start_mjd': obs_df['time_mjd'].min(),
                    'end_mjd': obs_df['time_mjd'].max(),
                    'duration_hours': (obs_df['time_mjd'].max() - obs_df['time_mjd'].min()) * 24
                },
                'delay_stats': {
                    'mean_delay_us': obs_df['delay_obs'].mean() * 1e6,
                    'std_delay_us': obs_df['delay_obs'].std() * 1e6,
                    'mean_sigma_ns': obs_df['delay_sigma'].mean() * 1e9
                }
            }
            
        except Exception as e:
            return {'error': f"Could not generate summary: {e}"}