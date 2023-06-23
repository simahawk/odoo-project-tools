# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import configparser

import click

from .utils.os_exec import run


def parse_bumpversion_cfg(ini_content):
    config = configparser.ConfigParser()
    # header gets stripped when you get new content via --dry-run --list
    header = "[bumpversion]"
    if header not in ini_content:
        ini_content = header + "\n" + ini_content
    config.read_string(ini_content)
    return config


def parse_new_version(cfg_content):
    cfg = parse_bumpversion_cfg(cfg_content)
    return cfg.get("bumpversion", "new_version")


def make_bumpversion_cmd(rel_type, new_version=None, dry_run=False):
    cmd = ["bumpversion"]
    if new_version:
        cmd.append(f"--new-version {new_version}")
    if dry_run:
        cmd.append("--dry-run --list")
    cmd.append(rel_type)
    return " ".join(cmd)


def make_towncrier_cmd(version):
    return "towncrier build --yes --version={}".format(version)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--type",
    "rel_type",
    type=click.Choice(['major', 'minor', 'patch'], case_sensitive=False),
)
@click.option("--new-version", "new_version")
@click.option("--dry-run", "dry_run", is_flag=True)
@click.option("--commit/--no-commit", default=False)
def bump(rel_type, new_version=None, dry_run=False, commit=False):
    cmd = make_bumpversion_cmd(rel_type, new_version=new_version, dry_run=dry_run)
    click.echo(f"Running: {cmd}")
    res = run(cmd)
    if dry_run:
        new_version = parse_new_version(res)
        click.echo(f"New version: {new_version}")


if __name__ == '__main__':
    cli()
