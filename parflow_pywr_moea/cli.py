""" This file defines command line interface using Python's module click
    which is used to run the integrated PyWr / Parflow model

    Functions:
    ---------------------------------
    render_model(filename, **data): populates Pywr .json file with data using
                                    jinja2 templating module

    Usage (in command line environment):
    ---------------------------------

"""

# TODO  Modify logger reporting functions so that lazy formatting is used

from __future__ import with_statement
import sys
import os
import json
import logging
import click
import tables
import pandas
import platypus
import random
import requests
import ast
import numpy as np
from matplotlib import pyplot as plt
from jinja2 import Environment, BaseLoader
from pathlib import Path
from pywr.model import Model
from pywr.recorders import TablesRecorder, CSVRecorder
from pywr.recorders import NumpyArrayNodeRecorder, NumpyArrayParameterRecorder, HydropowerRecorder
from pywr.recorders.progress import ProgressRecorder
from .moea import platypus_main, platypus_main_mpi
from .parflow.pywr_parameters import *
from .parflow.pywr_recorders import *
from .recorders import *
from .parflow_file_read_scripts import pf_read as pf_read
from .parflow.manager import ParflowRunner
from multiprocessing import Pool

# Instantiate the top level logger object where __name__ is the module's name
# and here __name__ == cli
logger = logging.getLogger(__name__)


# Define a function that creates (renders) a PyWr json model using data
# with Jinja2
def render_model(filename, **data):
    """ Populate PyWr model .json file with data
        Return a dictionary containing rendered json string defining the
        Pywr model """
    with open(filename) as file_handle:
        template_data = file_handle.read()

    template = Environment(loader=BaseLoader()).from_string(template_data)
    rendered = template.render(**data)
    #from
    print("Rendered Pywr model: " + rendered)
    # Return a dictionary from the rendered json string
    return json.loads(rendered)


# Command line interface
@click.group()
@click.option('-v', '--verbose', is_flag=True)
def cli(verbose):
    pywr_logger = logging.getLogger('pywr')
    root_logger = logging.getLogger(__name__.split('.')[0])

    ch = logging.StreamHandler(stream=sys.stdout)

    if verbose:
        root_logger.setLevel(logging.DEBUG)
        pywr_logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
        pywr_logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
                                   %(message)s')
    ch.setFormatter(formatter)

    root_logger.addHandler(ch)
    pywr_logger.addHandler(ch)


# It is assumed that folder-name exists - otherwise an error is produced
@cli.command()
@click.argument('folder-name', type=click.Path(exists=True, dir_okay=True,
                                               file_okay=False))
