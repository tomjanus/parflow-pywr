import os
import sys
import glob
import gzip
import json
import logging
import errno
from dateutil import parser
import pandas

# from pymongo import MongoClient
# TODO: BSON support
from bson import BSON
import concurrent.futures
from bson.dbref import DBRef
from bson.json_util import loads

# instantiate logger for logging errors, warnings and other communication
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(stream=sys.stdout)
formatter_long = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
                                    %(message)s')
formatter_short = logging.Formatter('%(message)s')
ch.setFormatter(formatter_short)
logger.addHandler(ch)


def get_value(objective):
    ''' Return the value of an objective with appropriate sign depending whether
        it's minimized of maximized '''

    sign = 1 if objective['minimise'] else -1
    return objective['value'] * sign


def get_metrics_and_vars(archive, file_type):
    '''Extracts relevant data (metrics and decision variables) from
       JSON files containing MOEA results and returned from find_archives
       function'''

    # archive is a list of .json files with MOEA results data
    logger.info('Exporting search')
    objective_cols = None
    variable_cols = None
    metrics = {}
    variables = {}
    for i in range(0, len(archive)):
        # Skip search.json files
        if archive[i][len(archive[i]) - 11:] == 'search.json':
            continue

        if file_type == 'bson':
            # TODO: Check this piece of code as it has been written by Andrew
            #       Slaughter to process BSON (compressed JSON) files and has
            #       not been tested. The code is outdated as the JSON code
            #       has been significantly updated
            try:
                bson_file = gzip.open(archive[i], 'rb')
                bson_dict = loads(bson_file.read())
                if objective_cols is None:
                    objective_cols = [str(m['name']) for m in
                                      bson_dict['metrics'] if m['objective']]
            except IOError:
                logger.exception("Unable to read the BSON file. " +
                                 "Trying with JSON")
                continue

        elif file_type == 'json':
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

                # Create a list with objective function names
                if objective_cols is None:
                    objective_cols = [str(m['name']) for m in
                                      json_dict['metrics'] if m['objective']]
                # Create a list with decision variables
                if variable_cols is None:
                    variable_cols = [str(m['name']) for m in
                                     json_dict['variables']]

    metrics = pandas.DataFrame(metrics).T
    variables = pandas.DataFrame(variables).T
    
    # Set 'evaluated_at' column as first column in the dataframe
    first_cols = ['evaluated_at']
    counter = 0
    for data_frame in [metrics, variables]:
        #from pudb import set_trace; set_trace()
        counter += 1
        data_frame = data_frame[
            [col for col in data_frame if col in first_cols] +
            [col for col in data_frame if col not in first_cols]]
        # Don't know how to solve the problem that data_frame is a copy of
        # metrics and variables respectively, instead of being a reference to them
        # Below is an ugly hack
        if counter == 1:
            metrics = data_frame
        elif counter == 2:
            variables = data_frame

    logger.info("Extract complete; " +
                "{} individuals found for search".format(len(metrics)))
    return metrics, variables


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

    logger.info('Number of files found in {} = {}'.
                format(files_path, str(len(result_files))))
    # Change directory back to current working directory
    os.chdir(cwd)
    # Yield a list of result files in each result folder
    yield result_files


def export_all_individuals(input_file_path, output_file_path, file_type,
                           variables_file_name, metrics_file_name,
                           output_file_type):
    ''' Finds all output files from MOEA, parses them and returns
        two separate files: one with metrics/objective functions and the other
        with decision variables '''

    # Define default file format as JSON
    if not file_type.lower() == 'bson' and not file_type.lower() == 'json':
        # Use json as default file type
        file_type = 'json'

    logger.info('File type used for saving results: {}'.format(file_type))
    logger.info('Directory with input files: {}'.format(
                os.path.relpath(input_file_path, os.curdir)))
    logger.info('Directory where output files will be saved: {}'.format(
                os.path.relpath(output_file_path, os.curdir)))

    # Initialise metrics and variables DataFrames
    metrics = pandas.DataFrame()
    variables = pandas.DataFrame()

    # Iterate through files produced by find_archives generator that returns a
    # list of files for each result folder produced in the simulation
    for archive in find_archives(input_file_path):
        # Populate the DataFrame with results
        metrics = metrics.append(
            get_metrics_and_vars(archive, file_type)[0])
        variables = variables.append(
            get_metrics_and_vars(archive, file_type)[1])

    # Create a dataframe with metrics and variables in the same data structure
    metrics_and_vars = pandas.concat([metrics, variables], axis=1, join='inner')
    # Remove duplicate columns (if present)
    metrics_and_vars = metrics_and_vars.loc[
        :, ~metrics_and_vars.columns.duplicated()]

    # Create folder where output files are to be saved if the folder does
    # not exist
    try:
        os.makedirs(output_file_path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise

    # Convert the metrics DataFrame to csv or hdf (h5)
    if output_file_type.lower() == 'csv':
        metrics.to_csv(os.path.join(output_file_path, metrics_file_name +
                                    '.csv'))
        variables.to_csv(os.path.join(output_file_path,
                                      variables_file_name + '.csv'))
        metrics_and_vars.to_csv(os.path.join(output_file_path,
                                      'metrics_and_vars' + '.csv'))
        logger.info('Metrics and Variables exported to CSV files {} and {} in {}'.
                    format(metrics_file_name + '.csv', variables_file_name +
                           '.csv', output_file_path))
    elif output_file_type.lower() == 'h5':
        metrics.to_hdf(os.path.join(
            output_file_path, metrics_file_name + '.h5'), 'metrics')
        variables.to_hdf(os.path.join(output_file_path, variables_file_name
                         + '.h5'), 'variables')
        metrics_and_vars.to_hdf(os.path.join(output_file_path, 'metrics_and_vars'
                         + '.h5'), 'metrics_and_vars')
        logger.info('Metrics and Variables exported to HDF files {} and {} in {}'.
                    format(metrics_file_name + '.h5', variables_file_name +
                           '.h5', output_file_path))
