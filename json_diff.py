#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for comparing two objects

Copyright (c) 2011, Red Hat Corp.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import division, absolute_import, print_function, unicode_literals
import json, sys
# import pdb
import logging
from optparse import OptionParser

__author__ = "Matěj Cepl"
__version__ = "0.9.0"

logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)

STYLE_MAP = {
    "_append": "append_class",
    "_remove": "remove_class",
    "_update": "update_class"
}
INTERNAL_KEYS = set(STYLE_MAP.keys())

LEVEL_INDENT = "&nbsp;"

out_str_template = """
<!DOCTYPE html>
<html lang='en'>
<meta charset="utf-8" />
<title>%s</title>
<style>
td {
  text-align: center;
}
.append_class {
  color: green;
}
.remove_class {
  color: red;
}
.update_class {
  color: navy;
}
</style>
<body>
  <h1>%s</h1>
  <table>
  %s
"""

# I would love to have better solution for this ...
if sys.version_info[0] == 3: unicode = str

def is_scalar(value):
    """
    Primitive version, relying on the fact that JSON cannot
    contain any more complicated data structures.
    """
    return not isinstance(value, (list, tuple, dict))

class HTMLFormatter(object):

    def __init__(self, diff_object):
        self.diff = diff_object

    def _generate_page(self, in_dict, title="json_diff result"):
        out_str = out_str_template % (title, title,
            self._format_dict(in_dict))
        out_str += """</table>
  </body>
</html>"""
        return out_str

    def _format_item(self, item, index, typch, level=0):
        level_str = ("<td>" + LEVEL_INDENT + "</td>") * level

        if is_scalar(item):
            out_str = ("<tr>\n  %s<td class='%s'>%s = %s</td>\n  </tr>\n" %
                (level_str, STYLE_MAP[typch], index, unicode(item)))
        elif isinstance(item, (list, tuple)):
            out_str = self._format_array(item, typch, level + 1)
        else:
            out_str = self._format_dict(item, typch, level + 1)
        return out_str.strip()

    def _format_array(self, diff_array, typch, level=0):
        out_str = []
        for index in range(len(diff_array)):
            out_str.append(self._format_item(diff_array[index], index, typch, level))
        return ("".join(out_str)).strip()

    # doesn't have level and neither concept of it, much
    def _format_dict(self, diff_dict, typch="unknown_change", level=0):
        out_str = []
        # For all STYLE_MAP keys which are present in diff_dict
        for typechange in set(diff_dict.keys()) & INTERNAL_KEYS:
            out_str.append(self._format_dict(diff_dict[typechange],
                 typechange, level))

        # For all other non-internal keys
        for variable in set(diff_dict.keys()) - INTERNAL_KEYS:
            out_str.append(self._format_item(diff_dict[variable],
                 variable, typch, level))

        return ("".join(out_str)).strip()

    def __str__(self):
        return self._generate_page(self.diff)

class BadJSONError(ValueError):
    pass

