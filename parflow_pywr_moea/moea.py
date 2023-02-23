""" Defines PlatypusPyretoDB wrapper class inheriting from PlatypusWrapper
    class and various functions for performing MOEA runs """

import sys
import os
import uuid
import logging
import json
import datetime
import requests
import platypus
import mongoengine as me
from pyreto_db import documents
from .recorders import PyretoDBRequestRecorder, PyretoDBDirectRecorder, \
                       PyretoDBJSONRecorder
from pywr.optimisation.platypus import PlatypusWrapper
from platypus.core import nondominated_sort
from platypus.core import nondominated

# instantiate logger for logging errors, warnings and other communication
logger = logging.getLogger(__name__)


class PlatypusPyretoDBWrapper(PlatypusWrapper):
    """ Wrapper Class for Platypus Wrapper adding communication (Recorder)
        capabilities
        Methods:
        ------------------------------------
        customise_model(self,model): instantiatetes a recorder based on the
                                     type of protocol specified
    """
    def __init__(self, *args, **kwargs):
        self.search_id = kwargs.pop('search_id')
        # define how optimization results are stored (mongodb, http or files)
        self.pyreto_url = kwargs.pop('url', None)
        self.pyreto_db = kwargs.pop('db', None)
        super().__init__(*args, **kwargs)

    def customise_model(self, model):
        """ Instantiates a PyWr recorder based on the value of self.pyreto_url
        """
        if self.pyreto_url is not None:
            protocol = self.pyreto_url.split(':')[0]
            # Instantiate a recorder based on the type of url provided
            # Results can be written into: a mongodb database, into the server
            # using http, or into files
            if protocol == 'mongodb':
                PyretoDBDirectRecorder(model, search_id=self.search_id,
                                       url=self.pyreto_url, db=self.pyreto_db)
            elif protocol.startswith('http'):
                PyretoDBRequestRecorder(model, search_id=self.search_id,
                                        url=self.pyreto_url, db=self.pyreto_db)
            elif protocol.startswith('file'):
                PyretoDBJSONRecorder(model, search_id=self.search_id,
                                     url=self.pyreto_url, db=self.pyreto_db)
            else:
                raise ValueError(
                    'Protocol "{}" not supported.'.format(protocol))


def create_new_search(**kwargs):
    """ Instantiates an environment for performing MOEA runs and returns
        search_id
        Calls: a private module function _create_new_search_direct or
               _create_new_search_request or _create_new_search_json
               depending on the type of protocol used """
    url = kwargs.get('url')
    protocol = url.split(':')[0]
    if protocol == 'mongodb':
        search_id = _create_new_search_direct(**kwargs)
    elif protocol.startswith('http'):
        search_id = _create_new_search_request(**kwargs)
    elif protocol.startswith('file'):
        search_id = _create_new_search_json(**kwargs)
    elif protocol.startswith('localhost'):
        search_id = _create_new_search_request(**kwargs)
    else:
        raise ValueError('Protocol "{}" not supported.'.format(protocol))

    return search_id


def _create_new_search_direct(drop=True, **kwargs):
    """ Saves search results in **kwargs to a MongoDB database """
    url = kwargs.pop('url')
    db = kwargs.pop('db')
    client = me.connect(host=url, db=db)
    # If True, remove the database db
    if drop:
        client.drop_database(db)
    # If no key 'started_at' in the dictionary kwargs, set 'started_at' to
    # current time and date
    if 'started_at' not in kwargs:
        kwargs['started_at'] = datetime.datetime.now()

    # Instantiates Search class object in documents within pyreto_db package
    search = documents.Search(**kwargs)
    # FIXME: No save() method in the Search class
    search.save()
    client.close()
    return search.id


def _create_new_search_request(**kwargs):
    """ Saves search results in **kwargs to a JSON file over via HTTP
        using requests Python library """
    url = kwargs.pop('url')
    db = kwargs.pop('db')
    drop = kwargs.pop('drop', None)
    # If no key 'started_at' in the dictionary kwargs, set 'started_at' to
    # current time and date
    if 'started_at' not in kwargs:
        kwargs['started_at'] = datetime.datetime.now().isoformat()

    search = dict(**kwargs)
    response = requests.post('{}/{}/searches'.format(url, db), json=search)
    return response.json()['_id']['$oid']


def _create_new_search_json(**kwargs):
    """ Saves search results in **kwargs to a JSON file stored locally """
    url = kwargs.pop('url')
    db = kwargs.pop('db')
    drop = kwargs.pop('drop', None)
    # If no key 'started_at' in the dictionary kwargs, set 'started_at' to
    # current time and date
    if 'started_at' not in kwargs:
        kwargs['started_at'] = datetime.datetime.now().isoformat()

    search_id = uuid.uuid4().hex
    print(url.split('://', 1)[1])  # Line added by Andrew Slaughter
    fn = os.path.join(url.split('://', 1)[1], db, search_id, 'search.json')
    # Search results
    search = dict(**kwargs)
    # Make sure directory exists
    os.makedirs(os.path.split(fn)[0], exist_ok=True)
    with open(fn, mode='w') as fh:
        json.dump(search, fh)

    return search_id


