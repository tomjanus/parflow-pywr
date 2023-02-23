""" This module defines VegetationTileFractionalCoverage class

    VegetationTileFractionalCoverage class contains methods to read fractional
    coverage in the Parflow/CLM model from and to the parflow DAT file.
"""


class VegetationTileFractionalCoverage:
    """ Wrapper around the DAT file specifying vegetation for Parflow tiles.

        Atrributes:
        -------------------------
        NUM_CLASSES: int
            number of vegetation classes in the Parflow/CLM model (currently 18)
        fractional_coverage: list
            a list of fractional coverage numbers (between zero and one) for
            each vegetation class and each tile in the Parflow modelling

        Methods:
        -------------------------
        read_from(cls, filename)
            reads fractional coverage from the .dat file, returns
            initialized instance of VegetationTileFractionalCoverage
            with fractional_coverage values from the .dat files
        rewrite_to(self, filename)
            writes fractional_coverage to the DAT file specified in filename
    """

    # Number of vegetation classes in the Parflow/CLM model
    NUM_CLASSES = 18

    # Initialise VegetationTileFractionalCoverage class object with a vector of
    # values specified in fractional_coverage
    def __init__(self, fractional_coverage):
        self.fractional_coverage = fractional_coverage
        """
        Parameters
        --------------------
        fractional_coverage: list
            Two-dimensional list with fractional coverage for each vegetation
            class and for each segment of the profile
        """

    # Class method that belongs to the class, not the object of the class
    @classmethod
    def read_from(cls, filename):
        """ Read fractional coverage from an existing file.

        Parameters
        --------------------
        filename: str
            name of the .dat file containing fractional coverage data for the
            model

        Returns
        --------------------
        Instantiated VegetationTileFractionalCoverage class object with
        fractional coverage read from the file
        """

        fractional_coverage = []
        with open(filename) as fh:
            for i, row in enumerate(fh.readlines()):
                if i < 2:  # Skip two header lines in the .dat file
                    continue
                # Fractional coverage is given in the final NUM_CLASSES columns
                data = row.split()[-cls.NUM_CLASSES:]
                # convert to floats
                data = [float(v) for v in data]
                fractional_coverage.append(data)
        return cls(fractional_coverage)

    def rewrite_to(self, filename):
        """ Writes fractional coverage data into a .dat file specified in filename

        Parameters
        --------------------
        filename: str
            name of the .dat file which will have fractional coverage data
            written to

        Raises
        --------------------
        ValueError
            If number of rows in the file is diffenent to the number of rows in
            fractional_coverage
        Value Error
            If total fractional coverage is not equal 1.0
        """
        with open(filename) as fh:
            rows = list(fh.readlines())

        if len(rows) - 2 != len(self.fractional_coverage):
            raise ValueError("Mismatch length of new fractional coverage \
                             data({}) and existing fractional"
                             "coverage data ({})."
                             .format(len(rows)-2,
                                     len(self.fractional_coverage)))

        with open(filename, 'w') as fh:
            # write headers
            for i in range(2):
                fh.write(rows[i])
            for i, (row, fc) in enumerate(zip(rows[2:],
                                              self.fractional_coverage)):
                if abs(sum(fc) - 1.0) > 1e-6:
                    raise ValueError('Total fractional coverage does not equal \
                                     1.0.')
                # Use new data for writing data lines
                data = row.split()[:-self.NUM_CLASSES] + [str(v) for v in fc]
                fh.write(' '.join(data) + '\n')
