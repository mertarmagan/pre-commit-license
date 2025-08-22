#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module contains main logic.

Three possibilities for license in docstrings;
1- no docstring + no license header -> add a docstring with license header
2- oneline docstring + no license header -> append license header and convert to multiline docstring
3- multiline docstring + no license header -> append license header
4- docstring + license header -> do nothing

* shebang, encoding pragma must stay if exist in all cases
* leave blank if module is empty (i.e __init__.py files)
* 
"""

import argparse
import ast
from typing import Sequence

from pre_commit_license.constants import DEFAULT_LICENSE
from pre_commit_license.docstring_writer import DocstringWriter


def _normalize_license(license: str) -> bytes:
    return license.encode().rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    # TODO: implement remove license?
    parser = argparse.ArgumentParser(
        "Fixes the license header of Python files",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames to fix license header",
    )
    parser.add_argument(
        "--license",
        default=DEFAULT_LICENSE,
        type=_normalize_license,
        help=(f"The license header to use. " f"Default: {DEFAULT_LICENSE}"),
    )
    args = parser.parse_args(argv)

    license_header_added = False

    message = "Added `{license}` to {filename}"

    for filename in args.filenames:
        with open(filename, "r+b") as file:
            root_tree = ast.parse(file.read())

        writer = DocstringWriter()
        writer.visit(root_tree)
        ast.fix_missing_locations(root_tree)

        with open(filename, "w+b") as file:
            file.write(ast.unparse(root_tree).encode())

        license_header_added |= writer.license_header_added

        if writer.license_header_added:
            print(
                message.format(license=writer.license_header_value, filename=filename)
            )

    return license_header_added


if __name__ == "__main__":
    raise SystemExit(main())
