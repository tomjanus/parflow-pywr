""" This module defines a recorder called ParflowVegetationDiversityRecorder
    which inherits from PyWr's Recorder class
"""
import numpy as np
# These import functions point to an installation of PyWr
# TODO: Add 'export PYTHONPATH=$PYTHONPATH:/path/to/PyWr' to ~/.profile file so
#       that we can import PyWr modules and functions without specifying their
#       location in the file system
from pywr.recorders import Recorder, NumpyArrayNodeRecorder, Aggregator
from pywr.parameters import load_parameter


class ParflowVegetationDiversityRecorder(Recorder):
    """ A Recorder class inheriting from PyWr's Recorder class which calculates
        a number of distinct landuse classes used in Parlow. Discount classes
        which are not considered vegetation

        Methods:
        -------------------------
        values(self)
            returns diversity score
        load(cls, model, data)
            instantiate ParflowVegetationDiversityRecorder class object from

    """

    def __init__(self, model, vegetation_param, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        vegetation_param.parents.add(self)
        self.vegetation_param = vegetation_param

    def values(self):
        """ Return diversity score. Diversity is the number of different landuse
            types allocated to the model excluding non-green landuse types.

            Identical for each scenario (JTomlinson)
        """
        # What is model.scenarios.combinations (ncomb)?
        ncomb = len(self.model.scenarios.combinations)
        # Get vegetation types of int for all surface tiles
        # The elements are indices of corresponding elements in landuse_classes
        landuse_indices = self.vegetation_param.get_integer_variables()
        # Get the list of landuse classes
        landuse_classes = self.vegetation_param.land_use_classes
        # Define a list of land types which should not be featured in diversity
        # 13 - urban/built-up lands
        # 15 - snow and ice
        # 16 - barren or sparsely vegetated
        # 17 - water bodies
        # 18 - bare soil
        non_green_types = [13, 15, 16, 17, 18]
        # Calculate a list of landuse types from the list of landuse indices
        landuse_vector = [landuse_classes[i] for i in landuse_indices]
        # Number of distinct green landuse types on the arable surface of
        # the domain
        landuse_vector_green = [landuse for landuse in landuse_vector if
                                landuse not in non_green_types]
        score = len(set(landuse_vector_green))
        return np.array([score for i in range(ncomb)], dtype=np.float64)

    @classmethod
    def load(cls, model, data):
        """ Read vegetation_param from PyWr model.

        Parameters
        --------------------
        model
            PyWr model ??????
        data
            ???????

        Returns
        --------------------
        Instantiated ParflowVegetationDiversityRecorder class with model and
        data
        """
        # Return ParflowVegetationParameter object from the JSON file, called
        # parflow_landuse
        vegetation_param = load_parameter(model, data.pop("vegetation_param"))
        # Return ParflowVegetationDiversityRecorder object
        return cls(model, vegetation_param=vegetation_param, **data)


# register the name so it can be loaded from JSON
ParflowVegetationDiversityRecorder.register()


class ParflowCropLandTypeNumberRecorder(Recorder):

    def __init__(self, model, vegetation_param, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        vegetation_param.parents.add(self)
        self.vegetation_param = vegetation_param
        # Value associated with crop land type in Parflow/CLM
        self.crop_vals = [12]

    def values(self):
        """ Return diversity score. Diversity is the number of different landuse
            types allocated to the model.

            Identical for each scenario (JTomlinson)
        """
        # What is model.scenarios.combinations (ncomb)?
        ncomb = len(self.model.scenarios.combinations)

        # Get vegetation types of int for all surface tiles
        # Returns a list with indices of vegetation_param.land_use_classes
        landuse_types = self.vegetation_param.get_integer_variables()

        # Find a list of landuse_classes from landuse_types (list of indices)
        landuse_classes = [self.vegetation_param.land_use_classes[ind]
                           for ind in landuse_types]

        # Number of crop fields on the arable surface of the domain
        score = len(list(filter(lambda x: x in self.crop_vals,
                    landuse_classes)))

        print("No. of crop fields: {}".format(score))

        return np.array([score for i in range(ncomb)], dtype=np.float64)

    @classmethod
    def load(cls, model, data):
        """ Read vegetation_param from PyWr model.

        Parameters
        --------------------
        model
            PyWr model ??????
        data
            ???????

        Returns
        --------------------
        Instantiated ParflowVegetationDiversityRecorder class with model and
        data
        """
        # Return ParflowVegetationParameter object from the JSON file, called
        # parflow_landuse
        vegetation_param = load_parameter(model, data.pop("vegetation_param"))
        # Return ParflowVegetationDiversityRecorder object
        return cls(model, vegetation_param=vegetation_param, **data)


# register the name so it can be loaded from JSON
ParflowCropLandTypeNumberRecorder.register()


class ParflowBareSoilLandTypeNumberRecorder(Recorder):

    def __init__(self, model, vegetation_param, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        vegetation_param.parents.add(self)
        self.vegetation_param = vegetation_param
        # Value associated with bare soil land type in Parflow/CLM
        self.crop_vals = [18]

    def values(self):
        """ Return diversity score. Diversity is the number of different landuse
            types allocated to the model.

            Identical for each scenario (JTomlinson)
        """
        # What is model.scenarios.combinations (ncomb)?
        ncomb = len(self.model.scenarios.combinations)

        # Get vegetation types of int for all surface tiles
        # Returns a list with indices of vegetation_param.land_use_classes
        landuse_types = self.vegetation_param.get_integer_variables()

        # Find a list of landuse_classes from landuse_types (list of indices)
        landuse_classes = [self.vegetation_param.land_use_classes[ind]
                           for ind in landuse_types]

        # Number of crop fields on the arable surface of the domain
        score = len(list(filter(lambda x: x in self.crop_vals,
                    landuse_classes)))

        print("No. of bare soil fields: {}".format(score))

        return np.array([score for i in range(ncomb)], dtype=np.float64)

    @classmethod
    def load(cls, model, data):
        """ Read vegetation_param from PyWr model.

        Parameters
        --------------------
        model
            PyWr model ??????
        data
            ???????

        Returns
        --------------------
        Instantiated ParflowVegetationDiversityRecorder class with model and
        data
        """
        # Return ParflowVegetationParameter object from the JSON file, called
        # parflow_landuse
        vegetation_param = load_parameter(model, data.pop("vegetation_param"))
        # Return ParflowVegetationDiversityRecorder object
        return cls(model, vegetation_param=vegetation_param, **data)


# register the name so it can be loaded from JSON
ParflowBareSoilLandTypeNumberRecorder.register()


class NoDaysAboveThresholdRecorder(NumpyArrayNodeRecorder):
    """ Calculates the number of timesteps in which the flow in a node
        is above the threshold value:

    Parameters:

    """

    def __init__(self, model, node, flow_threshold, **kwargs):
        super(NoDaysAboveThresholdRecorder, self).__init__(model, node, **kwargs)
        self.flow_threshold = flow_threshold
        self._temporal_aggregator = Aggregator("COUNT_NONZERO")

    # Override cythonized cdef setup
    def setup(self):
        ncomb = len(self.model.scenarios.combinations)
        nts = len(self.model.timestepper)
        self._data = np.zeros((nts, ncomb))

    # Override cythonized cdef reset
    def reset(self):
        self._data[:, :] = 0.0

    # Override cythonized cdef after
    def after(self):
        ts = self.model.timestepper.current
        for i in range(self._data.shape[1]):
            if self.node.flow[i] > self.flow_threshold:
                self._data[ts.index, i] = 1
            else:
                self._data[ts.index, i] = 0
        return 0

    def values(self):
        """Compute a value for each scenario using `temporal_agg_func`.
        """
        return self._temporal_aggregator.aggregate_2d(
            self._data, axis=0, ignore_nan=self.ignore_nan)

    @classmethod
    def load(cls, model, data):
        flow_threshold = load_parameter(model, data.pop('min_flow'))
        node = model._get_node_from_ref(model, data.pop("node"))
        return cls(model, node, flow_threshold, **data)


# register the name so it can be loaded from JSON
NoDaysAboveThresholdRecorder.register()
