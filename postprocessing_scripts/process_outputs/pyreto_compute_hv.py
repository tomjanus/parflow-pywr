import sys
import os
import time
import logging
import numpy as np
import pygmo as pg
import concurrent.futures
import pandas

# instantiate logger for logging errors, warnings and other communication
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(stream=sys.stdout)
formatter_long = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
                                    %(message)s')
formatter_short = logging.Formatter('%(message)s')
ch.setFormatter(formatter_short)
logger.addHandler(ch)


def compute_hv_evolution(data, ref_point=None, step=1000, include_final=False):
    """Compute the evolving hypervolume of an array of objectives.

     It is assumed that `data` is a an array of solution objectives with
      each row being a solution and each column an objective. The array
      should be sorted by evaluation time. A `pandas.Series` of hypervolume
      is computed every `step` evaluations.

     This calculation computes the non-dominated set at each chunk of size step
      by taking non-dominated set up to that point and sorting it with the new
      chunk. Once sorted the hypervolume is computed on the non-dominated set
      for up to the current chunk. This approach is more efficient than
      recomputing the non-dominated set over the entire array up to the chunk.

     """
    # reference point list for all objectives
    if ref_point is None:
        # If refernce point not specified assume 1 for each objective
        ref_point = [1 for _ in range(data.shape[1])]
    # set t00 to current time
    t00 = time.perf_counter()
    hv = {}
    # There is no non-dominated individuals to start with
    non_domin_data = None
    # Loop through the data in chunks of size step.
    for i in range(step, len(data), step):
        t0 = time.perf_counter()
        if non_domin_data is None:
            # If there is no existing data take the first chunk
            non_domin_data = data[:i, :]
        else:
            # Otherwise concatenate the existing non-dominated set with the next chunk.
            non_domin_data = np.concatenate([non_domin_data, data[(i-step):i, :]], axis=0)

        assert non_domin_data.shape[1] == data.shape[1]
        # Compute the new non-dominated set
        ndf, *_ = pg.fast_non_dominated_sorting(non_domin_data)
        non_domin_data = non_domin_data[ndf[0], :]

        # Compute the hypervolume
        hv[i] = pg.hypervolume(non_domin_data).compute(ref_point)
        t1 = time.perf_counter() - t0
        t10 = time.perf_counter() - t00  # cumulative
        print(f'Hypervolume at {i:06d} NFE is {hv[i]:.4f}; computed in {t1:.2f}s (total: {t10:.2f}s)')

    if include_final:
        hv[len(data)] = pg.hypervolume(data.values).compute(ref_point)

    # Returns pandas series
    hv = pandas.Series(hv)
    hv.index.name = 'nfe'
    return hv


def compute_hv_all_seeds(data, objective_columns, ref_point=None, step=1000,
                         group_by='search_seed', sort_by='evaluated_at',
                         single_seed=True):
    """Compute the combined hypervolume over a number of seeds.

    It is assumed that `data` is a `pandas.DataFrame` that contains the individuals
     for several searches. This function computes the evolving hypervolume at
     intervals of size `step`. This is done by sorting each search's individuals
     and then interleaving the data from all searches together in chunks of size
     `step`. This merged data is then considered as one search for which the
     evolving hypervolume is computed with a step size each to `step` multiplied
     by the number of searches.

     In case we only have a single seed, i.e. single_seed=True then we will just
     compute the evolving hypervolume on a single seed.

     data - DataFrame with normalized columns
     objective_columns - list with objective names
    """

    # Initialise an empty dictionary to store sorted data
    sorted_data = {}

    if single_seed:
        logger.info(f'Computing hypervolume for all {len(data)} '+
                    'individuals on a single seed.')
        sorted_data = data.sort_values(by=[sort_by])
        merged_data = sorted_data.values[:, 1:]
    else:
        # If multiple seeds then group the data by seed and sort by time
        logger.info(f'Computing hypervolume for all seeds with {len(data)} '+
                    'individuals.')
        # Group by seed
        for seed, seed_individuals in data.groupby(group_by):
            # Sort by evaluated time
            sorted_data[seed] = seed_individuals.sort_values(by=[sort_by])
            if len(seed_individuals) < step:
                raise ValueError(f'All seeds must have done at least {step} ',
                                 'function evaluations.')
        # Merge results from multiple seeds
        merged_data = []
        # Maximum no. of function evaluations across multiple seeds
        max_seed_nfe = max(df.shape[0] for df in sorted_data.values())
        # Carry out the merging operation
        for i in range(step, max_seed_nfe+1, step):
            for seed, df in sorted_data.items():
                if i < df.shape[0]:
                    # This search has more NFE than i so take the next chunk
                    chunk = df[objective_columns].iloc[(i-step):i, :].values
                elif step <= df.shape[0]:
                    # This search has less NFE than i, but more than step
                    # Take the last chunk of size step
                    chunk = df[objective_columns].iloc[-step:, :].values
                else:
                    # This would screw up the calculations
                    raise ValueError(f'All seeds must have done at least {step}'
                                     + ' function evaluations.')
                merged_data.append(chunk)

        # Create interleaved array for hypervolume calculation
        merged_data = np.concatenate(merged_data)

    if single_seed:
        df = compute_hv_evolution(
            merged_data, ref_point=ref_point, step=step)
    else:
        df = compute_hv_evolution(
            merged_data, ref_point=ref_point, step=step)

    # Normalise the index per the number dataframes.
    df.index = df.index / len(sorted_data)
    return df