@click.argument('config-file', type=click.Path(exists=True)) #type=click.File('rb'))
@click.option('-r', '--result_file', type=str, default='results_json')
@click.option('-s', '--start', type=int, default=365)
@click.option('-f', '--finish', type=int, default=365)
def read_parflow_results(folder_name, config_file, result_file, start, finish):
    """Reads variables saved by Parflow to a local folder"""

    # Number of days to be used from the simulation time-series
    num_days = abs(finish - start) + 1
    list_of_days = list(range(start, finish + 1, 1))

    # Initialise the dictionary to which we will be saving all results
    # and save the time-range information
    results_dict = {'time-range': {'start': start, 'finish': finish}}

    # Create empty lists for ids (nondominated solutions) and variables
    # to be read from Parflow outputs files and saved to a json file
    list_of_ids = []
    list_of_variables = []

    # Process the results passed into the code in the json config file
    try:
        with open(config_file) as f:
            config_dict = json.load(f)
        # Read ids and variables from the dictionary
        list_of_variables = config_dict['variables']
        list_of_ids = config_dict['ids']
    except EnvironmentError: # parent of IOError, OSError
        logger.warning('Reading config json file was not successful')
        logger.warning('Nothing to extract')

    logger.info('Extracting variables: {}'.format(list_of_variables))
    logger.info('Extracting following solution IDs: {}'.format(list_of_ids))
    logger.info('Extracting {} days from day {} to day {}'.format(
        num_days, start, finish))

    # TODO: Parallelise the code with multiprocessing

    # We will be extracting daily data (hard-coded for now, the time-step
    # depends on the setting in Parflow in the tlc file.)

    # Loop over the solutions (IDs)
    for id in list_of_ids:
        # Specify the subfolder storing files for result with id=id
        subfolder_name = 'id_' + str(id)
        # Loop over all days included in the time-series to extract
        for day in list_of_days:
            # The files are generated with 5 places for numbers in Parflow
            file_suffix = '.' + str(day).zfill(5) + '.pfb'
            # Loop over all variables to be extracted from the output files
            for var_name in list_of_variables:
                # File names depend on the name of the .tcl file describing
                # the Parflow model. In our case it's called profile.tcl, hence
                # they all start with 'profile'
                if var_name == 'wtd':
                    # Depth to water table [m]
                    file_name_no_suffix = 'profile.out.press'
                    slice_arg = np.index_exp[9,0,:]
                    multiplier = -1.0
                    const_bias = 0.0
                elif var_name == 'sat':
                    # Soil saturation [-] range 0 to 1
                    file_name_no_suffix = 'profile.out.satur'
                    slice_arg = np.index_exp[9,0,:]
                    multiplier = 1.0
                    const_bias = 0.0
                elif var_name == 't_grnd':
                    # Ground surface temperature [degC]
                    file_name_no_suffix = 'profile.out.t_grnd'
                    slice_arg = np.index_exp[:]
                    multiplier = 1.0
                    const_bias = -273.15
                elif var_name == 'soil_grnd':
                    # Ground heat flux [W/m2]
                    # if > 0 then from surface into ground
                    # if < 0 then from ground into the surface
                    file_name_no_suffix = 'profile.out.eflx_soil_grnd'
                    slice_arg = np.index_exp[:]
                    multiplier = 1.0
                    const_bias = 0.0
                elif var_name == 'lat_heat':
                    # Latent heat flux total [W/m2]
                    # Loss of energy from the surface due to evaporation
                    # if > 0 then from surface into atmosphere
                    # if < 0 then from atomosphere into surface
                    file_name_no_suffix = 'profile.out.eflx_lh_tot'
                    slice_arg = np.index_exp[:]
                    multiplier = 1.0
                    const_bias = 0.0
                elif var_name == 'sh_tot':
                    # Sensible heat flux total [W/m2]
                    # Loss of energy by thesurface by heat transfer to the atomosphere
                    # if > 0 then from surface into atmosphere
                    # if < 0 then from atmosphere into the surface
                    file_name_no_suffix = 'profile.out.eflx_sh_tot'
                    slice_arg = np.index_exp[:]
                    multiplier = 1.0
                    const_bias = 0.0
                elif var_name == 'lwrad_out':
                    # Outgoing long-wave radiation [W/m2]
                    # if > 0 then away from surface into atomosphere
                    # if < 0 then into the surface from atmosphere
                    file_name_no_suffix = 'profile.out.eflx_lwrad_out'
                    slice_arg = np.index_exp[:]
                    multiplier = 1.0
                    const_bias = 0
                elif var_name == 'evap_tot':
                    # Total evaporation [mm/d]
                    file_name_no_suffix = 'profile.out.qflx_evap_tot'
                    slice_arg = np.index_exp[:]
                    multiplier = 3600 * 24 # conversion from second to day
                    const_bias = 0
                elif var_name == 'evap_veg':
                    # Evaporation by vegetation [mm/d]
                    file_name_no_suffix = 'profile.out.qflx_evap_veg'
                    slice_arg = np.index_exp[:]
                    multiplier = 3600 * 24 # conversion from second to day
                    const_bias = 0
                elif var_name == 'evap_grnd':
                    # Evaporation from ground without condensation [mm/d]
                    file_name_no_suffix = 'profile.out.qflx_evap_grnd'
                    slice_arg = np.index_exp[:]
                    multiplier = 3600 * 24 # conversion from second to day
                    const_bias = 0
                elif var_name == 'evap_soi':
                    # Evaporation from soil [mm/d]
                    file_name_no_suffix = 'profile.out.qflx_evap_soi'
                    slice_arg = np.index_exp[:]
                    multiplier = 3600 * 24 # conversion from second to day
                    const_bias = 0
                elif var_name == 'tran_veg':
                    # Vegetation transpiration [mm/d]
                    file_name_no_suffix = 'profile.out.qflx_tran_veg'
                    slice_arg = np.index_exp[:]
                    multiplier = 3600 * 24 # conversion from second to day
                    const_bias = 0
                else:
                    file_name_no_suffix = ''
                    slice_arg = np.index_exp[:]
                    multiplier = []
                    const_bias = 0.0

                file_name = file_name_no_suffix + file_suffix

                try:
                    imported_data = pf_read.read(os.path.join(
                                folder_name, subfolder_name, file_name)) * \
                                    multiplier + const_bias
                    # Try slicing the data read from the file
                    try:
                        # Slice and convert to list for serialisation
                        # numpy arrays cannot be serialised
                        imported_data = np.squeeze(
                            imported_data[slice_arg]).tolist()
                    except NameError:
                        pass

                    # Write to results_dict here
                    if id not in results_dict.keys():
                        results_dict[id] = {}
                    else:
                        if var_name in results_dict[id].keys():
                            results_dict[id][var_name].append(imported_data)
                        else:
                            results_dict[id][var_name] = [imported_data]

                except FileNotFoundError:
                    logging.error('File {} not found'.format(file_name))

    results_json_file_name = result_file
    with open(os.path.join('./', results_json_file_name) + '.json',
              'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(results_dict, ensure_ascii=False, indent=4))


@cli.command()
@click.argument('json-config-file', type=click.Path(exists=True))
@click.argument('results-csv-file', type=click.Path(exists=True))
def run_parflow_batch(json_config_file, results_csv_file):
    # Read json config file and extract result ids and list of variables
    # representing landuse allocations in the 1D transsect

    # Define a nested function that creates a landuse allocation dictionary
    # for use in ParflowRunner's create_environment method
    # It's a copy of a class method with some modifications
    # The method could potentially be reused in this code but this is
    # a fast simple hack for the time-being
    def sparse_fractional_coverage(vec_landuse, land_use_classes):
        values = vec_landuse
        num_variable_tiles = len(values)
        """ Returns a list with coverage values for each tile """
        coverage = []
        print("Number of land surface tiles: "
              + str(num_variable_tiles))
        print("Number of land use classes: "
              + str(len(land_use_classes)))
        for i in range(num_variable_tiles):
            land_use_class = land_use_classes[values[i]]
            print("Allocated land class for tile {}: {}".
                  format(i+1, land_use_class))
            land_use_class -= 1  # Use zero based indexing for writing the files
            coverage.append({land_use_class: 1.0})
        return coverage

    # Read json config file and extract the required parameters
    try:
        with open(json_config_file) as f:
            config_dict = json.load(f)
        # Read ids and variables from the dictionary
        list_of_landuse_cols = config_dict['landuse_vec']
        list_of_ids = config_dict['ids']
        landuse_classes = config_dict['land_use_classes']
        logger.info('The following ids will be run {}'.format(list_of_ids))
        logger.info(
            'The vector of variables representing landuse allocation: {}'
            .format(list_of_landuse_cols))
        logger.info('Landuse classes: {}'.format(landuse_classes))
    except EnvironmentError: # parent of IOError, OSError
        logger.warning('Reading config json file was not successful')
        logger.warning('No simulations to run')

    # Read the csv file with all nondominated solutions and create a dataframe
    nondom_results_data = pandas.read_csv(results_csv_file)
    # Set index to be equal to simulation/solution IDs
    nondom_results_data.set_index('Unnamed: 0', inplace=True)

    # Initialise Parflow runner object
    parflow_obj = ParflowRunner(
        input_script='profile',
        run_args=[],
        base_model_directory='profile1_batch',
        work_directory='parflow_batch_jobs',
        vegetation_coverage_filename='drv_vegm.dat')

    # TODO: Parallelize this code - not done due to problems with pickling
    # some variables - requries some manual pickling / depickling
    def run_parflow_jobs(list_of_ids):
        for sim_id in list_of_ids:
            try:
                vec_landuse = nondom_results_data.loc[
                    sim_id, list_of_landuse_cols].to_list()
            except KeyError:
                logger.error("Cannot find ID: {}. Skipping...".format(sim_id))
                continue

            fractional_coverage = sparse_fractional_coverage(
                vec_landuse, landuse_classes)

            # Creat simulation (folder) name
            sim_name = 'id_' + str(sim_id)

            # Create a new local environment and run parflow
            try:
                parflow_obj.create_environment(sim_name, fractional_coverage)
                parflow_obj.run(sim_name)
            except OSError:
                logger.error(
                    "Folder {} already exists. Skipping...".format(sim_name))
                continue

        return -1

    run_parflow_jobs(list_of_ids)
    #pool = Pool()
    #pool.map(run_parflow_jobs, list_of_ids)

@cli.command()
@click.argument('input-json-file', type=click.Path(exists=True))
@click.option('-bo', '--binout', type=click.Path(), default="outputs/test.h5")
@click.option('-to', '--textout', type=click.Path(),
              default="outputs/test.csv")
@click.option('--result-dump', is_flag=True)
def run(input_json_file, binout, textout, result_dump):
    """ Runs PyWr model using rendered Pywr model from json file.
        Saves results in the provided output file """
    # Check whether folders to save binout and textout files exist
    # (using e.g. Path(binout).resolve().parent will produce absolute path)
    dir_binout = Path(binout).parent
    dir_textout = Path(textout).parent
    # from pudb import set_trace; set_trace()
    if not os.path.exists(dir_binout):
        os.makedirs(dir_binout)
    if not os.path.exists(dir_textout):
        os.makedirs(dir_textout)
    # Create a dictionary with json file containing rendered pywr model
    data = render_model(input_json_file)
    # Load data into Pywr model
    logger.info('Loading model from file: "{}"'.format(input_json_file))
    model = Model.load(data)
    base, _ = os.path.splitext(input_json_file)

    # Create recorders for recording data in pywr's model nodes
    TablesRecorder(model, binout,
                   parameters=[p for p in model.parameters if
                               p.name is not None])
    CSVRecorder(model, textout)

    # Execute the Pywr model
    logger.info('Starting model run.')
    ret = model.run()
    logger.info(ret)

    # Save the metrics
    save_metrics_to_excel = True

    if save_metrics_to_excel:
        metrics = {}
        metrics_aggregated = {}
        for rec in model.recorders:
            try:
                metrics[rec.name] = np.array(rec.values())
                metrics_aggregated[rec.name] = np.array(rec.aggregated_value())
            except NotImplementedError:
                pass
        metrics = pandas.DataFrame(metrics).T
        metrics_aggregated = pandas.Series(metrics_aggregated)

        writer = pandas.ExcelWriter(f"{base}_metrics.xlsx")
        metrics.to_excel(writer, 'scenarios')
        metrics_aggregated.to_excel(writer, 'aggregated')
        writer.save()

    # Save all results from all recorders if result_dump flag set to true
    # from pudb import set_trace; set_trace()
    if result_dump:
        # Write dataframes

        # ERROR: dumping model to dataframe raises ModelView Error

        store = pandas.HDFStore(f"{base}_dataframes.h5", mode='w')
        for rec in model.recorders:
            if hasattr(rec, 'to_dataframe'):
                df = rec.to_dataframe()
                store[rec.name] = df

            try:
                values = np.array(rec.values())
            except NotImplementedError:
                pass
            else:
                store[f'{rec.name}_values'] = pandas.Series(values)

        store.close()

        # Old part of the code
        model_df = model.to_dataframe()
        base, _ = os.path.splitext(binout)
        model_df.to_csv(base + '_allrecorders.csv')


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True),
              default="outputs/test.h5")
