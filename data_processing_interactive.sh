#!/bin/bash --login
#$ -cwd             # Job will run from the current directory
#$ -N data_proc
#$ -V
#$ -pe smp.pe 32     # Number of cores (2-32)
#$ -M tomasz.k.janus@gmail.com
#$ -m be

# Initialise proxy before making any downloads/uploads
module load tools/env/proxy

# Load Anaconda Python
module load apps/binapps/anaconda3/2019.03  # Python 3.7.3

# Activate conda environment
conda activate parflow_pywr

# Inform the Python script how many cores to use - $NSLOTS is automatically set to the number given above.
export OMP_NUM_THREADS=$NSLOTS

# To run a new job
python pyreto_export_multiple_runs.sh

# This file is set up to check execution of the problem on the CSF cluster in an interactive shell via qrsh