def platypus_main(search_name, data, seed, algorithm_class,
                  mongo_url=None, mongo_db=None, drop=False, extra_tags=None,
                  no_evals=1, no_threads=4, **algorithm_kwargs):
    """ Function to run MOEA without MPI
        data - dictionary containing json data describing Pywr model
    """
    # from pudb import set_trace; set_trace()
    #for key, value in algorithm_kwargs.items():
    #    print(key, value)

    # If the url to a Mongo database is provided
    if mongo_url is not None:
        tags = ['platypus', algorithm_class.__name__]
        if extra_tags is not None:
            tags.extend(extra_tags)
        print("Mongo host is :" + mongo_url)  # Line added by Andrew Slaughter
        search_id = create_new_search(
            name=search_name, algorithm=algorithm_class.__name__,
            tags=tags, drop=drop, url=mongo_url, db=mongo_db)
        logger.info('Created a new search in the pyreto database with id: \
                    {}'.format(search_id))
    else:
        search_id = None

    # Instantiate PlatypusPyretoDBWrapper class object
    wrapper = PlatypusPyretoDBWrapper(
        data, search_id=search_id, url=mongo_url, db=mongo_db)

    # Originally, population size of 47 (hard-coded) and 10000 evaluations (hard-coded)
    # Old piece of code: with platypus.MapEvaluator() as evaluator:
    # Changed to 2 and 1000 (Andrew)
    evaluator_class = platypus.ProcessPoolEvaluator
    evaluator_args = (no_threads,)
    logger.info('Running with multiprocessing on {} cores... '.format(
                no_threads))
    with evaluator_class(*evaluator_args) as evaluator:
        algorithm = algorithm_class(
            wrapper.problem, evaluator=evaluator, **algorithm_kwargs,
            seed=seed)
        algorithm.run(no_evals)

        # Calculate final nondominated results and objectives and save them
        # into a text file
        nondom_sol = nondominated(algorithm.result)
        nondom_sol_list = []
        for i in nondom_sol:
            nondom_sol_list.append(i.variables)
        nondom_obj = (s.objectives[:] for s in nondom_sol)
        # save nondom_obj list to json file
        final_json_file = 'nondom_final_' + str(search_name) + '.json'
        with open(final_json_file, 'w') as f:
            json.dump({
                "nondom sol": list(nondom_sol_list),
                "nondom obj": list(nondom_obj)
            }, f)


def platypus_main_mpi(search_name, data, seed, algorithm_class,
                      mongo_url=None, mongo_db=None,
                      drop=False, extra_tags=None, no_evals=1,
                      **algorithm_kwargs):
    """ Function to run MOEA with MPI
        data - dictionary containing json data describing Pywr model
    """
    from platypus.mpipool import MPIPool

    # Initialize the MPI pool (of parallel processes)
    pool = MPIPool()
    # Parallel computing using distributed memory and processes with MPI
    evaluator_class = platypus.PoolEvaluator
    evaluator_args = (pool,)

    if pool.is_master():
        if mongo_url is not None:
            tags = ['platypus', algorithm_class.__name__]
            if extra_tags is not None:
                tags.extend(extra_tags)
            print("Mongo host is :" + mongo_url)
            search_id = create_new_search(
                name=search_name, algorithm=algorithm_class.__name__,
                tags=tags, drop=drop, url=mongo_url, db=mongo_db)
            logger.info('Created a new search in the pyreto database with id: \
                        {}'.format(search_id))
        else:
            search_id = uuid.uuid4().hex
    else:
        search_id = None

    # Broadcast the search id to all nodes
    search_id = pool.bcast(search_id, root=0)

    # Instantiate PlatypusPyretoDBWrapper class object
    wrapper = PlatypusPyretoDBWrapper(data, search_id=search_id,
                                      url=mongo_url, db=mongo_db)

    # only run the algorithm on the master process
    if not pool.is_master():
        pool.wait()
        sys.exit(0)

    with evaluator_class(*evaluator_args) as evaluator:
        algorithm = algorithm_class(
            wrapper.problem, evaluator=evaluator, **algorithm_kwargs,
            seed=seed)
        algorithm.run(no_evals)

        # Calculate final nondominated results and objectives and save them
        # into a text file
        nondom_sol = nondominated(algorithm.result)
        nondom_sol_list = []
        for i in nondom_sol:
            nondom_sol_list.append(i.variables)
        nondom_obj = (s.objectives[:] for s in nondom_sol)
        # save nondom_obj list to json file
        final_json_file = 'nondom_final_' + str(search_name) + '.json'
        with open(final_json_file, 'w') as f:
            json.dump({
                "nondom sol": list(nondom_sol_list),
                "nondom obj": list(nondom_obj)
            }, f)

    pool.close()
