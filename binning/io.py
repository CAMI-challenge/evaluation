"""
CAMI IO
"""
import os.path
import re

# Global constants
COMMENT_CHAR = '#'
HEADER_CHAR = '@'
FIELD_SEP = '\t'
HEADER_SEP = ':'

# Header keys
TASK_KEY = 'task'
VERSION_KEY = 'version'
CONID_KEY = 'contestantid'
SAMPLEID_KEY = 'sampleid'
REFBASED_KEY = 'referencebased'
ASMBASED_KEY = 'assemblybased'
REPINFO_KEY = 'replicateinfo'

class Writer(object):

    __columns = ['SEQUENCEID', 'BINID', 'TAXID']

    def __init__(self, filename, overwrite=False):
        self.header_info = {
            'task': 'binning',
            'version': 1.0,
            'contestantid': '',
            'sampleid': '',
            'referencebased': 'F',
            'assemblybased': 'F',
            'replicateinfo': 'F'
        }
        if not overwrite and os.path.exists(filename):
            raise BinningError('output file {0} already exists'.format(filename))
        self.file_handle = open(filename, 'w')
        self._write_header()

    #
    # Helper function to set internal dictionary fields on header info
    #
    def _set_headinfo(self, key, value):
        if key not in self.header_info:
            raise HeaderError('unknown header info field {0}'.format(key))
        self.header_info[key] = value

    #
    # Public methods for setting various header fields.
    #
    # version and task are not exposed to users.
    #
    def set_contestantid(self, contestant):
        self._set_headinfo(CONID_KEY, contestant)

    def set_sampleid(self, sample):
        self._set_headinfo(SAMPLEID_KEY, sample)

    def set_reference_based(self):
        self._set_headinfo(REFBASED_KEY, 'T')

    def set_assembly_based(self):
        self._set_headinfo(ASMBASED_KEY, 'T')

    def set_replicate_info(self):
        self._set_headinfo(REPINFO_KEY, 'T')


    #
    # Write a line with implicit newline
    #
    def _writeline(self, line):
        self.file_handle.write(line + '\n')

    #
    # Write the header record
    #
    def _write_header(self):
        self._writeline('#CAMI Format for Binning')
        for k, v in self.header_info.iteritems():
            self._writeline('@{0}{1}{2}'.format(k, HEADER_SEP, v))
        self._writeline('@@{0}'.format(FIELD_SEP.join(Writer.__columns)))

    #
    # Write a single row
    #
    def writerow(self, row):
        if len(row) != len(Writer.__columns):
            raise FieldError('number of fields {0} does not agree with columns'.format(row, Writer.__columns))
        self._writeline(FIELD_SEP.join(row))
        pass

    #
    # Close underlying file
    #
    def close(self):
        self.file_handle.close()


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
        if len(sys.argv) != 3:
            print 'usage: [input file] [output file]'
            sys.exit(1)

        reader = Reader(sys.argv[1])
        print reader.columns
        data_rows = []
        for row in reader:
            print row
            data_rows.append(row)
        reader.close()

        writer = Writer(sys.argv[2])
        for row in data_rows:
            writer.writerow(row)
        writer.close()

    except IOError as e:
        print e
