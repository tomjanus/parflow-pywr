import os

def find_output_files(directory, substr):
    """ Look in a specified directory and find all .pfb files which match a
        pattern specified as substr

        Parameters
        -----------------------------
        directory: str
            Path to the .pfb files
        substr: str
            Pattern of the output file to match

        Returns
        -----------------------------
        filename: str
            Name of the file which matches the criterion
    """

    for filename in sorted(os.listdir(directory)):
        #  skip files with a .dist extension
        #  if filename[len(filename)-4:] == 'dist':
        #    continue
        #  base, _ = os.path.splitext(filename)  # remove .00000 extension
        #  base, ext = os.path.splitext(base)
        base, ext = os.path.splitext(filename)
        if ext.lower() != '.pfb':
            continue  # skip non-pfb files
        if substr in base:
            yield filename


output_files = list(find_output_files('./outputs', 'out.press'))
days_to_remove = 900

del output_files[:days_to_remove]

for t, filename in enumerate(output_files):
    print(t+days_to_remove, filename)
