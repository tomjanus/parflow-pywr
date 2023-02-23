# Parflow Installation Guide
Installation of the main program/code: Parflow/CLM - an integrated parallel watershed model coupled
with Community Land Model (CLM)

## Dependencies
1. Hypre
2. SiLo -  library for reading and writing a wide variety of scientific data to binary, disk filesb 
   [optional]. Used only if planning to use VisIt visualisation package
3. OpenMPI - check what version I'm running at Xubuntu and which version is available in CSF
4. TCL

### C/C++ and Fortran compilers

```
$ sudo apt-get install gcc
$ sudo apt-get install g++
$ sudo apt-get install gdc
$ sudo apt-get install gfortran
```

If you compile on CSF3 cluster, make sure that these compilers are available in the shell either
out-of-the-box or loaded with ``` module load [module-name] ```

### TCL
From repos: ```$ sudo apt-get install tcl-dev``` and ```$ sudo apt-get install tk-dev```

On the CSF3 cluster tcl-dev and tk-dev should be already installed

### OpenMPI

Check OpenMPI version in the CSF3 cluster

### Download Parlow, Hypre and Silo

Either tar.gz or via git clone

## COMPILATION
### Set environmental variables
```
nano ~/.bash_aliases

export CC=gcc
export CXX=g++
export FC=gfortran
export F77=gfortran

export PARFLOW_DIR=/path-to-parflow-dir/parflow/parflow

export SILO_DIR=/path-to-parflow-dir/silo
export HYPRE_DIR=/path-to-parflow-dir/hypre
export PATH=$PATH:/path-to-parflow-dir/visit/bin
```

Then ```source ~/.bash_aliases```


### Install OpenMPI (if not installed)
```
cd openmpi[tab]
sudo ./configure
sudo make all
sudo make check
sudo make all install
cd ..
```

or install from repos

### Install Silo
```
cd silo
./configure --prefix=$SILO_DIR --disable-silex

make all
make check
make all install
cd ..
```

### Install Hypre
```
cd hypre/src
./configure --prefix=$HYPRE_DIR --with-MPI [if you’re not using MPI, use --without-MPI]
make all
make check
make all install
cd ../..
```

### Install Parflow and PfTools
```
 cd parflow/pfsimulator
./configure --prefix=$PARFLOW_DIR --enable-timing --with-clm --with-silo=$SILO_DIR --with-hypre=$HYPRE_DIR --with-amps=mpi1 [if you’re not using MPI, leave the last flag off]
make install
cd ../pftools
./configure --prefix=$PARFLOW_DIR --with-silo=$SILO_DIR --with-amps=mpi1 [if you’re not using MPI, leave the last flag off]
make install
cd ../test
sudo ldconfig
make check
```

From a different source:
```
$ ./configure –prefix=${HOME}/Downloads/PARFLOW/parflow.693 –enable-timing –with-clm \
–with-silo=${HOME}/Downloads/PARFLOW/silo-4.7.2 –with-hypre=${HOME}/Downloads/PARFLOW/hypre-2.9.0b/src/hypre \
–with-amps=mpi1
```

Sometimes compilation errors may be encountered:

Next to build parflow run $ make install. Under ubuntu you might get errors at the very end of the building process related to gfortran and m libraries. 
This is probably a bug in the configuration process and you need to edit manually the Makefile.config under the config folder. 
If your current directory is the ../pfsimulator do the following: $ gedit config/Makefile.config. Search for a line that starts with 
LDLIBS    = $(LDLIBS_EXTRA)  (Note this is a very long line).

In this line you may see a gfortran m. Change those to -lgfortran -lm. Further right on the same line you may see two -l -l.
Those probably are the -ls that where missing. Anyway now delete them. Keep going right you may see some gfortran and m that they apart from
their -ls i.e. -l gfortran -l m. Remove the spaces between them.

Save the file, cross fingers and rerun $ make install. (DO NOT RERUN .configure). 


