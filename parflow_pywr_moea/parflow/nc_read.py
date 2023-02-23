""" Utility functions for reading data from Parflow HDF output files.

    Functions:
    --------------------------------------
    read_discharge: calculates discharge from Parflow output pressure in
                    profile.out.00001.nc nc file
    read_et: reads evapotranspiration data in profile.out.00001.nc
"""
import os
import numpy as np
import netCDF4


def read_discharge(directory, coordinates, channel_width=100, resample_size=None):
    """ Discover and read Parflow results inside `directory`.

    Parameters
    ------------------------------
    directory : str

    coordinates :
        Coordinates (points) for which discharge is calculated

    resample_size :

    Returns
    ------------------------------
    discharge : float
        Mean discharge flow

    Raises
    ------------------------------
    ValueError
        If dimensions from slope files in x and y dimensions are not equal

    This function attempts to x and y dimension slope files (JTomlinson)
    """

    # TODO make this output filename configurable
    fn = 'profile.out.00001.nc'
    # This file contains the simulation results
    nc_results = netCDF4.Dataset(os.path.join(directory, fn))
    # This file contains the slopes, mannings, etc. It only has one time-step
    nc_t0 = netCDF4.Dataset(os.path.join(directory, 'profile.out.00000.nc'))
    slpx = nc_t0.variables['slopex'][0, ...]
    slpy = nc_t0.variables['slopey'][0, ...]
    mannings = nc_t0.variables['mannings'][0, ...]

    if slpx.shape != slpy.shape != mannings.shape:
        raise ValueError('Data dimensions from slope files are not the same shape. '
                         'x: {}, y: {}'.format(slpx.shape, slpy.shape))
    discharge = {}

    for key, (oi, oj, ok) in coordinates.items():
        # The indexing in the NC files is [time, z, y, x]
        data = nc_results.variables['pressure'][:, ok, oj, oi]
        # Calculate discharge
        q = channel_width * (abs(slpx[oj, oi])) ** (1.0 / 2.0) / \
            mannings[oj, oi] * data ** (5.0 / 3.0)
        q += channel_width * (abs(slpy[oj, oi])) ** (1.0 / 2.0) / \
            mannings[oj, oi] * data ** (5.0 / 3.0)
        if resample_size is not None:
            end = resample_size * len(q) // resample_size
            # Here we reshape the timeseries so that each `resample_size` number
            # of hours is one row
            # For example, each day is a row, and each column is the hour within
            # the day.
            # The mean average is then calculated for each row (axis=1) to give,
            # for example, the daily mean flow.
            q = np.mean(q[:end].reshape(-1, resample_size), axis=1)
        discharge[key] = q
    return discharge


def read_et(directory, resample_size=None):
    """ Discover and read Parflow ET results inside `directory`.
    Parameters
    ---------------------------
    directory: str
        directory where the output .nc file is located

    Returns
    ---------------------------
    et: float
        total evapotranspiration for the domain
    """
    # TODO make this output filename configurable
    fn = 'profile.out.00001.nc'
    nc_results = netCDF4.Dataset(os.path.join(directory, fn))
    et = nc_results.variables['evaptrans']
    nt, nx, ny, nz = et.shape
    if resample_size is not None:
        end = resample_size * len(et) // resample_size
        # Compute the resample_size (e.g. daily) total ET.
        et = np.sum(et[:end].reshape(-1, resample_size, nx, ny, nz), axis=1)
    # Return timeseries total for the entire spatial domain
    return np.sum(et, axis=(1, 2, 3))
