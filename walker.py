
import os

# specify the directory you want to start from
rootDir = '.'  # replace with your desired directory

# specify the types of files
file_types = ['.py', '.js', '.ts', '.json']
ignore_dirs = ['venv', 'node_modules', '.next', 'temp']
ignore_files = ['walker.py', 'package.json', 'data.json']

# open the output file
with open('combined_code.txt', 'w') as outfile:
    # traverse directory
    for dirName, subdirList, fileList in os.walk(rootDir):
        # skip ignored directories
        subdirList[:] = [d for d in subdirList if d not in ignore_dirs]
        # skip ignored files
        fileList[:] = [f for f in fileList if f not in ignore_files]
        for fname in fileList:
            # check if file has the desired extension
            if any(fname.endswith(ft) for ft in file_types):
                file_path = os.path.join(dirName, fname)
                outfile.write(f'// {file_path}\n')
                with open(file_path, 'r') as infile:
                    # read each line of the file and write it to the output file
                    for line in infile:
                        outfile.write(line)
                outfile.write('\n\n')

