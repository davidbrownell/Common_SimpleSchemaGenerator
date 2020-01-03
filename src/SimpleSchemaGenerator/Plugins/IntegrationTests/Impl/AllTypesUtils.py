# ----------------------------------------------------------------------
# |
# |  AllTypesUtils.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-11 17:52:44
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains utilities used for AllTypes tests"""

import datetime
import os
import uuid

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.UriTypeInfo import Uri

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class AllTypesUtilsMixin(object):
    # ----------------------------------------------------------------------
    def ValidateTypes(self, obj):
        self.assertEqual(
            obj.bool_,
            [
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                True,
                True,
                True,
                False,
                False,
                False,
            ],
        )
        self.assertEqual(obj.date_, [datetime.date(2019, 2, 11), datetime.date(2019, 2, 11)])
        self.assertEqual(obj.datetime_, [datetime.datetime(2019, 2, 11, 17, 0, 0), datetime.datetime(2019, 2, 11, 17, 0, 0)])
        self.assertEqual([dir.lower() for dir in obj.directory_], [os.path.join(os.getcwd(), "DirectoryName").lower()])
        self.assertEqual(obj.duration_, [datetime.timedelta(1, 82862), datetime.timedelta(1, 82862, 3), datetime.timedelta(0, 82862)])
        self.assertEqual(obj.enum_, ["three", "two", "one"])
        self.assertEqual([filename.lower() for filename in obj.filename_], [os.path.join(os.getcwd(), "FileName").lower()])
        self.assertEqual(obj.guid_, [uuid.UUID("f638e451-c276-479a-aaa0-c699e35196fb")] * 4)
        self.assertEqual(obj.int_, [10, -10])
        self.assertEqual(
            obj.number_,
            [
                100.1,
                100.0,
                -100.1,
                -100.0,
            ],
        )
        self.assertEqual(obj.string_, ["test"])
        self.assertEqual(obj.time_, [datetime.time(10, 11, 12), datetime.time(10, 11, 12, 131415)])
        self.assertEqual(obj.uri_, [Uri.FromString("https://www.test.com"), Uri.FromString("file:///abc123")])
