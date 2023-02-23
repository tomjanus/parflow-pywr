import os
import sys
import pandas
from matplotlib import pyplot as plt


def plot_hv(filename):
    ''' plots hypervolume based on the results stored in the .csv file defined
        as the input argument filename '''
    base, *_ = os.path.splitext(filename)
    fig, ax = plt.subplots(figsize=(8, 4))
    df = pandas.read_csv(filename)

    df.set_index('nfe', inplace=True)
    df.plot(marker='o', ax=ax, legend=False)
    ax.grid()
    ax.set_xlabel('Fraction of total number of evaluations')
    ax.set_ylabel('Normalised hypervolume')
    #ax.set_title(base.replace('hypervolume ', ''))

    patches, labels = ax.get_legend_handles_labels()
    ax.legend(patches, labels, loc='best', ncol=2)

    fig.savefig(base + '.png', dpi=300)


def plot_hv_from_df(df):
    fig, ax = plt.subplots(figsize=(8, 4))
    df.set_index('nfe', inplace=True)
    df = df.iloc[:, 1:]

    df.plot(marker='o', ax=ax, legend=False)
    ax.grid()
    ax.set_xlabel('Number of function evaluations')
    ax.set_ylabel('Normalised hypervolume')
    #ax.set_title(base.replace('hypervolume ', ''))

    patches, labels = ax.get_legend_handles_labels()
    ax.legend(patches, labels, loc='best', ncol=2)

    fig.savefig('hypervolume.png', dpi=300)
