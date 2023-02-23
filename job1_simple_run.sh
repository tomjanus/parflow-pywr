#!/bin/bash --login
#$ -cwd             # Job will run from the current directory
#$ -N simple_run_test
#$ -V
#$ -M tomasz.k.janus@gmail.com
#$ -m be

# Initialise proxy before making any downloads/uploads
module load tools/env/proxy

# Load Anaconda Python
module load apps/binapps/anaconda3/2019.03  # Python 3.7.3

# Try also a newer version
# module load apps/binapps/anaconda3/2019.07  # Python 3.7.3

#module load apps/python/mpi4py/3.0.3
#module load apps/python/mpi4py/3.0.1

module load compilers/gcc/8.2.0

export HDF5_USE_FILE_LOCKING=FALSE
export PARFLOW_PYWR=/mnt/iusers01/mace01/w79846tj/parflow-pywr-moea/
export PARFLOW_DIR=/mnt/iusers01/mace01/w79846tj/parflow/install

# Activate conda environment
conda activate parflow_pywr

parflow-pywr run pywr-1-reservoir-model_profile1.json -bo outputs_test/test.h5 -to outputs_test/test.csv
#$PARFLOW_DIR/bin/parflow profile1/profile
