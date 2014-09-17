"""
CAMI IO
"""
import re


# Global constants
COMMENT_CHAR = '#'
HEADER_CHAR = '@'
FIELD_SEP = '\t'
TASK_KEY = 'task'
VERSION_KEY = 'version'
HEADER_SEP = ':'


class Writer(object):


    def __init__(self):
        pass


    def writerow(self, row):
        pass


class Reader(object):

    # define header fields which are mandatory
    __supports = {TASK_KEY: ['binning'], VERSION_KEY: ['1.0']}

    #
    # Test for a blank line
    #
    @staticmethod
    def _is_blank(line):
        return re.match('^\s*$', line) is not None

    #
    # Test for a comment line
    #
    @staticmethod
    def _is_comment(line):
        return line.startswith(COMMENT_CHAR)

    def __init__(self, filename):
        self.line_number = 0
        self.version_value = None
        self.filename = filename
        self.file_handle = open(filename, 'r')
        # TODO casting header information values, such as T => True.
        self.header_info = {}
        self.columns = []
        self._read_header()


    def __iter__(self):
        return self

    #
    # Check if manadatory fields in header have been set.
    #
    def _check_mandatory_set(self):
        if TASK_KEY not in self.header_info:
            raise HeaderError('format version not declared')
        if VERSION_KEY not in self.header_info:
            raise HeaderError('task type not declared')

    #
    # Read a line of the underlying file and increment line counter
    #
    def _readline(self):
        line = self.file_handle.next().strip()
        self.line_number += 1
        return line

    #
    # Parse the header lines and test-data that the reader supports
    # the file type.
    #
    def _header_parse(self, line):

        # header line is sufficiently long and potentially contains a key/value pair
        if len(line) < 4 or line.count(HEADER_SEP) != 1:
            raise HeaderError('malformed header line:{0}'.format(line))

        # split key and value, test-data for basic validity
        key, value = [l.lower() for l in line[1:].split(HEADER_SEP)]
        if len(key) <= 0:
            raise HeaderError('header does not appear to contain a key. line:{0} [{1}]'.format(self.line_number, line))
        elif len(value) <= 0:
            raise HeaderError('header does not appear to contain a value. line:{0} [{1}]'.format(self.line_number, line))

        if key in self.header_info:
            raise HeaderError('duplicate header key used. line:{0} [{1}]'.format(self.line_number, line))
        self.header_info[key] = value

        # test-data each header definition type is supported
        for k, v in Reader.__supports.iteritems():
            if key == k and value not in v:
                # TODO add explanation of what _is_ supported
                raise HeaderError('reader does not support the file type definition. line:{0} [{1}]'
                                  .format(self.line_number, line))

    #
    # Read the complete header, raise errors if malformed.
    # After completion, the file point should sit at the beginning
    # of actual data records.
    #
    def _read_header(self):
        while True:
            try:
                line = self._readline()
            except StopIteration:
                raise HeaderError('incomplete header, file ended at line:{0}'.format(self.line_number))

            # skip blank and comment lines
            if Reader._is_blank(line) or Reader._is_comment(line):
                continue

            # column definitions line, which marks the end of the header
            elif line.startswith(HEADER_CHAR * 2):
                self.columns = line[2:].split(FIELD_SEP)
                break

            # skip header lines, but test-data for validity
            elif line.startswith(HEADER_CHAR):
                self._header_parse(line)

        # Check that task and version are set within header
        self._check_mandatory_set()

    #
    # Close underlying input file
    #
    def close(self):
        self.file_handle.close()

    #
    # Read next line
    #
    def next(self):
        line = self._readline()
        if line is StopIteration:
            return StopIteration

        # skip blank and comment lines
        if Reader._is_blank(line) or Reader._is_comment(line):
            return self.next()

        values = line.split(FIELD_SEP)
        if len(values) != len(self.columns):
            raise FieldError('incorrect number of fields for line:{0} [{1}]'.format(self.line_number, line))

        return values

    #
    # Get header based information.
    #
    def get_info(self, key):
        return self.header_info[key]


#
# Local exception classes
#
class BinningError(IOError):
    pass


class FieldError(BinningError):
    pass


class HeaderError(BinningError):
    pass

#
# Basic cli for testing
#
if __name__ == '__main__':

    import sys

    try:
        if len(sys.argv) != 2:
            print 'usage: [cami tax binning file]'
            sys.exit(1)

        reader = Reader(sys.argv[1])
        print reader.columns
        for row in reader:
            print row

    except IOError as e:
        print e
