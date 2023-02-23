# Functions to extract Parflow output
# NAME:
#    functions_output.py
# VERSION:
#    03/25/2019 v0.5
# STATUS:
#    under development
# LANGUAGE:
#    Python 3.6x
# OWNER:
#    Thomas Pomeon - t.pomeon@fz-juelich.de - TP
# BASED ON WORK BY:
#    Niklas Wagner
#    Yueling Ma
# PURPOSE:
#    Reads Parflow .pfb outputs and exports discharge timeseries for a certain location #    and as an np array for the entire domain.
# REQUIRES:
#     sys, os, numpy, pf_read

import sys, os
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib as plt
#import pandas as pd

#Define path to pf_read
import pf_read as pfr

tstep=int(sys.argv[1])

#spinup
#name='/home/guest1/exercises/exercise9/exercisesix.out.satur.'+('{:05d}'.format(tstep))+'.pfb'
name='/home/guest1/exercises/exercise9/exercisenine.out.perm_x.pfb'
name='/home/lepton/git_projects/parflow-pywr-moea/parflow_jobs/ee2c64fa2e17447fb59d40dd7afd2eac/profile.out.qflx_evap_tot.00725.pfb'

#data = pfr.read(name)
data = pfr.read_chunk(name)

from pudb import set_trace; set_trace()

#print(np.amin(data[:,0,:]),np.amax(data[:,0,:]))
data = np.ma.masked_where(data <= -100000.0, data)

#color_map = plt.cm.get_cmap('Blues')
color_map = plt.cm.get_cmap('coolwarm_r')
plt.imshow(np.log(data[:,0,:]),interpolation='none',origin='lower',aspect='auto',cmap=color_map)
#plt.imsave(data[:,0,:].T,interpolation='none',vmin=0.0,vmax=1.0,origin='lower',aspect='auto',cmap=color_map)
plt.colorbar()
plt.show()
