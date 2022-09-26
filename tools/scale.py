#!/usr/bin/python3

# Script to scale sandtrail tracks to use the full space available.
# Parses a theta/rho coordinate file as obtained on sandify.org (.thr) and finds the maximum rho value
# Uses this value to scale all the rho coordinates such that the maximum rho becomes 1

import sys

def is_coordinate_line(line):
    return (not line.startswith('#')) and len(line.split()) == 2

def parse_line(line):
    return line.split()

def write_scaled(inp_name, oup_name, scale):
    with open(inp_name, 'r') as inp:
        with open(oup_name, 'w') as oup:
            line = inp.readline()
            while line:
                stripped = line.strip()
                if is_coordinate_line(stripped):
                    fields = parse_line(stripped)
                    theta = fields[0]
                    rho = float(fields[1])
                    scaled_rho = rho * scale
                    oup.write(theta + " {:.5f}\n".format(scaled_rho))
                else:
                    oup.write(line)
                line = inp.readline()
        
def find_max_rho(inp_name):
    max_rho = 0
    with open(inp_name, 'r') as inp:
        line = inp.readline()
        while line:
            stripped = line.strip()
            if is_coordinate_line(stripped):
                fields = parse_line(stripped)
                rho = float(fields[1])
                if rho > max_rho:
                    max_rho = rho
            line = inp.readline()
    return max_rho        

if len(sys.argv) < 2:
    print("Usage: python3 script_name input_filename [maximum_rho]")
    print("Example: python3 scale.py myfile.thr")
    sys.exit(2)

inp_name = sys.argv[1]
oup_name = inp_name[0:-4] if inp_name.endswith('.thr') else inp_name
oup_name = oup_name + "_scaled.thr" 

max_scale = 0.99 if len(sys.argv) < 3 else float(sys.argv[2])
print("Maximum rho should become: " + str(max_scale))

max_rho = find_max_rho(inp_name)
scale = max_scale / max_rho
print("Maximum found rho value is: " + str(max_rho))
print("Scaling all rho values by factor: " + str(scale))

write_scaled(inp_name, oup_name, scale)
print("Done writing new file with scaled rho values to: " + oup_name)