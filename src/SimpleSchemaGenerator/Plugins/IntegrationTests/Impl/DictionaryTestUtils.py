# ----------------------------------------------------------------------
# |
# |  DictionaryTestUtils.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-02-12 22:05:58
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Helpers for DictionaryTests tests"""

import os

import six

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DictionaryTestMixin(object):
    # ----------------------------------------------------------------------
    def ValidateSimpleDict(self, obj):
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj["key1"], [10, 20, 30])
        self.assertTrue("key2" not in obj)
        self.assertEqual(obj["key3"], [100])

    # ----------------------------------------------------------------------
    def ValidateStandardDict(self, obj):
        self.assertEqual(len(obj), 3)
        self.assertEqual(list(six.iterkeys(obj)), ["key1", "key2", "key3"])
        self.assertEqual([(item.first, getattr(item, "middle", None), item.last) for item in six.itervalues(obj)], [("first1", None, "last1"), ("first2", "middle2", "last2"), ("first3", None, "last3")])

    # ----------------------------------------------------------------------
    def ValidateNestedDict(self, obj):
        self.assertEqual(len(obj), 2)
        self.assertEqual(list(six.iteritems(obj["key1"])), [("keyA", ["10", "20", "30"])])
        self.assertEqual(list(six.iteritems(obj["key2"])), [("keyC", ["1000"]), ("keyD", ["100", "200"])])
