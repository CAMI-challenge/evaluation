"""
Binning IO module

This module intends to provide basic read and write of the CAMI Binning file format.

The format consists of an informational header and a tab-delimited body.

Line types:

Comment lines.

    # a comment

Header lines, which carry metadata.

    @foobar:123

Column definition line.

    @@SEQUENCEID{tab}TAXID{tab}BINID

Data line.

    read001{tab}123{tab}321

Where {tab} represents a single tab character.

"""
import os.path
import re

# Global constants
HEADER_COMMENT = '#CAMI Format for Binning'
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
    """
    Writer

    Opens a file on instantiation and validates header information. Provides iterator
    access to each subsequent data line, returned as a list of values.
    """
    __columns = ['SEQUENCEID', 'BINID', 'TAXID']

    def __init__(self, filename, overwrite=False):
        """
        Instatiate the Writer class for a given filename.
        :param filename: the filename to write
        :param overwrite: boolean flag for file overwriting
        :raises: BinningError when output file already exists and overwrite is False
        """
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

    def _set_headinfo(self, key, value):
        """
        Helper function to set internal dictionary fields on header info
        :param key: header key to set
        :param value: the value
        """
        if key not in self.header_info:
            raise HeaderError('unknown header info field {0}'.format(key))
        self.header_info[key] = value

    #
    # Public methods for setting various header fields.
    #
    # version and task are not exposed to users.
    #
    def set_contestantid(self, contestant):
        """
        Set the contestant id
        :param contestant:
        """
        self._set_headinfo(CONID_KEY, contestant)

    def set_sampleid(self, sample):
        """
        Set the sample id
        :param sample:
        """
        self._set_headinfo(SAMPLEID_KEY, sample)

    def set_reference_based(self):
        """
        Set reference based to true
        """
        self._set_headinfo(REFBASED_KEY, 'T')

    def set_assembly_based(self):
        """
        Set assembly based to true
        """
        self._set_headinfo(ASMBASED_KEY, 'T')

    def set_replicate_info(self):
        """
        Set replicate info to true
        """
        self._set_headinfo(REPINFO_KEY, 'T')


    #
    # Write a line with implicit newline
    #
    def _writeline(self, line):
        """
        Write a single line to the file
        :param line: the line to write to the file
        """
        self.file_handle.write(line + '\n')

    #
    # Write the header record
    #
    def _write_header(self):
        """
        Write the header to the file. This includes all the defined metadata.
        """
        self._writeline(HEADER_COMMENT)
        for k, v in self.header_info.iteritems():
            self._writeline('@{0}{1}{2}'.format(k, HEADER_SEP, v))
        self._writeline('@@{0}'.format(FIELD_SEP.join(Writer.__columns)))

    #
    # Write a single row
    #
    def writerow(self, row):
        """
        Write a row of values to the file.
        :param row: the row of values, corresponding to the column order.
        :raises FieldError when the number of fields does not agree with the defined number of columns
        """
        if len(row) != len(Writer.__columns):
            raise FieldError('number of fields {0} does not agree with columns'.format(row, Writer.__columns))
        self._writeline(FIELD_SEP.join(row))
        pass

    #
    # Close underlying file
    #
    def close(self):
        """
        Close the underlying file
        """
        self.file_handle.close()


class Reader(object):
    """
    Reader

    Read from a given CAMI binning file. Provides an iterator over the data lines
    where each row is returned as a list of values ordered by column definition.

    """

    # define header fields which are mandatory
    __supports = {TASK_KEY: ['binning'], VERSION_KEY: ['1.0']}

    #
    # Test for a blank line
    #
    @staticmethod
    def _is_blank(line):
        """
        Test if a line is blank

        :param line: the line to check
        :return: return True if line contains only white space
        """
        return re.match('^\s*$', line) is not None

    #
    # Test for a comment line
    #
    @staticmethod
    def _is_comment(line):
        """
        Test if a line is a comment

        :param line: the line to test
        :return: return True if the line is a comment (begins with #)
        """
        return line.startswith(COMMENT_CHAR)

    def __init__(self, filename):
        """
        Instantiate a Reader. The parser will open and read the header
        as part of instantiation.

        :param filename: the filename of the input file.
        :return:
        """
        self.line_number = 0
        self.version_value = None
        self.filename = filename
        self.file_handle = open(filename, 'r')
        # TODO casting header information values, such as T => True.
        self.header_info = {}
        self.columns = []
        self._read_header()


    def __iter__(self):
        """
        :return: return an iterator for the class
        """
        return self

    #
    # Check if manadatory fields in header have been set.
    #
    def _check_mandatory_set(self):
        """
        Check if the mandatory header fields have been included.
        :return: returns True if mandatory fields are found
        """
        if TASK_KEY not in self.header_info:
            raise HeaderError('format version not declared')
        if VERSION_KEY not in self.header_info:
            raise HeaderError('task type not declared')

    #
    # Read a line of the underlying file and increment line counter
    #
    def _readline(self):
        """
        Read a line from the file.
        :return: return the line as a string, stripped.
        """
        line = self.file_handle.next().strip()
        self.line_number += 1
        return line

    #
    # Parse the header lines and test-data that the reader supports
    # the file type.
    #
    def _header_parse(self, line):
        """
        Parse a line of the header
        :param line: the line to parse
        :raises: HeaderError when a line is invalid given its context
        """

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
        """
        Read the entire header and validate it.
        :raises: HeaderError when the header is truncated.
        """
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
        """
        Close the underlying file
        """
        self.file_handle.close()

    #
    # Read next line
    #
    def next(self):
        """
        Iterator over data lines.
        :return: the next row of values in the data table
        """
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
        """
        Return parsed header information.
        :param key: the key to return
        :return: value for the given key
        """
        return self.header_info[key]


#
# Local exception classes
#
class BinningError(IOError):
    """
    Base error class
    """
    pass


class FieldError(BinningError):
    """
    Data field errors
    """
    pass


class HeaderError(BinningError):
    """
    Header errors
    """
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
