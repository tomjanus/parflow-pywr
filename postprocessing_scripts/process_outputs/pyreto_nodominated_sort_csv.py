import sys
import os
import gzip
import time
import glob
import json
import logging
import errno
import pandas
import pygmo as pg
from dateutil import parser

# instantiate logger for logging errors, warnings and other communication
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(stream=sys.stdout)
formatter_long = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
                                    %(message)s')
formatter_short = logging.Formatter('%(message)s')
ch.setFormatter(formatter_short)
logger.addHandler(ch)

#TODO: INCORPORATE THIS INTO THE CLI (AT THE MOMENT IT IS JUST A STANDALONE SCRIPT THAT I USED ONCE TO GET THE RESULTS I NEEDED QUICKLY (TJ)
# TODO: CHECK THIS CODE, LOOKS LIKE IT DOESN'T DO A PROPER JOB AT CREATING NONDOMINATED SOLUTION SET

def nonominated_sort_csv(nonsorted_file_name, sorted_file_name, sorted_file_type, objective_cols):
    ''' Imports a csv file with solutions, runs a nondominated search on them and
        returns a file with only nondominated solutions in csv.gz format '''

    logger.info('Input file name: {}'.format(nonsorted_file_name)
    logger.info('Output file name: {}'.format(sorted_file_name))

    # Import the csv file into a dataframe
    metrics_and_vars = pandas.read_csv(nonsorted_file_name)

    # Initialise local variables used
    if objective_cols == None:
        objective_cols = ['turbine1_energy', 'max_flooded_area', 'bare_soil_count', 'crop_count', 'landuse_diversity']

    # Perform nondominated sorting with pygmo
    logger.info(f'Performing non-dominated sort on search')
    t0 = time.perf_counter()
    # ndf = list of non-dominated fronts
    # dl = domination list
    # dc = domination count
    # ndr = non-domination ranks
    # USAGE: ndf, dl, dc, ndr = pg.fast......
    non_dom_fronts, *_ = pg.fast_non_dominated_sorting(
       metrics_and_vars[objective_cols].values)
    tsort = time.perf_counter() - t0
    logger.info(f'Non-dominated sort complete in {tsort:.2f}s')
    
    indices = non_dom_fronts[0]
    metrics_and_vars_nondom = metrics_and_vars.iloc[indices, :]

    if sorted_file_type.lower() == 'csv':
        metrics_and_vars_nondom.to_csv(
            os.path.join(sorted_file_name+'.csv.gz'))
        logger.info('Metrics saved to compressed CSV file {} in current directory'.
                    format(metrics_file_name + '.csv'))
    elif sorted_file_type.lower() == 'h5':
        metrics_and_vars_nondom.to_hdf(
            os.path.join(output_path, metrics_file_name+'.h5'), 'metrics')
        logger.info('Metrics saved to HDF file {} in current directory'.
                    format(metrics_file_name + '.h5'))
