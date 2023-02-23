""" This module provides classes that are used to create recorder objects
    to record Pywr outputs to files/databases

    Instantiates/return a reference to a LOGGER object with name specified as
    __name__, i.e. module's name
"""
import logging
import json
import uuid
import os
import datetime
import requests
from pywr.recorders import Recorder
from pyreto_db import documents
import mongoengine as me

# instantiate logger for logging errors, warnings and other communication
logger = logging.getLogger(__name__)


class PyretoDBDirectRecorder(Recorder):
    """ """
    def __init__(self, *args, **kwargs):
        self.search_id = kwargs.pop('search_id')
        self.url = kwargs.pop('url')
        self.db = kwargs.pop('db')
        super().__init__(*args, **kwargs)
        self.created_at = None

        # Make this recorder dependent on all existing components
        for component in self.model.components:
            if component is not self:
                self.children.add(component)

    @property
    def connection_kwargs(self):
        """ """
        return {
            'host': self.url,
            'db': self.db
        }

    def _generate_variable_documents(self):
        """ """
        for variable in self.model.variables:

            if variable.double_size > 0:
                upper = variable.get_double_upper_bounds()
                lower = variable.get_double_lower_bounds()
                values = variable.get_double_variables()
                for i in range(variable.double_size):
                    yield documents.Variable(
                        name='{}[d{}]'.format(variable.name, i),
                        value=values[i], upper_bounds=upper[i],
                        lower_bounds=lower[i])

            if variable.integer_size > 0:
                upper = variable.get_integer_upper_bounds()
                lower = variable.get_integer_lower_bounds()
                values = variable.get_integer_variables()
                for i in range(variable.integer_size):
                    yield documents.Variable(
                        name='{}[i{}]'.format(variable.name, i),
                        value=values[i], upper_bounds=upper[i],
                        lower_bounds=lower[i])

    def _generate_metric_documents(self):
        """ """
        for recorder in self.model.recorders:

            try:
                value = recorder.aggregated_value()
            except NotImplementedError:
                value = None

            try:
                df = recorder.to_dataframe()
            except AttributeError:
                df = None

            if value is not None or df is not None:
                yield documents.Metric(
                    name=recorder.name, value=value, dataframe=df,
                    objective=recorder.is_objective is not None,
                    constraint=recorder.is_constraint,
                    minimise=recorder.is_objective == 'minimise')

    def reset(self):
        """ """
        self.created_at = None

    def before(self):
        """ """
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    def finish(self):
        """ """
        import time
        logger.info('Saving individual to MongoDB.')
        t0 = time.time()

        # Connect to the database
        client = me.connect(**self.connection_kwargs)
        search = documents.Search.objects(id=self.search_id).first()

        evaluated_at = datetime.datetime.now()
        # TODO runtime statistics
        individual = documents.Individual(
            variables=list(self._generate_variable_documents()),
            metrics=list(self._generate_metric_documents()),
            created_at=self.created_at,
            evaluated_at=evaluated_at,
            search=search,
        )

        individual.save()
        logger.info('Save complete in {:.2f}s'.format(time.time() - t0))
        client.close()


# register the name so it can be loaded from JSON
PyretoDBDirectRecorder.register()


