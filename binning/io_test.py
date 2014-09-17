import unittest
from io import *


class TestIO(unittest.TestCase):

    def test_empty_file(self):
        with self.assertRaises(BinningError):
            Reader('test-data/empty.txt')

    def test_missing_task(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/no-task.txt')

    def test_duplicate_key(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/dup-key.txt')

    def test_missing_key(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/missing-key.txt')

    def test_missing_value(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/missing-val.txt')

    def test_missing_version(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/no-ver.txt')

    def test_no_column_def(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/no-coldef.txt')

    def test_unknown_task(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/unk-task.txt')

    def test_unknown_version(self):
        with self.assertRaises(HeaderError):
            Reader('test-data/unk-ver.txt')

    def test_bad_number_fields(self):
        with self.assertRaises(FieldError):
            [r for r in Reader('test-data/bad-field.txt')]

    def test_valid_file(self):
        reader = Reader('test-data/valid.txt')
        self.assertEqual(5, len([r for r in reader]))


# TODO finish enumerate various tests.