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
import sys
import re

# Global constants
HEADER_COMMENT = '#CAMI Format for Binning'
COMMENT_CHAR = '#'
HEADER_CHAR = '@'
DELIMITER = '\t'
HEADER_SEP = ':'

# Generic keys
TASK_KEY = 'task'
VERSION_KEY = 'version'
CONID_KEY = 'contestantid'
SAMPLEID_KEY = 'sampleid'

# Binning constants
BIN_TASK = 'binning'
BIN_VERSION_SUPPORT = ['1.0']
REFBASED_KEY = 'referencebased'
ASMBASED_KEY = 'assemblybased'
REPINFO_KEY = 'replicateinfo'
BIN_COLUMN_DEFINITION = ['SEQUENCEID', 'TAXID', 'BINID']
BIN_MANDATORY_FIELDS = [REFBASED_KEY, ASMBASED_KEY, REPINFO_KEY]

# Profile constants
PRO_TASK = 'profiling'
PRO_VERSION_SUPPORT = ['1.0']
RANKS_KEY = 'ranks'
PRO_COLUMN_DEFINITION = ['TAXID', 'RANK', 'TAXPATH', 'TAXPATH_SN', 'PERCENTAGE']
PRO_MANDATORY_FIELDS = [RANKS_KEY]


class Writer(object):
    """
    Writer

    Opens a file on instantiation and validates header information. Provides iterator
    access to each subsequent data line, returned as a list of values.
    """

    def __enter__(self):
        """
        Instantiate class within with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit method for use within with statement. Closes underlying file.
        """
        self.close()

    def __init__(self, filename, additional_header_info, column_definition, overwrite=False):
        """
        Instatiate the Writer class for a given filename.
        :param filename: the filename to write
        :param additional_header_info: addition header fields for a concrete class
        :param column_definition: columns defined for a concrete class
        :param overwrite: boolean flag for file overwriting
        :raises: BinningError when output file already exists and overwrite is False
        """
        self.header_info = {
            TASK_KEY: '',
            VERSION_KEY: '',
            CONID_KEY: '',
            SAMPLEID_KEY: ''
        }
        self.header_info.update(additional_header_info)
        self.column_definition = column_definition

        if not overwrite and os.path.exists(filename):
            raise ParseError('output file {0} already exists'.format(filename))
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

    def _writeline(self, line):
        """
        Write a single line to the file
        :param line: the line to write to the file
        """
        self.file_handle.write(line + '\n')

    def _write_header(self):
        """
        Write the header to the file. This includes all the defined metadata.
        """
        self._writeline(HEADER_COMMENT)
        for k, v in self.header_info.iteritems():
            self._writeline('{0}{1}{2}{3}'.format(HEADER_CHAR, k, HEADER_SEP, v))
        self._writeline('{0}{1}'.format(HEADER_CHAR*2, DELIMITER.join(self.column_definition)))

    def writerow(self, row):
        """
        Write a row of values to the file.
        :param row: the row of values, corresponding to the column order.
        :raises FieldError when the number of fields does not agree with the defined number of columns
        """
        if len(row) != len(self.column_definition):
            raise FieldError('number of fields {0} does not agree with columns'.format(row, self.column_definition))
        self._writeline(DELIMITER.join(row))
        pass

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

    @staticmethod
    def _is_blank(line):
        """
        Test if a line is blank

        :param line: the line to check
        :return: return True if line contains only white space
        """
        return re.match('^\s*$', line) is not None

    @staticmethod
    def _is_comment(line):
        """
        Test if a line is a comment

        :param line: the line to test
        :return: return True if the line is a comment (begins with #)
        """
        return line.startswith(COMMENT_CHAR)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __init__(self, filename, task_name, version_support, mandatory_header_fields, column_definition):
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
        self.supports = {TASK_KEY: [task_name], VERSION_KEY: version_support}
        self.column_definition = column_definition
        self.mandatory_header_fields = [TASK_KEY, VERSION_KEY, CONID_KEY, SAMPLEID_KEY] + mandatory_header_fields
        self._read_header()


    def __iter__(self):
        """
        :return: return an iterator for the class
        """
        return self

    def _check_mandatory_set(self):
        """
        Check if the mandatory header fields have been included.
        :return: returns True if mandatory fields are found
        """
        for mf in self.mandatory_header_fields:
            if mf not in self.header_info:
                raise HeaderError('mandatory header field {0} was not found'.format(mf))


    def _readline(self):
        """
        Read a line from the file.
        :return: return the line as a string, stripped.
        """
        line = self.file_handle.next().strip()
        self.line_number += 1
        return line

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
        for k, v in self.supports.iteritems():
            if key == k and value not in v:
                # TODO add explanation of what _is_ supported
                raise HeaderError('reader does not support the file type definition. line:{0} [{1}]'
                                  .format(self.line_number, line))

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
                cols = line[2:].split(DELIMITER)
                if cols != self.column_definition:
                    raise HeaderError('column definition incorrect at line:{0} {1} '
                                      'should be {2}'.format(self.line_number, line, self.column_definition))
                break

            # skip header lines, but test-data for validity
            elif line.startswith(HEADER_CHAR):
                self._header_parse(line)

        # Check that task and version are set within header
        self._check_mandatory_set()

    def close(self):
        """
        Close the underlying file
        """
        self.file_handle.close()

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

        values = line.split(DELIMITER)
        if len(values) != len(self.column_definition):
            raise FieldError('incorrect number of fields for line:{0} [{1}]'.format(self.line_number, line))

        return values

    def get_info(self, key):
        """
        Return parsed header information.
        :param key: the key to return
        :return: value for the given key
        """
        return self.header_info[key]

    def print_headerinfo(self, handle=sys.stdout):
        """
        Print out the full dictionary of head info
        :param handle: file handle which to print
        """
        for k, v in self.header_info.iteritems():
            print >> handle, '{0}={1}'.format(k, v)


