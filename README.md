# Coupled ParFlow–Pywr Model Linked to MOEA

This repository contains a coupled **ParFlow–Pywr** model integrated with a **multi-objective evolutionary algorithm (MOEA)**. It was developed as part of the **DRAWIT** project, which investigates how land use decisions—particularly the type and spatial distribution of land use—affect multiple performance criteria in catchment systems.

The scientific findings are published in the **Journal of Hydrology**:

📄 **[Multicriteria land cover design in multi-sector systems via coupled distributed land and water management models](https://www.sciencedirect.com/science/article/pii/S0022169423002366)**  
*Tomasz Janus, James Tomlinson, Daniela Anghileri, Justin Sheffield, Stefan Kollet, and Julien Harou.*

Explore the results interactively via this [Dash Application](https://drawit-moea-results.onrender.com/).

---

## 📦 Installation

For development:
```bash
pip install -r requirements.txt -e .
```

To build and install the package:
```bash
pip install build .
```
Or:
```bash
python3 -m build --sdist --wheel .
```

---

## 📁 Input Data Description

- **ParFlow input** is located in:  
  `input_files/parflow/profile1/`  
  It uses meteorological forcing from `narr_1hr.wet.txt`, representing a semi-arid environment (provided by Prof. Stefan Kollet).

- **Pywr model** is stored in:  
  `input_files/pywr/pywr-1-reservoir-model_profile1.json`

---

## 🚀 Usage (Local Computer)

### 🔧 Initialize the environment
Run from the project root:
```bash
. ./init_env_drawit.sh
```
> ⚠️ The script is currently configured for use on the developer's laptop only.

---

### ▶️ Run a single Pywr–ParFlow simulation
```bash
parflow-pywr run [input-json] -bo [output-h5-path] -to [output-csv-path]
```

Example:
```bash
parflow-pywr run pywr-1-reservoir-model_profile1.json -bo outputs1/test.h5 -to outputs1/test.csv
```

---

### 📊 Plot results from HDF5 output
```bash
parflow-pywr plot -i [output-h5-path]
```

Example:
```bash
parflow-pywr plot -i outputs1/test.h5
```

---

### 📁 Run a batch of simulations
```bash
parflow-pywr run pywr-1-reservoir-model_profile1.json -bo outputs_batch/test.h5 -to outputs_batch/test.csv
```

---

## ⚙️ MOEA Optimization

> ℹ️ These commands rely on default CLI parameters—refer to the source code for customization.

### 🧬 NSGA-II (for 2 or 3 objectives)

```bash
parflow-pywr search [search-name] \
    -h file://[mongo-directory] \
    -d [json-output-dir] \
    -w [parflow-work-dir] \
    -ne [evaluations] \
    -p [parallel-jobs] \
    -ps [population-size] \
    -i [input-json]
```

Example:
```bash
parflow-pywr search optim_1 \
    -h file://optim_results \
    -d optim_1 \
    -w parflow_tmp_1 \
    -ne 50000 -p 16 -ps 40 \
    -i pywr-1-reservoir-model_profile1.json
```

### 🧬 NSGA-III (for 4 or more objectives)

```bash
parflow-pywr search [search-name] \
    -h file://[mongo-directory] \
    -d [json-output-dir] \
    -w [parflow-work-dir] \
    -a NSGAIII \
    -ne [evaluations] \
    -p [parallel-jobs] \
    -i [input-json]
```

Example:
```bash
parflow-pywr search optim_1 \
    -h file://optim_results \
    -d optim_1 \
    -w parflow_tmp_1 \
    -a NSGAIII -ne 50000 -p 16 \
    -i pywr-1-reservoir-model_profile1.json
```

---

## 🔌 Run MOEA with MPI

Use `mpirun` and add the `--mpi` flag:

Example (on local machine):
```bash
mpirun -n 3 --oversubscribe parflow-pywr search optim_1 \
    -h file://optim_results \
    -d optim_1 \
    -w parflow_tmp_1 \
    --mpi -a NSGAII -ne 6 -p 3 -ps 2 \
    -i pywr-1-reservoir-model_profile1.json
```

---

## 🖥️ Usage on CSF3 Cluster

### 🧳 Prepare

Copy the model files (`profile` folders, `.json` files, and `.sh` scripts) to your `~/scratch` directory.

### 🧪 Run MOEA interactively

```bash
qrsh -l short -V -cwd ./job_interactive.sh
```

### 📤 Submit MOEA batch job

```bash
qsub job1.sh
```

---

## 📈 Post-Processing Results

### 🧪 Run post-optimization batch simulations

```bash
parflow-pywr run-parflow-batch [config-json] [nondominated-csv]
```

Example:
```bash
parflow-pywr run-parflow-batch config_file_parflow_hydro.json parflow_metrics.csv
```

---

### 💾 Save results to JSON

#### Config 1: water and energy balances

```bash
parflow-pywr read-parflow-results ./parflow_batch_jobs/ \
    config_file_parflow_hydro.json -s 365 -f 730
```

#### Config 2: water balance with evaporation components

```bash
parflow-pywr read-parflow-results ./parflow_batch_jobs/ \
    config_file_parflow_hydro_2.json -s 365 -f 730 -r results_json2
```

---

## 🧰 Notes and Tips

- All commands assume the working directory is the project root.
- For best performance on clusters, ensure that input/output folders are on fast storage (`scratch`, RAM disk).
- The ParFlow model may require MPI configuration depending on your platform.
