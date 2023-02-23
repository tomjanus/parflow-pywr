import click
#import .outputs_visualisation
from process_outputs import pyreto_export_all_individuals
from process_outputs import pyreto_export_nodominated
from process_outputs import pyreto_compute_hv
from process_outputs import pyreto_plot_hv


@click.group()
def start_cli():
    ''' Function used to start the CLI program '''


@start_cli.command()
@click.option('--input-path', '-i', type=click.Path(), default='.',
              help='Path to the folder with individual MOEA results')
@click.option('--output-path', '-o', type=click.Path(), default='.',
              help='Path to the folder with exported MOEA results')
@click.option('--file-type', '-f', type=str, default='json',
              help='Type of file into which the parsed results are saved')
@click.option('--vars-file-name', type=str, default='all_variables')
@click.option('--metrics-file-name', type=str, default='all_individuals')
@click.option('--output-file-type', type=str, default='csv')
def export_all_results(input_path, output_path, file_type, vars_file_name,
                       metrics_file_name, output_file_type):
    pyreto_export_all_individuals.export_all_individuals(
        input_path, output_path, file_type, vars_file_name, metrics_file_name,
        output_file_type)


@start_cli.command()
@click.option('--input-path', '-i', type=click.Path(), default='.',
              help='Path to the folder with individual MOEA results')
@click.option('--output-path', '-o', type=click.Path(), default='.',
              help='Path to the folder with exported MOEA results')
@click.option('--metrics-file-name', type=str, default='parflow_metrics')
@click.option('--output-file-type', type=str, default='csv')
def export_nondominated_results(input_path, output_path, metrics_file_name,
                                output_file_type):
    pyreto_export_nodominated.export_nondominated_results(
        input_path, output_path, metrics_file_name,
        output_file_type)


@start_cli.command()
@click.option('--file-path', '-i', type=click.Path(), default='.',
              help='Path to the folder MOEA results')
@click.option('--file-name', '-f', type=str, default='parflow_metrics')
@click.option('--no-seeds', '-n', type=int, default=3)
@click.option('--output-file-name', '-o', type=str, default='hypervolume')
@click.option('--single-seed', default=True)
@click.option('--step-size', '-ss', type=int, default=50)
def compute_hypervolume(file_path, file_name, no_seeds, output_file_name,
                        single_seed, step_size):
    pyreto_compute_hv.compute_hv(
        file_path, file_name, no_seeds, output_file_name,
        single_seed, step_size)


@start_cli.command()
@click.option('--file-name', '-f', type=click.Path(), default='hypervolume.csv')
def plot_hypervolume(file_name):
    pyreto_plot_hv.plot_hv(file_name)


if __name__ == '__main__':
    start_cli()
