# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import sys
import click
import os
import pkg_resources
from subprocess import Popen, PIPE
from distutils.version import LooseVersion

REPO = 'git@github.com:camptocamp/odoo-project-tools'
# http://stackoverflow.com/a/39843432/647924
LS_REMOTE_CMD = 'git ls-remote --tags %s' % REPO


# TODO: cache it for a while (eg: 10m)
def get_git_versions():
    proc = Popen(LS_REMOTE_CMD, stdout=PIPE, shell=True)
    (out, err) = proc.communicate()
    return [
        x.split('refs/tags/')[-1]
        for x in out.decode('utf-8').splitlines()
        # ignore annotated tags dereferences
        # https://stackoverflow.com/questions/15472107
        if not x.endswith('^{}')
    ]


def get_latest_version():
    versions = get_git_versions()
    latest = '0.0.0'
    for v in versions:
        if LooseVersion(v) > LooseVersion(latest):
            latest = v
    return latest


def get_installed_version():
    # Example of version returned by setuptools_scm when
    # the package is installed from a git revision:
    # '1.0a15.dev19+g6dfcfe1.d20181114'
    # (last tag + 1, dev counter, sha, date)
    return pkg_resources.get_distribution("odoo-tools").version


def check_installed_version():
    if os.getenv("SKIP_VERSION_CHECK"):
        return
    click.echo("Checking version...")
    installed = get_installed_version()
    latest = get_latest_version()
    click.echo(
        "Latest: %s - installed: %s\n" % (latest, installed)
    )
    if not LooseVersion(installed) >= LooseVersion(latest):
        click.echo(
            "New version of `cloud_template` is available. "
            "Please, upgrade before proceeding."
        )
        sys.exit(0)