class Comparator(object):
    """
    Main workhorse, the object itself
    """
    def __init__(self, fn1=None, fn2=None, included_attrs=(), excluded_attrs=()):
        self.obj1 = None
        self.obj2 = None
        if fn1:
            try:
                self.obj1 = json.load(fn1)
            except (TypeError, OverflowError, ValueError) as exc:
                raise BadJSONError("Cannot decode object from JSON.\n%s" % unicode(exc))
        if fn2:
            try:
                self.obj2 = json.load(fn2)
            except (TypeError, OverflowError, ValueError) as exc:
                raise BadJSONError("Cannot decode object from JSON\n%s" % unicode(exc))
        self.excluded_attributes = excluded_attrs
        self.included_attributes = included_attrs

    def _is_incex_key(self, key, value):
        """Is this key excluded or not among included ones? If yes, it should be ignored.
        """
        key_out = ((self.included_attributes and (key not in self.included_attributes)) or
                (key in self.excluded_attributes))
        value_out = True
        if isinstance(value, dict):
            for change_key in value:
                if isinstance(value[change_key], dict):
                    for key in value[change_key]:
                        if ((self.included_attributes and (key in self.included_attributes)) or
                        (key not in self.excluded_attributes)):
                            value_out = False
        return key_out and value_out

    def _filter_results(self, result):
        """Whole -i or -x functionality. Rather than complicate logic while
        going through the object’s tree we filter the result of plain
        comparison.

        Also clear out unused keys in result"""
        out_result = {}
        for change_type in result:
            temp_dict = {}
            for key in result[change_type]:
                logging.debug("result[change_type] = %s, key = %s", unicode(result[change_type]), key)
                logging.debug("self._is_incex_key(key, result[change_type][key]) = %s",
                    self._is_incex_key(key, result[change_type][key]))
                if not self._is_incex_key(key, result[change_type][key]):
                    temp_dict[key] = result[change_type][key]
            if len(temp_dict) > 0:
                out_result[change_type] = temp_dict

        return out_result

    def _compare_elements(self, old, new):
        res = None
        # We want to go through the tree post-order
        if isinstance(old, dict):
            res_dict = self.compare_dicts(old, new)
            if (len(res_dict) > 0):
                res = res_dict
        # Now we are on the same level
        # different types, new value is new
        elif (type(old) != type(new)):
            res = new
        # recursive arrays
        # we can be sure now, that both new and old are
        # of the same type
        elif (isinstance(old, list)):
            res_arr = self._compare_arrays(old, new)
            if (len(res_arr) > 0):
                res = res_arr
        # the only thing remaining are scalars
        else:
            scalar_diff = self._compare_scalars(old, new)
            if scalar_diff is not None:
                res = scalar_diff

        return res


    def _compare_scalars(self, old, new, name=None):
        """
        Be careful with the result of this function. Negative answer from this function
        is really None, not False, so deciding based on the return value like in

        if self._compare_scalars(...):

        leads to wrong answer (it should be if self._compare_scalars(...) is not None:)
        """
        # Explicitly excluded arguments
        if old != new:
            return new
        else:
            return None

    def _compare_arrays(self, old_arr, new_arr):
        """
        simpler version of compare_dicts; just an internal method, becase
        it could never be called from outside.

        We have it guaranteed that both new_arr and old_arr are of type list.
        """
        inters = min(len(old_arr), len(new_arr)) # this is the smaller length

        result = {
            "_append": {},
            "_remove": {},
            "_update": {}
        }
        for idx in range(inters):
            res = self._compare_elements(old_arr[idx], new_arr[idx])
            if res is not None:
                result['_update'][idx] = res

        # the rest of the larger array
        if (inters == len(old_arr)):
            for idx in range(inters, len(new_arr)):
                result['_append'][idx] = new_arr[idx]
        else:
            for idx in range(inters, len(old_arr)):
                result['_remove'][idx] = old_arr[idx]

        # Clear out unused keys in result
        out_result = {}
        for key in result:
            if len(result[key]) > 0:
                out_result[key] = result[key]

        return self._filter_results(result)

    def compare_dicts(self, old_obj=None, new_obj=None):
        """
        The real workhorse
        """
        if not old_obj and hasattr(self, "obj1"):
            old_obj = self.obj1
        if not new_obj and hasattr(self, "obj2"):
            new_obj = self.obj2

        old_keys = set()
        new_keys = set()
        if old_obj and len(old_obj) > 0:
            old_keys = set(old_obj.keys())
        if new_obj and len(new_obj) > 0:
            new_keys = set(new_obj.keys())

        keys = old_keys | new_keys

        result = {
            "_append": {},
            "_remove": {},
            "_update": {}
        }
        for name in keys:
            # old_obj is missing
            if name not in old_obj:
                result['_append'][name] = new_obj[name]
            # new_obj is missing
            elif name not in new_obj:
                result['_remove'][name] = old_obj[name]
            else:
                res = self._compare_elements(old_obj[name], new_obj[name])
                if res is not None:
                    result['_update'][name] = res

        return self._filter_results(result)


if __name__ == "__main__":
    usage = "usage: %prog [options] old.json new.json"
    description = "Generates diff between two JSON files."
    parser = OptionParser(usage=usage)
    parser.add_option("-x", "--exclude",
                  action="append", dest="exclude", metavar="ATTR", default=[],
                  help="attributes which should be ignored when comparing")
    parser.add_option("-i", "--include",
                  action="append", dest="include", metavar="ATTR", default=[],
                  help="attributes which should be exclusively used when comparing")
    parser.add_option("-H", "--HTML",
                  action="store_true", dest="HTMLoutput", metavar="BOOL", default=False,
                  help="program should output to HTML report")
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error("Script requires two positional arguments, names for old and new JSON file.")

    diff = Comparator(open(args[0]), open(args[1]), options.include, options.exclude)
    if options.HTMLoutput:
        diff_res = diff.compare_dicts()
        # logging.debug("diff_res:\n%s", json.dumps(diff_res, indent=True))
        print(HTMLFormatter(diff_res))
    else:
        outs = json.dumps(diff.compare_dicts(), indent=4, ensure_ascii=False)
        outs = "\n".join([line for line in outs.split("\n")])
        print(outs.encode("utf-8"))
