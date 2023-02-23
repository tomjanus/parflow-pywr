""" This module defines functions which find and read Parflow output (pfb) files

    Functions:
    ---------------------------------
    find_output_files(directory, substr): returns an iterable object containing
                                          .pfb output file mathing the pattern
                                          specified in substr
    read(filename): returns np.array with pressures in the entire computational
                    domain
"""

import os
import logging
import numpy as np

logger = logging.getLogger(__name__)  # Initialise a logger for logging messages


def find_output_files(directory, substr):
    """ Look in a specified directory and find all .pfb files which match a
        pattern specified as substr

        Parameters
        -----------------------------
        directory: str
            Path to the .pfb files
        substr: str
            Pattern of the output file to match

        Returns
        -----------------------------
        filename: str
            Name of the file which matches the criterion
    """

    for filename in sorted(os.listdir(directory)):
        #  skip files with a .dist extension
        #  if filename[len(filename)-4:] == 'dist':
        #    continue
        #  base, _ = os.path.splitext(filename)  # remove .00000 extension
        #  base, ext = os.path.splitext(base)
        base, ext = os.path.splitext(filename)
        if ext.lower() != '.pfb':
            continue  # skip non-pfb files
        if substr in base:
            yield filename


def read(filename):
    """ Read a parflow output file and return the data.
        Parameters
        --------------------------
        filename : str
            Name of the Parflow .pfd file to read

        Returns
        --------------------------
        data: np.array
            Pressures calculated in all points in the computational grid
    """
    #logger.debug('Reading parflow file: "{}"'.format(filename))
    # Read data from Parflow's binary output file
    with open(filename, "rb") as f:
        #print("File name: "+filename)
        # Read 9 values (see count) of big-endian 32-bit signed integers
        a = np.fromfile(f, dtype='>i4', count=9)  # a is an auxiliary np array
        # Number of x- y- and z-dim points in the computational grid
        nx = a[6]
        ny = a[7]
        nz = a[8]
        nn = nx * ny * nz
        # Create an empty numpy array to store results
        data = np.empty(nn)
        # Read 3 values (see count) of big-endian 64-bit floating-point numbers
        d = np.fromfile(f, dtype='>f8', count=3)
        # Find computational grid spacing in x, y, and z dimensions
        dx = d[0]
        dy = d[1]
        dz = d[2]
        # Read a big-endian 32-bit signed integer value
        a = np.fromfile(f, dtype='>i4', count=1)
        nsubgrid = a[0]  # What is this variable?
        ostride = 0
        for i in range(0, nsubgrid):
            # Read 9 values (see count) of big-endian 32-bit signed integers
            a = np.fromfile(f, dtype='>i4', count=9)
            ix = a[0]
            iy = a[1]
            iz = a[2]
            inx = a[3]
            iny = a[4]
            inz = a[5]
            inn = inx * iny * inz
            stride = ostride + inx * iny * inz
            # Read a vector of data
            # What is this data? Water pressures (water-depths)?
            data[ostride:stride] = np.fromfile(f, dtype='>f8', count=inn)
            ostride = stride
            output = data.reshape((nx, ny, nz)), (dx, dy, dz)
    return output

# For testing, if called from main, read from the specified path and print the
# returned data structure
if __name__ == '__main__':
    a = read('/home/james/dev/parflow/test/default_single.out.press.00000.pfb')
    print(a.shape)