@click.option('-n', '--nodes_list', default=[
              'supply1', 'city1', 'reservoir1', 'turbine1', 'city1_release'])
def plot(input_file, nodes_list):
    # Read the hdf5 file
    with tables.open_file(input_file) as h5:
        # Get the time vector and convert to pandas dataframe
        time = h5.get_node("/time")
        dates = pandas.to_datetime({
            'year': time.col('year'), 'month': time.col('month'),
            'day': time.col('day')
        })
        data = {}
        for node in h5.walk_nodes("/", "CArray"):
            if node._v_name in nodes_list:
                data[node._v_name] = pandas.DataFrame(node[:, 0], index=dates)

    # Plot the simulation results
    # You can use vitables to visualise the data in hdf5 files
    fig, axarr = plt.subplots(nrows=len(data), sharex=True, figsize=(12, 8))
    for ax, (name, df) in zip(axarr, data.items()):
        df.plot(ax=ax)
        ax.set_ylabel(name)

    base, _ = os.path.splitext(input_file)
    fig.savefig(base + '.png')
    plt.show()


@cli.command()
@click.argument('name', type=str)
@click.option('--mpi/--no-mpi', default=False)
@click.option('-a', '--algorithm', type=click.Choice(
              ['NSGAII', 'NSGAIII', 'EpsMOEA', 'EpsNSGAII']), default='NSGAII')
