#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import XDiff

class TestXDiff(unittest.TestCase):
    def test_XDiff(self):
        XDiff.XDiff('old.xml', 'new.xml', 'diff.xml')
        self.assertTrue(True, "we have managed to get through XDiff.")