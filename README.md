
# Coupled Parflow & Pywr model linked to MOEA.

This repository contains a combined parflow-pywr model that is linked to a multi-objective evolutionary algorithm (MOEA). It is used as part of the project called DRAWIT which has been set up to investigate how land use decisions with regards to the type and the position of land uses in the catchent affect multiple performance criteria of catchments.

The results of the study are published in the Journal of Hydrology in the paper: *Multicriteria land cover design in multi-sector systems via coupled distributed land and water management models* by: Tomasz Janus, James Tomlinson, Daniela Anghileri, Justin Sheffield, Stefan Kollet and Julien Harou.

# Installation

  - for development
      ```bash
         pip install -r requirements.txt -e .
      ```
  - as a build
      ```bash
         pip install build .
      ```
      or
      ```bash
         python3 -m build --sdist --wheel .
      ```

## Desciption of the input data used
The parflow model is given in the directory `input_files/parflow/profile1`:
The meteorological forcing input is given in file ```narr_1hr.wet.txt``` provided by Prof. Stefan Kollet and representing a semi-arid environent.

The pywr model is stored in `input_files/pywr/pywr-1-reservoir-model_profile1.json`

## Usage (local computer)
### Before running any of the code:
Initiate environment to work on the project by runninng:
```sh
$. ./init_env_drawit.sh
```
from project directory (set up to work only on my laptop for the moment). Remember to use "dot space dot /init..." when executing the command.

### To execute one simulation run of Pywr linked to Parflow
```sh
$ parflow-pywr run [json-file-name] -bo [path-to-h5-file] -to [path-to-csv-file]
```
e.g.
```sh
$ parflow-pywr run pywr-1-reservoir-model_profile1.json -bo outputs1/test.h5 -to outputs1/test.csv
```

### To plot the results saved to a h5 file
```sh
$ parflow-pywr plot -i [path-to-h5-file]
```
e.g.
```sh
$ parflow-pywr plot -i outputs1/test.h5
```

### To run batch simulation (number of scenarios)
parflow-pywr run pywr-1-reservoir-model_profile1.json -bo outputs_batch/test.h5 -to outputs_batch/test.csv


### To run MOEA optimization (with results saved in individual json files) without
NOTE: some of the commands take advantage of default parameter setting in the CLI (please consult the source code for details)

1. To run with NSGA-II (to be used when objectives are either 2 or 3

```sh
$ parflow-pywr search [search-name] -h file://[directory-for-mongo-db] -d [name-of-folder-with-json-files] -w [working-dir-for-parflow-outputs] -ne [no-of-evaluations] -p [no-of-cpus] -ps [population-size] -i [input-json-file]
```

e.g.

```sh
$ parflow-pywr search optim_1 -h file://optim_results -d optim_1 -w parflow_tmp_1 -ne 50000 -p 16 -ps 40 -i pywr-1-reservoir-model_profile1.json
```

will create a search called ```optim_1```, write all search results to folder ```optim_results``` in subfolder ```optim_1``` and use folder ```parflow_tmp_1``` as working folder for saving outputs from Parflow in each run. The search will use 50000 evaluations on 16 parallel threads and population of 40. The model used in simulations is in the JSON ```file pywr-1-reservoir-model_profile1.json```

2. To run with NSGA-III (to be used for many, i.e. 4 or more objectives)

```sh
$ parflow-pywr search [search-name] -h file://[directory-for-mongo-db] -d [name-of-folder-with-json-files] -w [working-dir-for-parflow-outputs] -a NSGAIII -ne [no-of-evaluations] -p [no-of-cpus] -i [input-json-file]
```

e.g.

```sh
$ parflow-pywr search optim_1 -h file://optim_results -d optim_1 -w parflow_tmp_1 -a NSGAIII -ne 50000 -p 16 -i pywr-1-reservoir-model_profile1.json
```

will create a search called ```optim_1```, write all search results to folder ```optim_results``` in subfolder ```optim_1``` and use folder ```parflow_tmp_1``` as working folder for saving outputs from Parflow in each run. The search will use 50000 evaluations on 16 parallel threads. The model used in simulations is in the JSON ```file pywr-1-reservoir-model_profile1.json```

## To run MOEA optimization using MPI

Run the commands intdoduced in the previous paragraph by preceeding them by command 'mpirun' and, in each command, add the '--mpi' flag

On laptop:
``` sh
$ mpirun -n 3 --oversubscribe parflow-pywr search optim_1 -h file://optim_results -d optim_1 -w parflow_tmp_1 --mpi -a NSGAII -ne 6 -p 3 -ps 2 -i pywr-1-reservoir-model_profile1.json
``` 



## Usage (CSF3 cluster)
Copy all model files (profile folders, model .json files) and ```.sh``` job scripts to ```~/scratch`` area.

### To run MOEA optimization on CSF cluster in interactive mode
In ```~/scratch``` area type:
```sh
$ qrsh -l short -V -cwd ./job_interactive.sh
```
to run short interactive job in the current working directory

### To run MOEA optimization on CSF cluster as a batch job
```sh
$ qsub job1.sh
```

### To run post-optimization processing of results

### To run post-optimization batch simulations on selected nondominated solutions
```
sh 
$ parflow-pywr run-parflow-batch [loation of config json file] [location of nondom sol. csv file]
```

e.g.
```
sh 
$ parflow-pywr run-parflow-batch config_file_parflow_hydro.json parflow_metrics.csv
```

### To save the results from seleted runs into a .json file

First configuration with water and energy mass balances
```
sh
$ parflow-pywr read-parflow-results ./parflow_batch_jobs/ config_file_parflow_hydro.json -s 365 -f 730
```
Second configuration with mode water mass balance variables (evaporation components)
```
sh
$ parflow-pywr read-parflow-results ./parflow_batch_jobs/ config_file_parflow_hydro_2.json -s 365 -f 730 -r results_json2
```



