#!/bin/bash --login
#$ -cwd             # Job will run from the current directory
#$ -N moea1_nompi
#$ -V
#$ -pe smp.pe 16     # Number of cores (2-32)
#$ -M tomasz.k.janus@gmail.com
#$ -m be
#$ -t 1-4          # A job-array with 4 seeds

# Initialise proxy before making any downloads/uploads
module load tools/env/proxy

# Load Anaconda Python
module load apps/binapps/anaconda3/2019.03  # Python 3.7.3
# Try also a newer version
# module load apps/binapps/anaconda3/2019.07  # Python 3.7.3

export HDF5_USE_FILE_LOCKING=FALSE
export PARFLOW_PYWR=/mnt/iusers01/mace01/w79846tj/parflow-pywr-moea/
export PARFLOW_DIR=""

SEED_PARAM=( 10 20 30 40 50 60 70 80 90 100 )
# Job index for each of the run in the job-array
INDEX=$((SGE_TASK_ID-1))

# Load parflow
module load apps/intel-18.0/parflow/3.6.0

# Activate conda environment
conda activate parflow_pywr

# Inform the Python script how many cores to use - $NSLOTS is automatically set to the number given above.
export OMP_NUM_THREADS=$NSLOTS

# To run a new job (use 100000 function evaluations and NSGAIII algorithm)
parflow-pywr search optim_$SGE_TASK_ID -h file://optim_results_$SGE_TASK_ID -d \
optim_nompi_$SGE_TASK_ID -w parflow_tmp_$SGE_TASK_ID_nompi -a NSGAIII -ne 80000 -p $NSLOTS -i pywr-1-reservoir-model_profile1.json \
--seed=${X_PARAM[$INDEX]}

