# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 10:06:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-22.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------

# Parsing is split into the following steps:

#   1) Populate
#      Converts ANTLR tokens into a hierarchy of Items. Errors generated are limited to those that can
#      be calculated given a single statement.
#
#   2) Resolve
#      Resolves references to ensure a consistent processing experience.
#
#   3) Validate
#      Validates that the Items in the Item hierarchy conform to logical rules.
#
#   4) Transform
#      Converts the Items in the Item hierarchy into Elements.
