""" Define classes which specify Pywr custom parameters
    ParflowRunnerParameter(Parameter): runs Parflow from within PyWr
    ParflowDischargeParameter(Parameter):
    ParflowEvapoTranspirationParameter(Parameter):
    ParflowVegetationParameter(Parameter):
"""


# from .nc_read import read_discharge, read_et
import uuid
import logging
import numpy as np
from pywr.parameters import Parameter, load_parameter
from .manager import ParflowRunner
from .hydrography import read_discharge
from .et import read_et

logger = logging.getLogger(__name__)

class ParflowRunnerParameter(Parameter):
    """ Class inheriting from Pywr Parameter Class defining a custom
        parameter used for running Parflow from within Pywr
        Methods:
        -------------------------------------
        resample_size(self): recalculates communication interval (sampling) to
                             align Parflow's output with PyWr's
        reset(self): run Parflow before each evaluation of Pywr
        finish(self):removes the working directory with input/output files
        directory(self): returns model directory
        load(cls,model,data): loads Parflow's data from JSON file
    """

    def __init__(self, model, runner, *args, **kwargs):
        # called once when the parameter is created
        vegetation_param = kwargs.pop("vegetation_param", None)
        self.remove_environments = kwargs.pop("remove_environments", True)
        # TODO read this directly from the Parflow input script (TCL)
        self.dump_interval = kwargs.pop("dump_interval", None)
        super().__init__(model, *args, **kwargs)
        self.runner = runner
        self.env_name = None

        if vegetation_param is not None:
            vegetation_param.parents.add(self)
        self.vegetation_param = vegetation_param

    @property
    def resample_size(self):
        """ Calculate the size of any resampling needed to align Parflow output
            with Pywr time-step. """
        if self.dump_interval is None:
            # Unknown size of Parflow output; assume the same as Pywr (i.e. no
            # resampling)
            return None
        # Pywr time-step is in days; convert to hours to be comparable with
        # Parflow
        timestep = self.model.timestepper.delta.days * 24
        if self.dump_interval > timestep:
            # Throw an error. We could do some infilling, but probably better to
            # make the user aware this is a problem.
            raise ValueError('The dump interval of Parflow is less frequent \
                              than Pywr timestep.')
        if timestep % self.dump_interval != 0:
            raise ValueError('The dump interval of Parflow is not a multiple \
                              of the Pywr timestep.')
        # Return the integer resampling size.
        return timestep // self.dump_interval

    def reset(self):
        """ Run parflow before each evaluation of Pywr. Called for every run
            at the start of a model run before the first timestep """
        # called before each PyWr run
        self.env_name = uuid.uuid4().hex
        # Run parflow
        self.runner.create_environment(self.env_name)
        if self.vegetation_param is not None:
            self.runner.rewrite_vegetation_coverage(
                self.env_name,
                self.vegetation_param.to_sparse_fractional_coverage())
        self.runner.run(self.env_name)

    def finish(self):
        if self.remove_environments:
            self.runner.remove_environment(self.env_name)

    def value(self, ts, scenario_index):
        # called once per timestep for each scenario
        """ This returns nothing useful. """
        return 0.0

    @property
    def directory(self):
        return self.runner.model_directory(self.env_name)

    # Create an instance of the parameter from JSON
    @classmethod
    def load(cls, model, data):
        # called when the parameter is loaded from a JSON document
        # Parse parflow configuration
        parflow_script = data.pop("input_script")
        parflow_directory = data.pop("directory", ".")
        parflow_work_directory = data.pop("work_directory")
        parflow_args = data.pop("arguments", [])
        vegetation_coverage_filename = data.pop(
            "vegetation_coverage_filename", None)
        parflow_runner = ParflowRunner(
            parflow_script, parflow_args, parflow_directory,
            parflow_work_directory,
            vegetation_coverage_filename=vegetation_coverage_filename)

        if "vegetation_param" in data:
            # Load parameter from JSON
            vegetation_param = load_parameter(
                model, data.pop("vegetation_param"))
        else:
            vegetation_param = None

        return cls(model, parflow_runner,
                   vegetation_param=vegetation_param, **data)


# register the name so it can be loaded from JSON
ParflowRunnerParameter.register()


