# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from typing import IO, NamedTuple, Sequence

# TODO: replace with current year dynamically (if license added?)
DEFAULT_LICENSE = b'"""(C) Corporate 2023 AG."""'


def has_coding(line: bytes) -> bool:
    if not line.strip():
        return False
    return line.lstrip()[:1] == b"#" and (
        b"unicode" in line
        or b"encoding" in line
        or b"coding:" in line
        or b"coding=" in line
    )


class ExpectedContents(NamedTuple):
    shebang: bytes
    rest: bytes
    # True: has exactly the license header expected
    # False: missing license header entirely
    # None: has a license header, but it does not match
    license_status: bool | None
    ending: bytes

    @property
    def has_any_license(self) -> bool:
        return self.license_status is not False

    def is_expected_license(self, remove: bool) -> bool:
        expected_license_status = not remove
        return self.license_status is expected_license_status


def _get_expected_contents(
    first_line: bytes,
    second_line: bytes,
    rest: bytes,
    expected_license: bytes,
) -> ExpectedContents:
    # TODO: add docstring match
    ending = b"\r\n" if first_line.endswith(b"\r\n") else b"\n"

    if first_line.startswith(b"#!"):
        shebang = first_line
        potential_coding = second_line
    else:
        shebang = b""
        potential_coding = first_line
        rest = second_line + rest

    if potential_coding.rstrip(b"\r\n") == expected_license:
        license_status: bool | None = True
    elif has_coding(potential_coding):
        license_status = None
    else:
        license_status = False
        rest = potential_coding + rest

    return ExpectedContents(
        shebang=shebang,
        rest=rest,
        license_status=license_status,
        ending=ending,
    )


def fix_license_header(
    f: IO[bytes],
    remove: bool = False,
    expected_license: bytes = DEFAULT_LICENSE,
) -> int:
    expected = _get_expected_contents(
        f.readline(),
        f.readline(),
        f.read(),
        expected_license,
    )

    # Special cases for empty files
    if not expected.rest.strip():
        # If a file only has a shebang or a coding pragma, remove it
        if expected.has_any_license or expected.shebang:
            f.seek(0)
            f.truncate()
            f.write(b"")
            return 1
        else:
            return 0

    if expected.is_expected_license(remove):
        return 0

    # Otherwise, write out the new file
    f.seek(0)
    f.truncate()
    f.write(expected.shebang)
    if not remove:
        f.write(expected_license + expected.ending)
    f.write(expected.rest)

    return 1


def _normalize_license(license: str) -> bytes:
    return license.encode().rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        "Fixes the license header of python files",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to fix")
    parser.add_argument(
        "--license",
        default=DEFAULT_LICENSE,
        type=_normalize_license,
        help=(f"The license header to use.  " f"Default: {DEFAULT_LICENSE.decode()}"),
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the license header",
    )
    args = parser.parse_args(argv)

    return_value = 0

    if args.remove:
        message = "Removed the license header from {filename}"
    else:
        message = "Added `{license}` to {filename}"

    for filename in args.filenames:
        with open(filename, "r+b") as f:
            file_return_value = fix_license_header(
                f,
                remove=args.remove,
                expected_license=args.license,
            )
            return_value |= file_return_value
            if file_return_value:
                print(
                    message.format(license=args.license.decode(), filename=filename),
                )

    return return_value


if __name__ == "__main__":
    raise SystemExit(main())
