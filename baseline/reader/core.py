#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced VgosDB Reader for handling tgz archives of NetCDF files
"""

import tarfile
import io
import xarray as xr
import re
from pathlib import Path

class Node:
    def __init__(self, tar, members, prefix="", cache=None):
        self._tar = tar
        self._members = members
        self._prefix = "" if prefix in ("", "/") else prefix.rstrip('/') + '/'
        self._cache = cache or {}

    def __getitem__(self, key):
        path = self._prefix + key
        
        # Check if it's a directory (has subdirectories or files under it)
        if path + '/' in self._members or any(m.startswith(path + '/') for m in self._members):
            return Node(self._tar, self._members, path, self._cache)
        # Check if it's a file
        elif path in self._members:
            # Use cache if available
            if path in self._cache:
                return self._cache[path]
            
            fileobj = self._tar.extractfile(self._members[path])
            dataset = xr.open_dataset(io.BytesIO(fileobj.read()))
            self._cache[path] = dataset  # Cache the dataset
            return dataset
        else:
            raise KeyError(f"'{key}' not found")

    def keys(self):
        children = set()
        prefix_len = len(self._prefix)
        for name in self._members:
            if not name.startswith(self._prefix):
                continue
            rest = name[prefix_len:]
            if '/' in rest:
                child = rest.split('/', 1)[0]
            else:
                child = rest
            if child:  # Skip empty strings
                children.add(child)
        return children

    def __repr__(self):
        return f"<Node: {sorted(self.keys())}>"
    
    def pretty_print(self, max_depth=3, _depth=0, _prefix=""):
        """Pretty print the directory structure"""
        if _depth > max_depth:
            return
        keys = sorted(self.keys())
        for i, key in enumerate(keys):
            is_last = i == len(keys) - 1
            connector = "└── " if is_last else "├── "
            
            # Check if this is a NetCDF file and show some info
            full_path = self._prefix + key
            if full_path in self._members and key.endswith('.nc'):
                # Get file size
                size = self._members[full_path].size
                size_str = f" ({self._format_size(size)})"
                print(_prefix + connector + key + size_str)
            else:
                print(_prefix + connector + key)
    
            try:
                child = self[key]
                if isinstance(child, Node):
                    extension = "    " if is_last else "│   "
                    child.pretty_print(max_depth, _depth + 1, _prefix + extension)
            except Exception:
                continue
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def find_files(self, pattern):
        """Find all files matching a pattern (regex supported)"""
        matches = []
        regex = re.compile(pattern)
        for path in self._members:
            if path.startswith(self._prefix):
                relative_path = path[len(self._prefix):]
                if regex.search(relative_path):
                    matches.append(relative_path)
        return sorted(matches)
    
    def list_nc_files(self):
        """List all NetCDF files under this node"""
        return self.find_files(r'\.nc$')


class VgosDBReader:
    def __init__(self, path):
        self.path = Path(path)
        self._tar = tarfile.open(path, 'r:gz')
        self._members = {
            m.name: m for m in self._tar.getmembers()
            if m.isfile() and m.name.endswith('.nc')
        }
        self._cache = {}
        
        # Auto-skip single root directory
        root_dirs = set()
        for member_path in self._members:
            if '/' in member_path:
                root_dir = member_path.split('/')[0]
                root_dirs.add(root_dir)
            else:
                root_dirs.add('')  # Files at root level
        
        if len(root_dirs) == 1 and '' not in root_dirs:
            # Single root directory - skip it
            self._root_prefix = list(root_dirs)[0] + '/'
        else:
            self._root_prefix = ''
        
        self.root = Node(self._tar, self._members, self._root_prefix, self._cache)

    def __getitem__(self, key):
        return self.root[key]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the tarfile and clear cache"""
        if hasattr(self, '_tar'):
            self._tar.close()
        self._cache.clear()
        
    def pretty_print(self, max_depth=3):
        """Pretty print the directory structure"""
        print(f"VgosDB Archive: {self.path.name}")
        print("=" * 40)
        self.root.pretty_print(max_depth=max_depth)
    
    def find_files(self, pattern):
        """Find all files matching a pattern"""
        return self.root.find_files(pattern)
    
    def list_nc_files(self):
        """List all NetCDF files in the archive"""
        return self.root.list_nc_files()
    
    def get_stations(self):
        """Try to identify station names from file structure"""
        stations = set()
        # Look for common patterns in VLBI data
        for path in self._members:
            # Remove root prefix if it exists
            clean_path = path[len(self._root_prefix):] if path.startswith(self._root_prefix) else path
            
            # Look for station codes (typically 2-8 uppercase letters)
            parts = clean_path.split('/')
            for part in parts:
                # Station codes are often in filenames or directory names
                if re.match(r'^[A-Z]{2,8}$', part):
                    stations.add(part)
                # Also check for station patterns in filenames
                matches = re.findall(r'[A-Z]{2,8}', part)
                stations.update(matches)
        
        return sorted(list(stations))
    
    def summary(self):
        """Print a summary of the archive contents"""
        nc_files = self.list_nc_files()
        stations = self.get_stations()
        
        print(f"VgosDB Archive Summary: {self.path.name}")
        print("=" * 50)
        print(f"NetCDF files: {len(nc_files)}")
        print(f"Potential stations: {', '.join(stations) if stations else 'None detected'}")
        
        # Group files by type
        file_types = {}
        for f in nc_files:
            if '/' in f:
                category = f.split('/')[0]
            else:
                category = 'root'
            file_types[category] = file_types.get(category, 0) + 1
        
        if file_types:
            print("\nFile categories:")
            for category, count in sorted(file_types.items()):
                print(f"  {category}: {count} files")


# Example usage
if __name__ == "__main__":
    # Use context manager for automatic cleanup
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