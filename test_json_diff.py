# -*- coding: utf-8 -*-
"""
PyUnit unit tests
"""
import unittest
import json
import json_diff
from StringIO import StringIO

SIMPLE_OLD = u"""
{
    "a": 1,
    "b": true,
    "c": "Janošek"
}
"""

SIMPLE_NEW = u"""
{
    "b": false,
    "c": "Maruška",
    "d": "přidáno"
}
"""

SIMPLE_DIFF =  u"""
{
    "append": {
        "d": "přidáno"
    },
    "remove": {
        "a": 1
    },
    "update": {
        "c": "Maruška",
        "b": false
    }
}
"""

NESTED_OLD = u"""
{
    "a": 1,
    "b": 2,
    "son": {
        "name": "Janošek"
    }
}
"""

NESTED_NEW = u"""
{
    "a": 2,
    "c": 3,
    "daughter": {
        "name": "Maruška"
    }
}
"""

NESTED_DIFF = u"""
{
    "append": {
        "c": 3,
        "daughter": {
            "name": "Maruška"
        }
    },
    "remove": {
        "b": 2,
        "son": {
            "name": "Janošek"
        }
    },
    "update": {
        "a": 2
    }
}
"""

class TestXorgAnalyze(unittest.TestCase):
    def test_empty(self):
        diffator = json_diff.Comparator({}, {})
        diff = diffator.compare_dicts()
        self.assertEqual(json.dumps(diff).strip(), "{}", \
             "Empty objects diff.\n\nexpected = %s\n\nobserved = %s" % \
             (str({}), str(diff)))

    def test_simple(self):
        diffator = json_diff.Comparator(StringIO(SIMPLE_OLD), StringIO(SIMPLE_NEW))
        diff = diffator.compare_dicts()
        expected = json.loads(SIMPLE_DIFF)
        self.assertEqual(diff, expected, "All-scalar objects diff." + \
                         "\n\nexpected = %s\n\nobserved = %s" % \
                         (str(expected), str(diff)))

    def test_realFile(self):
        diffator = json_diff.Comparator(open("test/old.json"), open("test/new.json"))
        diff = diffator.compare_dicts()
        expected = json.load(open("test/diff.json"))
        self.assertEqual(diff, expected, "Simply nested objects (from file) diff." + \
                         "\n\nexpected = %s\n\nobserved = %s" % \
                         (str(expected), str(diff)))

    def test_nested(self):
        diffator = json_diff.Comparator(StringIO(NESTED_OLD), StringIO(NESTED_NEW))
        diff = diffator.compare_dicts()
        expected = json.loads(NESTED_DIFF)
        self.assertEqual(diff, expected, "Nested objects diff. " + \
                         "\n\nexpected = %s\n\nobserved = %s" % \
                         (str(expected), str(diff)))
    def test_large_with_exclusions(self):
        diffator = json_diff.Comparator(open("test/old-testing-data.json"), \
                    open("test/new-testing-data.json"), ('command', 'time'))
        diff = diffator.compare_dicts()
        expected = json.load(open("test/diff-testing-data.json"))
        self.assertEqual(diff, expected, "Large objects with exclusions diff." + \
                         "\n\nexpected = %s\n\nobserved = %s" % \
                         (str(expected), str(diff)))

if __name__ == "__main__":
    unittest.main()