""" Module contains read_et function which reads Parflow evapotranspiration
    outputs in out.evaptranssum"""

import os
import numpy as np
from .pf_read import read, find_output_files


def read_et(directory):
    """ Discover and read Parflow (evapotranspiration?) output results located
        inside directory.

        Parameters
        -------------------------------
        directory: str
            Path to the files which needs to be read

        Returns
        -------------------------------
        et: list
            Total sth..????

    This function attempts to read x and y dimension slope files (JTomlinson)
    """

    # TODO pass through the substr keyword argument so it is configurable
    # from this function
    # Sorted output files
    output_files = list(find_output_files(directory, 'out.evaptranssum'))
    # nt = len(output_files)
    et = []
    # Loop over timesteps
    for t, filename in enumerate(output_files):
        data, deltap = read(os.path.join(directory, filename))
        et.append(np.sum(data))
    return et