#
#  BINNING IO
#

class BinningWriter(Writer):
    """
    Concrete class for CAMI binning format.
    """

    def __init__(self, filename, overwrite=False):

        binning_header_info = {
            TASK_KEY: BIN_TASK,
            VERSION_KEY: 1.0,
            REFBASED_KEY: 'F',
            ASMBASED_KEY: 'F',
            REPINFO_KEY: 'F'
        }

        super(BinningWriter, self).__init__(
            filename, binning_header_info, BIN_COLUMN_DEFINITION, overwrite)

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


class BinningReader(Reader):
    """
    Concrete class for reading CAMI binning format
    """
    def __init__(self, filename):
        super(BinningReader, self).__init__(
            filename, BIN_TASK, BIN_VERSION_SUPPORT, BIN_MANDATORY_FIELDS, BIN_COLUMN_DEFINITION)


#
# PROFILE IO
#

class ProfileWriter(Writer):
    """
    Concreate class for writing CAMI profiling format.
    """
    def __init__(self, filename, overwrite=False):

        profiling_header_info = {
            TASK_KEY: PRO_TASK,
            VERSION_KEY: 1.0,
            RANKS_KEY: 'superkingdom|phylum|class|order|family|genus|species|strain'
        }

        super(ProfileWriter, self).__init__(
            filename, profiling_header_info, PRO_COLUMN_DEFINITION, overwrite)

class ProfileReader(Reader):
    """
    Concrete class for reading CAMI profiling format
    """
    def __init__(self, filename):
        super(ProfileReader, self).__init__(
            filename, PRO_TASK, PRO_VERSION_SUPPORT, PRO_MANDATORY_FIELDS, PRO_COLUMN_DEFINITION)

#
# Error types
#

class ParseError(IOError):
    """
    Base error class
    """
    pass


class FieldError(ParseError):
    """
    Data field errors
    """
    pass


class HeaderError(ParseError):
    """
    Header errors
    """
    pass
