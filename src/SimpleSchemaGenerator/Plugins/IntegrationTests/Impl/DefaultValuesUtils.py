# ----------------------------------------------------------------------
# |
# |  DefaultValuesUtils.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-23 21:49:13
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Helpers for DefaultValues tests"""

import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DefaultValuesMixin(object):
    # ----------------------------------------------------------------------
    def ValidateObject1(self, obj):
        self.assertEqual(obj.attribute, "foo")
        self.assertFalse(hasattr(obj, "attribute_no_default"))

        self.assertEqual(obj.value, False)
        self.assertFalse(hasattr(obj, "value_no_default"))

        self.assertFalse(hasattr(obj, "values"))

    # ----------------------------------------------------------------------
    def ValidateObject2(self, obj):
        self.assertEqual(obj.attribute, "bar")
        self.assertFalse(hasattr(obj, "attribute_no_default"))

        self.assertEqual(obj.value, True)
        self.assertFalse(hasattr(obj, "value_no_default"))
