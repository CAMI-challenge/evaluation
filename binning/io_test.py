import unittest
from io import *


class TestRead(unittest.TestCase):

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


class TestWrite(unittest.TestCase):

    def setUp(self):
        reader = Reader('test-data/valid.txt')
        self.rows = []
        for r in reader:
            self.rows.append(r)
        reader.close()

    def test_write_file(self):
        writer = Writer('test-data/delete.txt', overwrite=True)
        for r in self.rows:
            writer.writerow(r)
        writer.close()

    def test_no_overwrite(self):
        with self.assertRaises(BinningError):
            Writer('test-data/delete.txt', overwrite=False)

    def test_uknown_header(self):
        with self.assertRaises(HeaderError):
            writer = Writer('test-data/delete.txt', overwrite=True)
            writer._set_headinfo('foo','bar')

    def test_bad_field_number(self):
        with self.assertRaises(FieldError):
            writer = Writer('test-data/delete.txt', overwrite=True)
            writer.writerow([1,2,3,4])