class PyretoDBRequestRecorder(Recorder):
    """ """
    def __init__(self, *args, **kwargs):
        self.search_id = kwargs.pop('search_id')
        self.url = kwargs.pop('url')
        self.db = kwargs.pop('db')
        super().__init__(*args, **kwargs)
        self.created_at = None

        # Make this recorder dependent on all existing components
        for component in self.model.components:
            if component is not self:
                self.children.add(component)

    def _generate_variable_documents(self):
        """ """
        for variable in self.model.variables:

            if variable.double_size > 0:
                upper = variable.get_double_upper_bounds()
                lower = variable.get_double_lower_bounds()
                values = variable.get_double_variables()
                for i in range(variable.double_size):
                    yield dict(name='{}[d{}]'.format(variable.name, i),
                               value=float(values[i]),
                               upper_bounds=float(upper[i]),
                               lower_bounds=float(lower[i]))

            if variable.integer_size > 0:
                upper = variable.get_integer_upper_bounds()
                lower = variable.get_integer_lower_bounds()
                values = variable.get_integer_variables()
                for i in range(variable.integer_size):
                    yield dict(name='{}[i{}]'.format(variable.name, i),
                               value=int(values[i]),
                               upper_bounds=int(upper[i]),
                               lower_bounds=int(lower[i]))

    def _generate_metric_documents(self):
        """ """
        for recorder in self.model.recorders:

            try:
                value = float(recorder.aggregated_value())
            except NotImplementedError:
                value = None

            try:
                df = recorder.to_dataframe()
                df = df.to_json(orient='split')
            except AttributeError:
                df = None

            if value is not None or df is not None:
                yield dict(name=recorder.name, value=value,
                           dataframe=df,
                           objective=recorder.is_objective is not None,
                           constraint=recorder.is_constraint,
                           minimise=recorder.is_objective == 'minimise')

    def reset(self):
        """ """
        self.created_at = None

    def before(self):
        """ """
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    def _make_insert_url(self, ):
        """ """
        return '{}/{}/searches/{}/individuals'.format(
            self.url, self.db, self.search_id)

    def finish(self):
        """ """
        import time
        url = self._make_insert_url()
        logger.info('Saving individual to PyretoDB via HTTP: {}'.format(url))
        t0 = time.time()

        evaluated_at = datetime.datetime.now()
        # TODO runtime statistics
        individual = dict(
            variables=list(self._generate_variable_documents()),
            metrics=list(self._generate_metric_documents()),
            created_at=self.created_at.isoformat(),
            evaluated_at=evaluated_at.isoformat(),
        )

        response = requests.post(url, json=individual)
        if response.status_code != 200:
            logger.error('Failed to save individual to PyretoDB. Status code:\
                         {}'.format(response.status_code))
        else:
            response_data = response.json()
            if 'error' in response_data:
                logger.error('Failed to save individual to PyretoDB. Response \
                              error: {}'.format(response_data['error']))
            else:
                logger.info(
                    'Save complete in {:.2f}s'.format(time.time() - t0))


# register the name so it can be loaded from JSON
PyretoDBRequestRecorder.register()


class PyretoDBJSONRecorder(Recorder):
    """ Recorder used to save MOEA search results to JSON files """
    # This recorder is currently in use in our simulation runs
    def __init__(self, *args, **kwargs):
        self.search_id = kwargs.pop('search_id')
        self.url = kwargs.pop('url')
        self.db = kwargs.pop('db')
        super().__init__(*args, **kwargs)
        self.created_at = None

        # Make this recorder dependent on all existing components
        for component in self.model.components:
            if component is not self:
                self.children.add(component)

    def _generate_variable_documents(self):
        """ """
        for variable in self.model.variables:

            if variable.double_size > 0:
                upper = variable.get_double_upper_bounds()
                lower = variable.get_double_lower_bounds()
                values = variable.get_double_variables()
                for i in range(variable.double_size):
                    yield dict(
                        name='{}[d{}]'.format(variable.name, i),
                        value=float(values[i]), upper_bounds=float(upper[i]),
                        lower_bounds=float(lower[i]))

            if variable.integer_size > 0:
                upper = variable.get_integer_upper_bounds()
                lower = variable.get_integer_lower_bounds()
                values = variable.get_integer_variables()
                for i in range(variable.integer_size):
                    yield dict(
                        name='{}[i{}]'.format(variable.name, i),
                        value=int(values[i]), upper_bounds=int(upper[i]),
                        lower_bounds=int(lower[i]))

    def _generate_metric_documents(self):
        """ """
        for recorder in self.model.recorders:

            try:
                value = float(recorder.aggregated_value())
            except NotImplementedError:
                value = None

            try:
                df = recorder.to_dataframe()
                df = df.to_json(orient='split')
            except AttributeError:
                df = None

            if value is not None or df is not None:
                yield dict(name=recorder.name, value=value,
                           dataframe=df,
                           objective=recorder.is_objective is not None,
                           constraint=recorder.is_constraint,
                           minimise=recorder.is_objective == 'minimise')

    def reset(self):
        """ """
        self.created_at = None

    def before(self):
        """ """
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    def _make_filename(self, ):
        """ """
        return os.path.join(self.url.split('://', 1)[1], self.db,
                            self.search_id, uuid.uuid4().hex+'.json')

    def finish(self):
        """ """
        import time
        fn = self._make_filename()
        logger.info('Saving individual to PyretoDB to JSON: {}'.format(fn))
        t0 = time.time()

        evaluated_at = datetime.datetime.now()

        # TODO runtime statistics
        individual = dict(
            variables=list(self._generate_variable_documents()),
            metrics=list(self._generate_metric_documents()),
            created_at=self.created_at.isoformat(),
            evaluated_at=evaluated_at.isoformat(),
        )

        # Make sure directory exists
        os.makedirs(os.path.split(fn)[0], exist_ok=True)

        with open(fn, mode='w') as fh:
            json.dump(individual, fh)
        logger.info('Save complete in {:.2f}s'.format(time.time() - t0))


# register the name so it can be loaded from JSON
PyretoDBJSONRecorder.register()
