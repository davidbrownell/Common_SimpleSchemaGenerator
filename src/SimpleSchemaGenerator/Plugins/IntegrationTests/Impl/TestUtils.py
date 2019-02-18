# ----------------------------------------------------------------------
# |
# |  TestUtils.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-18 09:18:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Helpers for Test tests"""

import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestUtilsMixin(object):
    # ----------------------------------------------------------------------
    def ValidateTestBase(self, obj):
        self.assertEqual(obj[0].a, ["one", "two"])
        self.assertEqual(obj[1].a, ["three"])

    # ----------------------------------------------------------------------
    def ValidateTestDerived(self, obj):
        self.assertEqual(obj.b, False)
        self.assertEqual(obj.d, -100.1)
        self.assertEqual(obj.ref, -200.2)
        self.assertEqual(obj.ref2, 100.1)
        self.assertEqual(obj.ref3, [-10, -20])
        self.assertEqual(obj.ref4, [10, 20])
