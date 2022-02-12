# ----------------------------------------------------------------------
# |
# |  FileSystemTestUtils.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-11 09:15:04
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains utilities used for FileSystem tests"""

import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class FileSystemUtilsMixin(object):
    # ----------------------------------------------------------------------
    def ValidateRoot(
        self,
        root,
        process_additional_data=False,
    ):
        self.assertEqual(root.name, "one")
        self.assertEqual(root.directories[0].name, "two")
        self.assertEqual(root.directories[0].directories[0].name, "three")
        self.assertEqual(root.directories[0].directories[0].files[0].name, "file1")
        self.assertEqual(root.directories[0].directories[0].files[0].size, 10)
        self.assertEqual(root.directories[0].directories[0].files[1].name, "file2")
        self.assertEqual(root.directories[0].directories[0].files[1].size, 200)
        self.assertEqual(root.files[0].name, "file10")
        self.assertEqual(root.files[0].size, 20)

    # ----------------------------------------------------------------------
    def ValidateRoots(
        self,
        roots,
        process_additional_data=False,
    ):
        self.assertEqual(roots[0].name, "dir1")
        self.assertEqual(roots[1].name, "dir2")

        if process_additional_data:
            self.assertEqual(roots[1].extra[0].two, "2")
            self.assertEqual(roots[1].extra[0].simple_value, "value")
            self.assertEqual(roots[1].extra[1].a, "a")
            self.assertEqual(roots[1].extra[1].b, "b")
            self.assertEqual(roots[1].extra[1].value[0].one, "1")
            self.assertEqual(roots[1].extra[1].value[0].simple_value, "text value")
            self.assertEqual(roots[1].extra[1].value[1].simple_value, "another text value")
