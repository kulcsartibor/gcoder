
import sys
import argparse
import re
import tempfile

def main():
    parser = argparse.ArgumentParser(description='This application converts RepRap flavour GCode to Machinekit flavour GCode')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help='input file, takes input from stdin if not specified')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help='output file, prints output to stdout of not specified')
    parser.add_argument('-d', '--debug', help='enable debug mode', action='store_true')
    parser.add_argument('-z', '--safe_z', type=float, default=2.0,  help='Safe Z coordinate')
    args = parser.parse_args()

    safe_z_coord = args.safe_z

    inFile = args.infile
    outFile = args.outfile

    current_z = safe_z_coord

    mod_z = False

    for line in inFile:
        if str.startswith(line, ";TYPE:FILL"):
            mod_z = True

        if bool(re.match('G\d+( F\d+)? A[-\d\.]+', line)):
            continue

        newline = re.sub('A\d+\.\d+', '', line).strip()
        if mod_z:
            newline = re.sub('Z((\d+\.)?\d+)', 'Z-\\1', newline)

        m = re.search('Z(-?\d*\.?\d+)', newline)
        if m is not None:
            current_z = m.group(1)

        if str.startswith(newline, 'G0'):
            outFile.write('G1 F600 Z' + str(safe_z_coord) + '\n')
            outFile.write(newline + '\n')
            outFile.write('G1 F600 Z' + str(current_z) + '\n')
            continue

        outFile.write(newline + '\n')

    inFile.close()
    outFile.close()

    exit(0)

if __name__ == "__main__":
    main()