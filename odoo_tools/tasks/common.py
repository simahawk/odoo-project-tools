# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import errno
import os
import shutil
import tempfile
from contextlib import contextmanager
from functools import lru_cache
from subprocess import Popen

import yaml
from invoke import exceptions

try:
    from ruamel.yaml import YAML
except ImportError:
    print("Missing ruamel.yaml from requirements")
    print("Please run `pip install -r tasks/requirements.txt`")


def exit_msg(message):
    print(message)
    raise exceptions.Exit(1)


def root_path():
    current_dir = (
        os.getcwd()
    )  # directory from where search for .cookiecutter.context.yml starts
    max_depth = 5
    while max_depth > 0:
        file_list = os.listdir(current_dir)
        parent_dir = os.path.dirname(current_dir)
        if ".cookiecutter.context.yml" in file_list:
            return current_dir
        else:
            if current_dir == parent_dir:
                break
            else:
                current_dir = parent_dir
        max_depth -= 1
    exit_msg("Missing cookiecutter.context.yml. It's not a project directory. Exiting")


def build_path(path, from_root=True, from_file=None):
    if not from_file and from_root:
        base_path = root_path()
    else:
        if from_file is None:
            from_file = __file__
        base_path = os.path.dirname(os.path.realpath(from_file))

    return os.path.join(base_path, path)


# TODO: change depending on new structure
# use root_path to get root project directory
VERSION_FILE = build_path("odoo/VERSION")
HISTORY_FILE = build_path("HISTORY.rst")
PENDING_MERGES_DIR = build_path("pending-merges.d")
MIGRATION_FILE = build_path("odoo/migration.yml")
GITIGNORE_FILE = build_path(".gitignore")
COOKIECUTTER_CONTEXT = build_path(".cookiecutter.context.yml")
GIT_C2C_REMOTE_NAME = "camptocamp"
TEMPLATE_GIT_REPO_URL = "git@github.com:{}.git"
TEMPLATE_GIT = TEMPLATE_GIT_REPO_URL.format("camptocamp/odoo-template")


def gpg_decrypt_to_file(ctx, file_name, password=False):
    """Get a value from lastpass.
    :param file_name: File .gpg to decrypt
    :param password: password to decript gpg file
    """
    passphrase = ""
    if password:
        passphrase = "--pinentry-mode loopback --batch --passphrase '{}' --no-tty --quiet".format(
            password
        )
    ctx.run("gpg --yes {} '{}'".format(passphrase, file_name))


def yaml_load(stream, Loader=None):
    return yaml.load(stream, Loader=Loader or yaml.FullLoader)


@lru_cache(maxsize=None)
def cookiecutter_context():
    with open(COOKIECUTTER_CONTEXT) as f:
        return yaml_load(f.read())


@contextmanager
def cd(path):
    prev = os.getcwd()
    os.chdir(os.path.expanduser(path))
    try:
        yield
    finally:
        os.chdir(prev)


def current_version():
    with open(VERSION_FILE) as fd:
        version = fd.read().strip()
    return version


def ask_confirmation(message):
    """Gently ask user's opinion."""
    r = input(message + " (y/N) ")
    return r in ("y", "Y", "yes")


def ask_or_abort(message):
    """Fail (abort) immediately if user disagrees."""
    if not ask_confirmation(message):
        exit_msg("Aborted")


def check_git_diff(ctx, direct_abort=False):
    try:
        ctx.run("git diff --quiet --exit-code")
        ctx.run("git diff --cached --quiet --exit-code")
    except exceptions.Failure:
        if direct_abort:
            exit_msg("Your repository has local changes. Abort.")
        ask_or_abort(
            "Your repository has local changes, are you sure you want to continue?"
        )


@contextmanager
def tempdir():
    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            # already deleted
            if e.errno != errno.ENOENT:
                raise


def search_replace(file_path, old, new):
    """Replace a text in a file on each lines"""
    shutil.move(file_path, file_path + ".bak")
    with open(file_path + ".bak") as f_r:
        with open(file_path, "w") as f_w:
            for line in f_r:
                f_w.write(line.replace(old, new))


def update_yml_file(path, new_data, main_key=None):
    yaml = YAML()
    # preservation of indentation
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path) as f:
        data = yaml_load(f.read())
        if main_key:
            data[main_key].update(new_data)
        else:
            data.update(new_data)

    with open(path, "w") as f:
        yaml.dump(data, f)


def git_ignores(file):
    ignored = []
    with open(file) as f:
        for line in f.read().splitlines():
            if line.strip() and not line.startswith("#"):
                ignored.append(line)
    return ignored


def git_ignores_global(ctx):
    return git_ignores(
        ctx.run("git config --global core.excludesfile", hide=True).stdout.strip()
    )


GIT_IGNORES = git_ignores(GITIGNORE_FILE)


def get_from_lastpass(ctx, note_id, get_field):
    """Get a value from lastpass.

    :param note_id: lastpass id of the note to show
    :param get_field: Lastpass field to get (as specified on lpass --help
                      for show command)
    :return: Value of the field for this note
    """
    password = False
    try:
        password = ctx.run(
            "lpass show {} {}".format(get_field, note_id), hide=True
        ).stdout.strip()
    except Exception as expt:
        print("Error in get_from_lastpass : {}".format(expt))
    return password


def make_dir(path_dir):
    try:
        os.makedirs(path_dir)
    except OSError:
        if not os.path.isdir(path_dir):
            msg = ("Directory does not exist and could not be created: {}").format(
                path_dir
            )
            exit_msg(msg)
        else:
            pass  # directory already exists, nothing to do in this case


def get_migration_file_modules(migration_file):
    """Read the migration.yml and get module list."""
    with open(migration_file) as stream:
        content = yaml_load(stream)
    modules = set()
    for version in range(len(content["migration"]["versions"])):
        try:
            migration_version = content["migration"]["versions"][version]
            modules.update(migration_version["addons"]["upgrade"])
        except KeyError:
            pass
    return modules


def has_exec(name):
    try:
        devnull = open(os.devnull, "w")
        Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as err:
        if err.errno == os.errno.ENOENT:
            return False
    return True