class ParflowDischargeParameter(Parameter):
    """ Class inheriting from Pywr Parameter Class defining a custom
        parameter used for reading discharge from parflow
        Methods:
        -------------------------------------
        reset(self): read Parflow discharge before every PyWr run
        value(self, ts, scenario_index): returns discharge from Parflow for a
                                         given timestep ts and scanario
        load(cls, model, data): loads the parameter from JSON
    """
    def __init__(self, model, runner_param, coordinates, *args, **kwargs):
        # called once when the parameter is created
        self.offset = kwargs.pop("offset", 0)
        self.start_from = kwargs.pop("start_from")

        super().__init__(model, *args, **kwargs)

        runner_param.parents.add(self)
        self.runner_param = runner_param
        self.coordinates = coordinates
        self.values = None

    def reset(self):
        """ Read Parflow discharge before every PyWr run before the first
            time step """
        # called before each PyWr run
        parflow_directory = self.runner_param.directory

        for _, array in read_discharge(
                parflow_directory, {self.name: self.coordinates},
                self.start_from).items():
                # resample_size=self.runner_param.resample_size).items():
            self.values = array

            #logger.info('Flow array: {}'.format(array))

    def value(self, ts, scenario_index):
        """Returns the value of the parameter, i.e. discharge from the Parflow
           model at a given timestep (ts) for a given scenario (scenario_index)
        """
        # called once per timestep for each scenario
        return self.values[ts.index+self.offset]

    # Create an instance of the parameter from JSON
    @classmethod
    def load(cls, model, data):
        # called when the parameter is loaded from a JSON document
        runner_param = load_parameter(model, data.pop("runner"))
        coordinates = data.pop("coordinates")
        return cls(model, runner_param, coordinates, **data)


# register the name so it can be loaded from JSON
ParflowDischargeParameter.register()


class ParflowEvapoTranspirationParameter(Parameter):
    """ Class inheriting from Pywr Parameter Class defining a custom
        parameter used for reading evapotranspiration info from parflow
        Methods:
        -------------------------------------
        reset(self): read evapotranspiration before every PyWr run
        value(self, ts, scenario_index): returns evapotranspiration for a
                                         given timestep ts and scanario
        load(cls, model, data): loads the parameter from JSON
    """
    def __init__(self, model, runner_param, *args, **kwargs):
        # called once when the parameter is created
        self.offset = kwargs.pop("offset", 0)
        super().__init__(model, *args, **kwargs)
        runner_param.parents.add(self)
        self.runner_param = runner_param
        self.values = None

    def reset(self):
        """ Read evapotranspiration before every PyWr run """
        # called before each PyWr run
        parflow_directory = self.runner_param.directory
        self.values = read_et(parflow_directory)
        # , resample_size=self.runner_param.resample_size)

    def value(self, ts, scenario_index):
        """Returns the value of the parameter at a given timestep (ts) for a
           given scenario (scenario_index)"""
           # called once per timestep for each scenario
        #logger.info("the error source: {}".format(self.values[ts.index+self.offset]))
        #from pdb import set_trace; set_trace()
        #print("ts value: {}".format(ts))
        #print("ts index value: {}".format(ts.index))
        #print("self.values length: {}".format(len(self.values)))
        return self.values[ts.index+self.offset]

    # Create an instance of the ParflowEvapoTranspirationParameter from JSON
    @classmethod
    def load(cls, model, data):
        # Load parameter from JSON
        runner_param = load_parameter(model, data.pop("runner"))
        return cls(model, runner_param, **data)


# register the name so it can be loaded from JSON
ParflowEvapoTranspirationParameter.register()


class ParflowVegetationParameter(Parameter):
    """ Class inheriting from Pywr Parameter Class defining a custom
        parameter used for reading vegetation info from parflow
        Methods:
        -------------------------------------
        num_variable_tiles(self): returns and sets the number of tiles in Parflow
        to_sparse_fractional_coverage(self): returns a list with coverage values
        load(cls, model, data): loads the parameter from JSON
    """
    def __init__(self, model, land_use_classes, num_variable_tiles, *args, **kwargs):
        # called once when the parameter is created
        super().__init__(model, *args, **kwargs)
        self.land_use_classes = land_use_classes
        self.num_variable_tiles = num_variable_tiles  # This sets integer_size
        self.double_size = 0
        self._values = np.zeros(self.integer_size, dtype=np.int32)

    @property
    def num_variable_tiles(self):
        return self.integer_size

    @num_variable_tiles.setter
    def num_variable_tiles(self, value):
        self.integer_size = value

    def to_sparse_fractional_coverage(self):
        """ Returns a list with coverage values for each tile """
        coverage = []
        print("Number of land surface tiles: "
              + str(self.num_variable_tiles))
        print("Number of land use classes: "
              + str(len(self.land_use_classes)))
        for i in range(self.num_variable_tiles):
            land_use_class = self.land_use_classes[self._values[i]]
            print("Allocated land class for tile {}: {}".
                  format(i+1, land_use_class))
            land_use_class -= 1  # Use zero based indexing for writing the files
            coverage.append({land_use_class: 1.0})
        return coverage

    def set_integer_variables(self, values):
        self._values[...] = np.array(values, dtype=np.int32)

    def get_integer_variables(self):
        return self._values

    def get_integer_lower_bounds(self):
        return np.zeros(self.integer_size, dtype=np.int32)

    def get_integer_upper_bounds(self):
        return np.ones(
            self.integer_size, dtype=np.int32) * (len(self.land_use_classes)-1)

    def value(self, ts, scenario_index):
        """ This returns nothing useful. """
        # called once per timestep for each scenario
        return 0.0

    # create an instance of the parameter from JSON
    @classmethod
    def load(cls, model, data):
        return cls(model, **data)


# register the name so it can be loaded from JSON
ParflowVegetationParameter.register()