@click.option('-ps', '--pop-size', type=int, default=50)
@click.option('-s', '--seed', type=int, default=None)
#@click.option('-nt', '--no-threads', type=int, default=4)
@click.option('-p', '--num-cpus', type=int, default=4)
@click.option('-ne', '--no-evals', type=int, default=1)
#@click.option('-n', '--max-nfe', type=int, default=1000)
@click.option('-e', '--epsilons', multiple=True, type=float, default=(0.05, ))
@click.option('--divisions-inner', type=int, default=1)
@click.option('--divisions-outer', type=int, default=5)
@click.option('-h', '--mongo-host', type=str, default=None)
@click.option('-d', '--mongo-db', type=str, default=None)
@click.option('-df', '--mongo-drop-db', is_flag=True)
@click.option('-w', '--work-directory',
              type=click.Path(dir_okay=True,
                              file_okay=False), default=None)
@click.option('--variable-control-curve', is_flag=True)
@click.option('-i', '--input-json-file', type=click.Path(exists=True))
def search(name, mpi, algorithm, pop_size, seed, num_cpus, no_evals, epsilons,
           divisions_inner, divisions_outer, mongo_host, mongo_db,
           mongo_drop_db, work_directory, variable_control_curve,
           input_json_file):
    """Perform MOEA runs with the integrated PyWR Parflow model"""
    logger.info('Parflow work directory: {}'.format(work_directory))
    logger.info('Variable control curve: {}'.format(variable_control_curve))
    logger.info('Rendering model in file: "{}"'.format(input_json_file))
    data = render_model(input_json_file,
                        work_directory=work_directory,
                        variable_control_curve=variable_control_curve
                        )
    search_tags = [
        '{}variable-control-curve'.format(''
                                          if variable_control_curve else 'no-'),
    ]

    # Initialise variables depending on the chosen MOEA algorithm
    if algorithm == 'NSGAII':
        algorithm_class = platypus.NSGAII
        algorithm_kwargs = {'population_size': pop_size}
    elif algorithm == 'NSGAIII':
        algorithm_class = platypus.NSGAIII
        algorithm_kwargs = {
            'divisions_outer': divisions_outer,
            'divisions_inner': divisions_inner}
    elif algorithm == 'EpsMOEA':
        algorithm_class = platypus.EpsMOEA
        algorithm_kwargs = {
            'population_size': pop_size, 'epsilons': epsilons}
    elif algorithm == 'EpsNSGAII':
        algorithm_class = platypus.EpsMOEA
        algorithm_kwargs = {
            'population_size': pop_size, 'epsilons': epsilons}
    else:
        raise RuntimeError('Algorithm "{}" not supported.'.format(algorithm))

    # Define seed for random number generation
    if seed is None:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)

    logger.info('Starting model search...')

    if mpi:
        platypus_main_mpi(name, data, seed, algorithm_class,
                          mongo_url=mongo_host, mongo_db=mongo_db,
                          drop=mongo_drop_db, extra_tags=search_tags,
                          no_evals=no_evals, **algorithm_kwargs)
    else:
        platypus_main(name, data, seed, algorithm_class,
                      mongo_url=mongo_host, mongo_db=mongo_db,
                      drop=mongo_drop_db, extra_tags=search_tags,
                      no_evals=no_evals, no_threads=num_cpus,
                      **algorithm_kwargs)


