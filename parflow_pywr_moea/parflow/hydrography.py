""" Functions for calculating discharge from pressure in Parflow output files
    out.press.

    Functions:
    --------------------------------------
    find_slope_files: returns tuples with slope files in x and y directions in
                      a given directory matching a pattern out.slope_{}
    read_discharge: calculated discharge from Parflow output pressure in slope
                    files in a specified directory for given coordinates and a
                    given Manning's coefficient
    """

import os
import logging
import numpy as np
from .pf_read import read, find_output_files

logger = logging.getLogger(__name__)


def find_slope_files(directory, suffix='out.slope_{}'):
    """ Return the filenames of x and y slope files in the given directory.
        Parameters
        -----------------------------------
        directory : str
            Name of the directory (path) where slope files are located
        suffix : str
            Pattern for recognizing slope files in the directory
            (out.slope_{}) where {} is either 'x' or 'y'

        Returns
        -----------------------------------
        slope_x, slopye_y
            Tuple with slope file names in x and y directions, respectively

        Raises
        -----------------------------------
        FileNotFoundError
            If unable to find a slope file

    """
    slope_x = None
    slope_y = None

    for filename in os.listdir(directory):
        # Lines commented out by Andrew Slaughter
        # base, _ = os.path.splitext(filename)  # remove .00000 extension
        # base, ext = os.path.splitext(base)  # remove extension .pfb

        # Andrew's new line
        base, ext = os.path.splitext(filename)  # remove extension .pfb

        if ext.lower() != '.pfb':
            continue  # skip non-pfb files

        if base.endswith(suffix.format('x')):
            slope_x = filename
        elif base.endswith(suffix.format('y')):
            slope_y = filename

    if slope_x is None:
        raise FileNotFoundError('Unable to find slope x output file in \
                                directory: "{}"'.format(directory))
    if slope_y is None:
        raise FileNotFoundError('Unable to find slope y output file in \
                                directory: "{}"'.format(directory))

    return slope_x, slope_y


# List of parameters in the read_discharge function and with a coma and
# blank space, fix it
def read_discharge(directory, coordinates, start_from, channel_width=100,
                   mannings=8.333e-6, ):
    """ Discover and read Parflow results inside `directory`.

    This function calculates discharge from Parflow based on the
    values of ponding depth in cell 0,0,0.
    Uses default Manning's coefficient of 8.333e-6 h/(m^(1/3)) which should
    be equal to the value set in Parflow in the profile.tcl script
    """

    slope_x_filename, slope_y_filename = find_slope_files(directory)
    slpx, deltax = read(os.path.join(directory, slope_x_filename))
    slpy, deltay = read(os.path.join(directory, slope_y_filename))
    if slpx.shape != slpy.shape:
        raise ValueError(
            'Data dimensions from slope files is not the same shape. '
            'x: {}, y: {}'.format(slpx.shape, slpy.shape))
    if deltax != deltay:
        raise ValueError(
            'Grid sizes from slope files is not the same shape. '
            'x: {}, y: {}'.format(slpx.shape, slpy.shape))
    nx, ny, nz = slpx.shape
    # dx, dy, dz = deltax
    n_obs = 9
    # TODO pass through the substr keyword argument so it is configurable
    # from this function
    # Sorted output files
    output_files = list(find_output_files(directory, 'out.press'))

    if start_from >= len(output_files):
        raise ValueError('Trying to remove more entries than the flow vector \
                          has. Using full vector')
    else:
        del output_files[:start_from]

    nt = len(output_files)
    discharge = {k: np.ndarray(nt, dtype='f8') for k in coordinates.keys()}
    # Loop over timesteps
    for t, filename in enumerate(output_files):
        data, deltap = read(os.path.join(directory, filename))
        if slpx.shape[:2] != data.shape[:2]:
            raise ValueError(
                'First two dimensions from pressure file ("{}") \
                is not the same shape as the slope files. '
                'x: {}, y: {}'.format(filename, slpx.shape, data.shape))
        if deltax != deltap:
            raise ValueError(
                'Grid sizes from pressure file ("{}") is not the same shape. '
                'x: {}, y: {}'.format(filename, deltax.shape, deltay.shape))
        # TODO can this loop be vectorised?
        for key, (oi, oj, ok) in coordinates.items():
            #print("ponding depth: {}".format(data[oi, oj, ok]))
            # Calculate discharge using Manning's formula (in m3/h)
            q = channel_width * (abs(slpx[oi, oj, 0])) ** (1.0 / 2.0) / \
                mannings * max(data[oi, oj, ok], 0) ** (5.0 / 3.0)
            q += channel_width * (abs(slpy[oi, oj, 0])) ** (1.0 / 2.0) / \
                mannings * max(data[oi, oj, ok], 0) ** (5.0 / 3.0)
            # Convert units from m3/hr (Parflow) to m3/day
            q *= 24
            discharge[key][t] = q
            # print("discharge, m3/d: {}".format(q))
    print("Discharge characteristics: ")
    logger.info("Mean flow: {} m3/d".format(np.mean(discharge[key])))
    logger.info("Median flow: {} m3/d".format(np.median(discharge[key])))
    logger.info("Max flow: {} m3/d".format(np.max(discharge[key])))
    logger.info("Min flow: {} m3/d".format(np.min(discharge[key])))
    logger.info("Std. dev. of flow: {} sqrt(m3/d)".format(
                np.std(discharge[key])))
    #import pdb; pdb.set_trace()
    return discharge