def compute_hv(file_path, file_name, no_seeds, output_file_name,
               single_seed=True, step_size=10):
    ''' Computes hypervolume from a population of individuals
        Inputs:
            file_path : path to the folder in which the files with MOEA results
                        are stored
            file_name : name of the file that contains MOEA results
            no_seeds : No of seeds used in the MOEA study. The value is used to
                       set max number of workers in ProcessPoolExecutor
            output_file_name: name of the file with the computed hypervolume
            single_seed : a flag indicating whether the data contains
                          multiple seeds or a single seed
            step_size : step increments for which hp is calculated
    '''

    # Specify which extensions are supported to read the data from
    # Currently supports only CSV files (no HDF5)
    extensions_list = [
        '.csv',
        '.csv.gz',
    ]

    # Load data from a file given in file_name in path given in file_path
    # Once a file is found break the loop and continue with loading the results
    # found in that file
    found_files_counter = 0
    iter_counter = 0
    for extension in extensions_list:
        file_with_path = os.path.join(file_path, file_name+extension)
        iter_counter += 1
        try:
            all_individuals = pandas.read_csv(
                file_with_path, parse_dates=True, index_col=0)
            found_files_counter += 1
            # Escape the loop after the first found file (read only one file)
            break
        except FileNotFoundError:
            if found_files_counter == 0 and \
               iter_counter == len(extensions_list):
                raise

    # Create a list of columns which do not contain objectives
    non_objective_columns = [
        'search_seed',
        'search_id',
        'evaluated_at',
    ]

    # Create a list of objective columns
    objective_columns = [c for c in all_individuals if c not in
                         non_objective_columns]

    # Normalise the objectives by their range within each search
    normalised = all_individuals.copy()
    for column in objective_columns:
        if (normalised[column].max() - normalised[column].min()) < 1e-3:
            normalised[column] = (normalised[column] - normalised[column].min()) / \
                                 (normalised[column].min())
            logger.warning(f'Objective "{column}" has zero range ('
                           'i.e. maximum equals minimum).')
        else:
            # Normalizes the values in the column such that their values fall in
            # between zero and one
            normalised[column] = (normalised[column] - normalised[column].min()) / \
                                 (normalised[column].max() -
                                  normalised[column].min())

    # We can use a with statement to ensure threads are cleaned up promptly
    if single_seed:
        logging.info('Computing hypervolume for a single seed with ',
                     f'{len(all_individuals)} individuals.')
        individuals = normalised.sort_values(by=['evaluated_at'])
        hv_data = compute_hv_all_seeds(
            individuals, objective_columns, ref_point=None, step=step_size,
            group_by='search_seed', sort_by='evaluated_at', single_seed=True)

    else:
        with concurrent.futures.ProcessPoolExecutor(no_seeds) as executor:
            # Start the HV calculations; using a key for the seed / name
            future_to_seed = {
                # first future is to compute all seeds
                executor.submit(
                    compute_hv_all_seeds, normalised, objective_columns): 'all'
            }

            for seed, seed_individuals in normalised.groupby('search_seed'):
                logging.info(f'Computing hypervolume for seed {seed} with ',
                             f'{len(all_individuals)} individuals.')
                # Sort by evaluated time
                seed_individuals = seed_individuals.sort_values(by=['evaluated_at'])
                future_to_seed[executor.submit(compute_hv_evolution,
                               seed_individuals[objective_columns].values)] = seed

            hv_data = {}
            for future in concurrent.futures.as_completed(future_to_seed):
                seed = future_to_seed[future]
                try:
                    df = future.result()
                except Exception as exc:
                    logger.error(
                        f'Failed to compute HV for search " with seed: {seed}', exc)
                else:
                    logger.info(
                        f'Successfully computed HV for search " with seed: {seed}')
                    hv_data[seed] = df

    hv_data_df = pandas.DataFrame(hv_data)
    hv_data_df.to_csv(output_file_name+'.csv')
    logger.info("Finished processing search")
