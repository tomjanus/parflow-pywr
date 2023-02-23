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


def get_metrics_and_vars(archive):
    ''' The function takes the metrics DataFrame (metrics) and the list of
        json files containing individual MOEA results and produces a
        DataFrame of metrics and variables in the non-dominated front '''

    objective_cols = None
    variable_cols = None
    metrics = {}
    variables = {}
    for i in range(0, len(archive)):
        # Skip search.json files
        if archive[i][len(archive[i]) - 11:] == 'search.json':
            continue

        with open(archive[i], 'r') as json_file:
            json_dict = json.load(json_file)
            # bson_object_conv = BSON.encode(json_object)
            metrics[i] = {m['name']: m['value'] for m in
                          json_dict['metrics'] if m['objective']}
            variables[i] = {m['name']: m['value'] for m in
                            json_dict['variables']}
            # Check for the presence of evaluated_at, search_seed and
            # search_id in the JSON dict
            if "evaluated_at" in json_dict:
                metrics[i]['evaluated_at'] = parser.parse(
                    json_dict['evaluated_at'])
                variables[i]['evaluated_at'] = parser.parse(
                    json_dict['evaluated_at'])
                #pandas.to_datetime(metrics['evaluated_at'])
            if "search_seed" in json_dict:
                metrics[i]['search_seed'] = parser.parse(
                    json_dict['search_seed'])
                variables[i]['search_seed'] = parser.parse(
                    json_dict['search_seed'])
            if "search_id" in json_dict:
                metrics[i]['search_id'] = parser.parse(
                    json_dict['search_id'])
                variables[i]['search_id'] = parser.parse(
                    json_dict['search_id'])

            # Run only in the first iteration (afterwards the objects will
            # not be None any longer)
            if objective_cols is None:
                objective_cols = [str(m['name']) for m in
                                  json_dict['metrics'] if m['objective']]
            if variable_cols is None:
                variable_cols = [str(m['name']) for m in
                                 json_dict['variables']]

    metrics = pandas.DataFrame(metrics).T
    variables = pandas.DataFrame(variables).T

    # Filter to the non-dominated solutions.
    logger.info(f'Performing non-dominated sort on search')
    t0 = time.perf_counter()

    # ndf = list of non-dominated fronts
    # dl = domination list
    # dc = domination count
    # ndr = non-domination ranks
    # USAGE: ndf, dl, dc, ndr = pg.fast......
    non_dom_fronts, *_ = pg.fast_non_dominated_sorting(
        metrics[objective_cols].values)
    tsort = time.perf_counter() - t0
    logger.info(f'Non-dominated sort complete in {tsort:.2f}s')

    indices = non_dom_fronts[0]
    metrics = metrics.iloc[indices, :]

    metrics_and_vars = pandas.concat([metrics, variables], axis=1, join='inner')
    # Remove duplicate rows (if present)
    metrics_and_vars.drop_duplicates(subset=variable_cols, inplace=True)
    # Remove duplicate columns (if present)
    metrics_and_vars = metrics_and_vars.loc[
        :, ~metrics_and_vars.columns.duplicated()]
    # Set 'evaluated_at' column as first column in the dataframe
    first_cols = ['evaluated_at']
    metrics_and_vars = metrics_and_vars[
        [col for col in metrics_and_vars if col in first_cols] +
        [col for col in metrics_and_vars if col not in first_cols]]

    logger.info(f'Extract and sort complete; {len(metrics_and_vars)} ' +
                'non-dominated individuals found for search')
    return metrics_and_vars


def find_archives(files_path):
    ''' Iterator returning files matching given criteria, containing MOEA
        results '''

    result_files = []
    cwd = os.getcwd()
    # Change directory to files_path
    os.chdir(files_path)
    # Finds all files in the current directory (in the result folder)
    for file in glob.glob("*"):
        result_files.append(os.path.join(files_path, file))

    logger.info('Number of result files = {}'.
                format(str(len(result_files))))

    # Change directory back to current working directory
    os.chdir(cwd)
    # Yield a list of result files in each result folder
    yield result_files


def export_nondominated_results(files_path, output_path, metrics_file_name,
                                output_file_type):
    ''' Finds all nondominated results from the collection of files with all
        MOEA results in JSON format, runs a nondominated search on them and
        returns a file with only nondominated solutions in csv.gz format '''

    logger.info('Directory with input files: {}'.format(
                os.path.relpath(files_path, os.curdir)))
    logger.info('Directory where output files will be saved: {}'.format(
                os.path.relpath(output_path, os.curdir)))

    metrics_and_vars = pandas.DataFrame()
    for archive in find_archives(files_path):
        metrics_and_vars = metrics_and_vars.append(
            get_metrics_and_vars(archive))

    # Create folder where output files are to be saved if the folder does
    # not exist
    try:
        os.makedirs(output_path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise

    if output_file_type.lower() == 'csv':
        metrics_and_vars.to_csv(
            os.path.join(output_path, metrics_file_name+'.csv.gz'))
        logger.info('Metrics saved to compressed CSV file {} in {}'.
                    format(metrics_file_name + '.csv', output_path))
    elif output_file_type.lower() == 'h5':
        metrics_and_vars.to_hdf(
            os.path.join(output_path, metrics_file_name+'.h5'), 'metrics')
        logger.info('Metrics saved to HDF file {} in {}'.
                    format(metrics_file_name + '.h5', output_path))
