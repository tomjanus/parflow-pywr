""" This module defines ParflowRunner class

    ParflowRunner class contains methods to manage the setup and execution of
    Parflow from within Pywr.
"""

import os
import shutil
import subprocess
import logging
import numpy as np
from .vegetation import VegetationTileFractionalCoverage

logger = logging.getLogger(__name__)


class ParflowRunner:
    """ Class to manage the setup and execution of parflow runs.
        Methods:
        -------------------------
        __init__ : object initialisation for ParflowRunner class
        model_directory: creates a full path to the directory for the model
                         given in name
        create_environment: creates the directory with files for running the
                            Parflow/PyWr model
        remove_environment: removes the directory and the files after successful
                            execution of the model
        rewrite_vegetation_coverage: writes sparse_fractional_coverage into
                                     Parflow's vegetation coverage file
        run: executes Parflow as a subprocess
    """

    def __init__(self, input_script, run_args, base_model_directory,
                 work_directory, vegetation_coverage_filename=None):
        self.input_script = input_script
        self.run_args = run_args
        self.base_model_directory = base_model_directory
        self.work_directory = work_directory
        self.vegetation_coverage_filename = vegetation_coverage_filename

    def model_directory(self, name):
        """ Returns full path of the directory for the model given in name """
        return os.path.join(self.work_directory, name)

    def create_environment(self, name, sparse_fractional_coverage=None):
        """ Create the basic working environment with files required to
            run the Pywr/Parflow model. Writes fractional vegetation
            fractional_coverage if specified as an argument """
        #from pudb import set_trace; set_trace()
        directory = self.model_directory(name)
        # Copy the contents of the base model
        shutil.copytree(self.base_model_directory, directory)
        # If sparse_fractional_coverage passed as an argument then write
        # write sparse_fractional_coverage into the model
        if sparse_fractional_coverage is not None:
            self.rewrite_vegetation_coverage(name, sparse_fractional_coverage)

    def remove_environment(self, name):
        """ Remove the directory with files generated in a combined Pywr/Parflow
            run """
        directory = self.model_directory(name)
        # Remove the directory tree from directory defined with name
        shutil.rmtree(directory)

    def rewrite_vegetation_coverage(self, name, sparse_fractional_coverage):
        """ Rewrite the vegetation coverage file for this environment.
            Initialises VegetationTileFractionalCoverage with
            dense_fractional_coverage and writes it to the Parflow's/CLM's
            vegetation file"""
        dense_fractional_coverage = []
        for data in sparse_fractional_coverage:
            # Make an list of zeros
            coverage = np.zeros(VegetationTileFractionalCoverage.NUM_CLASSES)
            # Assign values to the dense array as required.
            for iclass, value in data.items():
                coverage[iclass] = value
            # Now, normalise data.
            coverage /= coverage.sum()
            dense_fractional_coverage.append(coverage)

        filename = os.path.join(self.model_directory(name),
                                self.vegetation_coverage_filename)
        VegetationTileFractionalCoverage(
            dense_fractional_coverage).rewrite_to(filename)

    # Run parflow using TCLSH shell
    # def run(self, name):
    #     command = ['tclsh', self.input_script] + list(self.run_args)
    #     logger.debug('Running parflow with the following command: \
    #                   "{}"'.format(" ".join(command)))
    #     subprocess.run(command, check=True, stdout=subprocess.PIPE, \
    #                    cwd=self.model_directory(name))
    #     logger.debug('Parflow model run complete.')

    def run(self, name, mode='parflow'):
        """ Run parflow installed in the path '$PARFLOW_DIR/bin/parflow' """
        parflow = os.environ['PARFLOW_DIR'] + '/bin/parflow'
        # parflow = "/home/pbzep/pfdir/parflow" - Anrew Slaughter

        logger.info("Parflow results will be written to: " +
                    self.model_directory(name))

        if mode == 'tclsh':
            # Run parflow by executing the .tcl Parflow script
            # The script needs to include pfrun command in its body to execute
            # Parflow
            command = ['tclsh', self.input_script + '.tcl']
        else: # if 'parflow'
            # Generate Parflow run command defined as: parflow <parflow.pfidb>
            # <list of run arguments>
            logger.info(self.input_script)
            command = [parflow, self.input_script] + list(self.run_args)
            # First, recompile the .tcl file into pfidb file
            # Run a new subprocess
            recompile_tcl_command = ['tclsh', self.input_script + '.tcl']
            cwd_rel = self.model_directory(name)
            try:
                sub1 = subprocess.run(recompile_tcl_command, check=True,
                                      stdout=subprocess.PIPE,
                                      cwd=cwd_rel)
                #sub1 = subprocess.Popen(recompile_tcl_command,
                #                        stdout=subprocess.PIPE,
                #                        cwd=self.model_directory(name))
                #proc_stdout = sub1.communicate()[0]
                logger.info(self.input_script + ".tcl compiled into: " +
                            self.input_script + ".pfidb")
            except subprocess.CalledProcessError as call_error:
                raise RuntimeError("Command '{}' return with error (code {}): \
                                   {}".format(call_error.cmd,
                                              call_error.returncode,
                                              call_error.output))
            # TODO: WRITE THE COMMAND TO RUN THE TCLSH SCRIPT

        logger.debug('Running Parflow with the following \
                     command: "{}"'.format(" ".join(command)))
        # Run parflow as a subprocess in the current working directory defined
        # as self.model_directory(name). Opens a standard output stdout as a
        # pipe (subprocess.PIPE)
        try:
            logger.debug("Trying to run command: ", command)
            logger.debug("Executing in directory: ", self.model_directory(name))
            logger.debug("Executing script ", self.input_script)
            cwd_abs = os.path.abspath(self.model_directory(name))
            sub2 = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                                  cwd=cwd_rel)
            #subprocess.run(command, check=True, stdout=subprocess.PIPE,
            #               cwd=self.model_directory(name))
            #print('absolute path: ', os.path.abspath(self.model_directory(name)))
            #print(type(self.model_directory(name)))
            #sub2 = subprocess.Popen([self.model_directory(name),command])
            #subprocess.run('echo shit's not working, check=True, shell=True)
        except subprocess.CalledProcessError as call_error:
            raise RuntimeError("Command '{}' return with error (code {}): \
                               {}".format(call_error.cmd, call_error.returncode,
                               call_error.output))
        logger.debug('Parflow model run complete.')
