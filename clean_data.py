import glob

files = glob.glob('*.txt')


import fileinput
import sys

for i in files:
    for line_number, line in enumerate(fileinput.input(i, inplace=1)):
      if line_number == 0 or line_number == 2:
        continue
      else:
        sys.stdout.write(line)
