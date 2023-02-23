#!/bin/bash --login
#$ -cwd              # Use the current directory
    
# Load the software
module load compilers/gcc/8.2.0
module load libs/gcc/hypre/2.18.2-serial

~/parflow/dependencies/cmake/bin/cmake \
     -S ~/parflow/src \
     -B ~/parflow/build \
     -D PARFLOW_AMPS_LAYER=seq \
     -D PARFLOW_AMPS_SEQUENTIAL_IO=TRUE \
     -D HYPRE_ROOT=${HYPREDIR} \
     -D PARFLOW_ENABLE_TIMING=TRUE \
     -D PARFLOW_HAVE_CLM=TRUE
