# This is a collection of tools used for post-processing results from MOEA runs

# USAGE
## Exporting all solutions into a .csv file
``` sh
$ moea-tools export-all-results -i <path-to-folder-with-input-files> -o <path-to-folder-with-output-files>
```
## Exporting nondominated solutions into a .csv and .h5 files
``` sh
$ moea-tools export-nondominated-results -i <path-to-folder-with-input-files> -o <path-to-folder-with-output-files>

# --include-time <flag, default=False> - this does not seem to be present in the file any longer (or was it just intended only?)
```

## Compute hypervolume from the values obtained from MOEA runs
``` sh
$ moea-tools 
```

# TYPICAL WORKFLOW
1. Run `moea-tools export-all-results`
   * This will produce a .csv file or .h5 file with all results. .csv file is set by default
2. Run `moea-tools compute_hv`
   * This will produce a csv file with hypervolume
3. Run `moea-tools plot_hv` to plot the hypervolume
4. Run `moea-tools export-nondominated-results` to export nondominated results for plotting in **Polyvis** <http://www.polyvis.org>
