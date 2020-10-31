#!/usr/bin/python
#
# Version 1.1
#   - Fix problem not picking up F word
# Version 1.2 - modified by Alexander Roessler
#   - simplfied output
#   - added argparse


import sys
import re
import argparse
import math
import tempfile


class gcode(object):
    def __init__(self):
        self.inFile = None
        self.outFile = None
        self.tmpFile = None

    def initVariables(self):
        self.regMatch = {}
        self.line_count = 0
        self.output_line_count = 0
        self.prev_p = [999999, 999999, 999999, 999999, 999999]  # high number so we detect the change on first move
        self.current_in_file = None
        self.current_out_file = None
        self.invertZ = False

    def convert(self, infile, outfile):
        self.inFile = infile
        self.outFile = outfile
        self._load(self.inFile)

    def outputLine(self, line):
        self.current_out_file.write(line + '\n')

    def loadList(self, l):
        self._load(l)

    def _load(self, gcodeFile):
        self.initVariables()
        lastx = 0
        lasty = 0
        lastz = 0
        lasta = 0
        lastf = 0

        self.current_out_file = self.outFile

        for line in gcodeFile:
            self.line_count = self.line_count + 1
            line = line.rstrip()
            original_line = line
            if type(line) is tuple:
                line = line[0]

            if str.startswith(line, ";TYPE:FILL"):
                self.invertZ = True

            if ';' in line or '(' in line:
                sem_pos = line.find(';')
                par_pos = line.find('(')
                pos = sem_pos
                if pos is None:
                    pos = par_pos
                elif par_pos is not None:
                    if par_pos > sem_pos:
                        pos = par_pos
                comment = line[pos + 1:].strip()
                line = line[0:pos]
            else:
                comment = None

            # we only try to simplify G1 coordinated moves
            G = self.getCodeInt(line, 'G')
            if G == 1:    # Move
                x = self.getCodeFloat(line, 'X')
                y = self.getCodeFloat(line, 'Y')
                z = self.getCodeFloat(line, 'Z')
                a = self.getCodeFloat(line, 'A')
                f = self.getCodeFloat(line, 'F')

                if x is None:
                    x = lastx
                if y is None:
                    y = lasty
                if z is None:
                    z = lastz
                if a is None:
                    a = lasta
                if f is None:
                    f = lastf

                if self.invertZ and z > 0:
                    z = -z

                diffx = x - lastx
                diffy = y - lasty
                diffz = z - lastz
                diffa = a - lasta

                diffxy = math.hypot(diffx, diffy)

                dead = False
                if (diffx == 0.0) and (diffy == 0.0) and (diffz == 0.0):
                    dead = True
                    self.simplifyLine(G, [x, y, z, f, None, None], comment)
                else:
                    self.simplifyLine(G, [x, y, z, f, None, None], comment)

                lastx = x
                lasty = y
                lastz = z
                lasta = a
                lastf = f

            elif (G == 0) or (G == 92):    # Rapid - remember position
                x = self.getCodeFloat(line, 'X')
                y = self.getCodeFloat(line, 'Y')
                z = self.getCodeFloat(line, 'Z')
                a = self.getCodeFloat(line, 'A')

                if x is None:
                    x = lastx
                if y is None:
                    y = lasty
                if z is None:
                    z = lastz
                if a is None:
                    a = lasta

                lastx = x
                lasty = y
                lastz = z
                lasta = a

                if G != 92:
                    self.simplifyLine(G, [x, y, z, None, None, None], comment)
            else:
                self.outputLine(original_line)
                self.output_line_count = self.output_line_count + 1

        self.outputLine("; GCode file processed by " + sys.argv[0])
        self.outputLine("; Input Line Count = " + str(self.line_count))
        self.outputLine("; Output Line Count = " + str(self.output_line_count))


    def getCodeInt(self, line, code):
        if code not in self.regMatch:
            self.regMatch[code] = re.compile(code + r'([^\s]+)', flags=re.IGNORECASE)
        m = self.regMatch[code].search(line)
        if m is None:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    def getCodeFloat(self, line, code):
        if code not in self.regMatch:
            self.regMatch[code] = re.compile(code + r'([^\s]+)', flags=re.IGNORECASE)
        m = self.regMatch[code].search(line)
        if m is None:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None

    def simplifyLine(self, g, p, c):
        self.output_line_count = self.output_line_count + 1
        #print "i, g,p,c=", i, g,p,c
        s = "G" + str(g) + " "
        # if (p[0] is not None) and (p[0] != self.prev_p[0]):
        if (p[0] is not None):
            self.prev_p[0] = p[0]
            s = s + "X{0:g}".format(p[0]) + " "
        # if (p[1] is not None) and (p[1] != self.prev_p[1]):
        if (p[1] is not None):
            self.prev_p[1] = p[1]
            s = s + "Y{0:g}".format(p[1]) + " "
        if (p[2] is not None) and (p[2] != self.prev_p[2]):
        # if (p[2] is not None):
            self.prev_p[2] = p[2]
            s = s + "Z{0:g}".format(p[2]) + " "
        # if (p[3] is not None) and (p[3] != self.prev_p[3]):
        if (p[3] is not None):
            self.prev_p[3] = p[3]
            s = s + "F{0:g}".format(p[3]) + " "
        if p[4] is not None:
            s = s + "I{0:g}".format(p[4]) + " "
        if p[5] is not None:
            s = s + "J{0:g}".format(p[5]) + " "
        if c is not None:
            s = s + "; " + c
        s = s.rstrip()
        self.outputLine(s)

    def compareValue(self, newValue, oldValue, tolerance):
        return (newValue < (oldValue * (1.0 - tolerance))) \
               or (newValue > (oldValue * (1.0 + tolerance)))



def main():
    parser = argparse.ArgumentParser(description='This application simplifies G1 straight feeds to G2 and G3 arc moves')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), help='input file, takes input from stdin if not specified')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), help='output file, prints output to stdout of not specified')
    parser.add_argument('-p', '--plane', type=int, default=17,
                        help='plane parameter')
    parser.add_argument('-pt', '--point_tolerance', type=float, default=0.05,
                        help='point tolerance parameter')
    parser.add_argument('-lt', '--length_tolerance', type=float, default=0.005,
                        help='length tolerance parameter')
    parser.add_argument('-d', '--debug', help='enable debug mode', action='store_true')
    args = parser.parse_args()

    inFile = args.infile
    outFile = args.outfile

    gcode().convert(inFile, outFile)

    inFile.close()
    outFile.close()


if __name__ == "__main__":
    main()