@cli.command('import-results')
@click.argument('directory', type=click.Path(exists=True, dir_okay=True,
                                             file_okay=False))
@click.argument('mongo-host', type=str)
@click.argument('mongo-db', type=str)
@click.option('--mongo-drop-db', is_flag=True)
def import_results(directory, mongo_host, mongo_db, mongo_drop_db):
    """Import MOEA search results from a specified directory that containts
       file 'search.json' """
    print(mongo_host, mongo_db)

    with open(os.path.join(directory, 'search.json')) as fh:
        search_data = json.load(fh)

        response = requests.post('{}/{}/searches'.format(mongo_host, mongo_db),
                                 json=search_data)
        print(response)
        search_id = response.json()['_id']['$oid']

    insert_url = '{}/{}/searches/{}/individuals'.format(mongo_host, mongo_db,
                                                        search_id)
    for fn in os.listdir(directory):
        base, ext = os.path.splitext(fn)
        if base == 'search' or ext != '.json':
            continue

        with open(os.path.join(directory, fn)) as fh:
            individual_data = json.load(fh)

            # TODO edit the main recorder to write using msgpack
            for metric in individual_data['metrics']:
                try:
                    metric.pop('dataframe')
                except KeyError:
                    pass

            response = requests.post(insert_url, json=individual_data)
            if response.status_code != 200:
                logger.error('Failed to save individual to PyretoDB. \
                              Status code: {}'.format(response.status_code))
            else:
                response_data = response.json()
                if 'error' in response_data:
                    logger.error('Failed to save individual to PyretoDB. \
                         Response error: {}'.format(response_data['error']))
                else:
                    logger.info('Save complete!')


def start_cli():
    # Run cli with environment variables (if present)
    # e.g. export PARFLOW_PYWR_RUN_OUTPUT=outputs/file.h5
    #      export PARFLOW_PYWR_SEARCH_MONGO_DROP_DB=false
    #      export PARFLOW_PYWR_SEARCH_MPI=false
    cli(auto_envvar_prefix='PARFLOW_PYWR')
