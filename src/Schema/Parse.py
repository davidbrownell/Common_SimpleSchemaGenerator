# ----------------------------------------------------------------------
# |  
# |  Parse.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 13:16:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Functionality used when parsing SimpleSchema files"""

import os
import sys

from collections import OrderedDict

import six

from .Impl.Populate import Populate
# BugBug from .Impl.Validate import Validate
# BugBug from .Impl.Transform import Transform

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def ParseFiles( filenames,
                parser,
                filter_unsupported_extensions,
                filter_unsupported_attributes,
              ):
    d = OrderedDict()

    for filename in filenames:
        d[filename] = lambda filename=filename: open(filename).read()

    return ParseEx( d,
                    parser,
                    filter_unsupported_extensions,
                    filter_unsupported_attributes,
                  )

# ----------------------------------------------------------------------
def ParseStrings( named_strings,            # { "<name>" : "<content>", ... }
                  parser,
                  filter_unsupported_extensions,
                  filter_unsupported_attributes,
                ):
    d = OrderedDict()

    for k, v in six.iteritems(named_strings):
        d[k] = lambda v=v: v

    return ParseEx( d,
                    parser,
                    filter_unsupported_extensions,
                    filter_unsupported_attributes,
                  )

# ----------------------------------------------------------------------
def ParseEx( source_name_content_generators,            # { "<name>" : def Func() -> content }
             parser,
             filter_unsupported_extensions,
             filter_unsupported_attributes,
           ):
    parser.VerifyFlags()

    root = Populate(source_name_content_generators, parser)

    root = Validate( root,
                     parser,
                     filter_unsupported_extensions,
                     filter_unsupported_attributes,
                   )

    root = Transform(root, parser)

    # Eliminate the root element as the parent for top-level elements
    for child in root.Children:
        child.Parent = None

    return root.Children
