import unittest
from io import *


class TestBinningRead(unittest.TestCase):

    def test_empty_file(self):
        with self.assertRaises(ParseError):
            BinningReader('test-data/binning-empty.txt')
        with self.assertRaises(ParseError):
            ProfileReader('test-data/profile-empty.txt')

    def test_missing_task(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/binning-no-task.txt')
        with self.assertRaises(HeaderError):
            ProfileReader('test-data/profile-no-task.txt')

    def test_duplicate_key(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/dup-key.txt')

    def test_missing_key(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/missing-key.txt')

    def test_missing_value(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/missing-val.txt')

    def test_missing_version(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/binning-no-ver.txt')
        with self.assertRaises(HeaderError):
            ProfileReader('test-data/profile-no-ver.txt')

    def test_no_column_def(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/binning-no-coldef.txt')
        with self.assertRaises(HeaderError):
            ProfileReader('test-data/profile-no-coldef.txt')

    def test_unknown_task(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/binning-unk-task.txt')
        with self.assertRaises(HeaderError):
            ProfileReader('test-data/profile-unk-task.txt')

    def test_unknown_version(self):
        with self.assertRaises(HeaderError):
            BinningReader('test-data/binning-unk-ver.txt')
        with self.assertRaises(HeaderError):
            ProfileReader('test-data/profile-unk-ver.txt')

    def test_bad_row(self):
        with self.assertRaises(FieldError):
            [r for r in BinningReader('test-data/binning-bad-row.txt')]
            [r for r in ProfileReader('test-data/profile-bad-row.txt')]


    def test_valid_file(self):
        reader = BinningReader('test-data/binning-valid.txt')
        self.assertEqual(5, len([r for r in reader]))

        reader = ProfileReader('test-data/profile-valid.txt')
        self.assertEqual(12, len([r for r in reader]))


class TestBinningWrite(unittest.TestCase):

    def setUp(self):

        self.bin_rows = []
        self.pro_rows = []

        with BinningReader('test-data/binning-valid.txt') as reader:
            for r in reader:
                self.bin_rows.append(r)

        with ProfileReader('test-data/profile-valid.txt') as reader:
            for r in reader:
                self.pro_rows.append(r)

    def test_write_file(self):
        with BinningWriter('test-data/binning-delete.txt', overwrite=True) as writer:
            for r in self.bin_rows:
                writer.writerow(r)

        with ProfileWriter('test-data/profile-delete.txt', overwrite=True) as writer:
            for r in self.pro_rows:
                writer.writerow(r)

    def test_no_overwrite(self):
        with self.assertRaises(ParseError):
            BinningWriter('test-data/binning-delete.txt', overwrite=False)

        with self.assertRaises(ParseError):
            ProfileWriter('test-data/profile-delete.txt', overwrite=False)

    def test_unknown_header(self):
        with self.assertRaises(HeaderError):
            with BinningWriter('test-data/binning-delete.txt', overwrite=True) as writer:
                writer._set_headinfo('foo', 'bar')

        with self.assertRaises(HeaderError):
            with ProfileWriter('test-data/profile-delete.txt', overwrite=True) as writer:
                writer._set_headinfo('foo', 'bar')

    def test_bad_field_number(self):
        with self.assertRaises(FieldError):
            with BinningWriter('test-data/binning-delete.txt', overwrite=True) as writer:
                writer.writerow([99] * 20)

        with self.assertRaises(FieldError):
            with ProfileWriter('test-data/profile-delete.txt', overwrite=True) as writer:
                writer.writerow([99] * 20)