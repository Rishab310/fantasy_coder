import os
import sys
import filecmp
import re
import subprocess
from subprocess import CalledProcessError, TimeoutExpired

STATUS_CODES = {
    200: 'OK',
    201: 'ACCEPTED',
    400: 'WRONG ANSWER',
    401: 'COMPILATION ERROR',
    402: 'RUNTIME ERROR',
    403: 'INVALID FILE',
    404: 'FILE NOT FOUND',
    408: 'TIME LIMIT EXCEEDED'
}


class Program:
    """ Class that handles all the methods of a user program """

    def __init__(self, filename, inputfile, timelimit, expectedoutputfile):
        """Receives a name of a file from the userIt must be a valid c, c++, java file """
        self.fileName = filename  # Full name of the source code file
        self.language = None  # Language
        self.name = None  # File name without extension
        self.inputFile = inputfile  # Input file
        self.expectedOutputFile = expectedoutputfile  # Expected output file
        self.actualOutputFile = "calculatedoutput.txt"  # Actual output file
        self.timeLimit = timelimit  # Time limit set for execution in seconds

    def isvalidfile(self):
        """ Checks if the filename is valid """
        validfile = re.compile("^(\\S+)\\.(java|cpp|c|py)$")
        matches = validfile.match(self.fileName)
        if matches:
            self.name, self.language = matches.groups()
            if self.language == 'py':
                self.language = 'python'
            return True
        return False

    def compile(self):
        """ Compiles the given program, returns status code and errors """

        # Remove previous executables
        if os.path.isfile(self.name):
            os.remove(self.name)

        # Check if files are present
        if not os.path.isfile(self.fileName):
            return 404, 'Missing file'

        # Check language
        cmd = None
        if self.language == 'java':
            cmd = 'javac {}'.format(self.fileName)
        elif self.language == 'c':
            cmd = 'gcc {1}'.format(self.name, self.fileName)
        elif self.language == 'cpp':
            cmd = 'g++ -o {0} {1}'.format(self.name, self.fileName)
        else:
            return 200, None

        # Invalid files
        if cmd is None:
            return 403, 'File is of invalid type'

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell = True
            )

            # Check for errors
            if proc.returncode != 0:
                return 401, proc.stderr
            else:
                return 200, None
        except CalledProcessError as e:
            print(e.output)

    def run(self):
        """ Runs the executable, returns status code and errors """

        # Check if files are present
        if not os.path.isfile(self.fileName) :
            return 404, 'Missing executable file'

        # Check language
        cmd = None
        if self.language == 'java':
            cmd = 'java {}'.format(self.name)
            print("JAVA COMMAND: ", cmd)
        elif self.language in ['c', 'cpp']:
            cmd = "./a.out"
            print("C COMMAND: ", cmd)
        elif self.language == 'python': cmd = 'python3 {}.py'.format(self.name)
            

        # Invalid files
        if cmd is None:
            return 403, 'File is of invalid type'

        try:
            with open('calculatedoutput.txt', 'w') as fout:
                fin = None
                if self.inputFile and os.path.isfile(self.inputFile):
                    fin = open(self.inputFile, 'r')
                proc = subprocess.call(
                    cmd,
                    stdin=fin,
                    stdout=fout,
                    stderr=subprocess.PIPE,
                    timeout=self.timeLimit,
                    shell=True,
                    universal_newlines=True
                )
            # Check for errors
            if proc != 0:
                return 402, proc.stderr
            else:
                return 200, None
        except TimeoutExpired as tle:
            print("Return error")
            return 408, tle
        except CalledProcessError as e:
            print(e.output)
        except Exception as e:
            return 408, e

        # Perform cleanup
        if self.language == 'java':
            os.remove('{}.class'.format(self.name))
        elif self.language in ['c', 'cpp']:
            os.remove(self.name)

    def match(self):
        if os.path.isfile(self.actualOutputFile) and os.path.isfile(self.expectedOutputFile):
            result = filecmp.cmp(self.actualOutputFile, self.expectedOutputFile, shallow=False)
            if result:
                return 201, None
            else:
                return 400, None
        else:
            return 404, 'Missing output files'


def codechecker(filename, inputfile=None, expectedoutput=None, timeout=1, check=True):
    newprogram = Program(
        filename=filename,
        inputfile=inputfile,
        timelimit=timeout,
        expectedoutputfile=expectedoutput
    )
    
    if newprogram.isvalidfile():
        print('Executing code checker...')
        # Compile program
        compileResult, compileErrors = newprogram.compile()
        print('Compiling... {0}({1})'.format(STATUS_CODES[compileResult], compileResult), flush=True)
        if compileErrors is not None:
            sys.stdout.flush()
            return 401, compileErrors
            print(compileErrors, file=sys.stderr)
            exit(0)

        # Run program
        runtimeResult, runtimeErrors = newprogram.run()
        print('Running... {0}({1})'.format(STATUS_CODES[runtimeResult], runtimeResult), flush=True)
        if runtimeErrors is not None:
            sys.stdout.flush()
            return runtimeResult ,runtimeErrors
            print(runtimeErrors, file=sys.stderr)
            exit(0)

        if check:
            # Match expected output
            matchResult, matchErrors = newprogram.match()
            print('Verdict... {0}({1})'.format(STATUS_CODES[matchResult], matchResult), flush=True)
            if matchErrors is not None:
                sys.stdout.flush()
                return matchResult, matchErrors
                print(matchErrors, file=sys.stderr)
                exit(0)
            return matchResult,STATUS_CODES[matchResult]
    else:
        print('FATAL: Invalid file', file=sys.stderr)


if __name__ == '__main__':

    code, msg = codechecker(
        filename='add.py',               # Source code file
        inputfile='input.txt',                  # Input file
        expectedoutput='output.txt',     # Expected output
        timeout=2,                              # Time limit
        check=True                              # Set to true to check actual output against expected output
    )
    print("----------------\n", code,msg)
