# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import sys

stdin, stdout = sys.stdin, sys.stdout

# Workaround for when you need to set a pdb in a click command inside pytest session.
# NOTE: this is not needed if you run tests w/ `catch_exceptions=False`.
# eg: runner.invoke(init, catch_exceptions=False)
#
# Since CliRunner overrides sys.{stdin,stdout} and pdb depends on them,
# it's quite expected that this doesn't just work. pytest,
# which also does IO redirection, monkey patches the global pdb.set_trace
# so that it disables IO redirection when called allowing it work even
# if IO redirection is enabled. But I think click generally tries to avoid
# affecting global state...
#
# Credit: https://github.com/pallets/click/issues/843#issuecomment-427684909


def pdb_set_trace():
    import pdb  # noqa

    pdb.Pdb(stdin=stdin, stdout=stdout).set_trace()
