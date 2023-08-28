# -*- coding: utf-8 -*-
from __future__ import annotations

import io

import pytest

from pre_commit_license.__main__ import _normalize_license, fix_license_header, main


def test_integration_inserting_pragma(tmpdir):
    path = tmpdir.join("foo.py")
    path.write_binary(b"import httplib\n")

    assert main((str(path),)) == 1

    assert path.read_binary() == (
        b'"""(C) Copyright Corporate 2023 AG."""\n' b"import httplib\n"
    )


def test_integration_ok(tmpdir):
    path = tmpdir.join("foo.py")
    path.write_binary(b'"""(C) Copyright Corporate 2023 AG."""\nx = 1\n')
    assert main((str(path),)) == 0


def test_integration_remove(tmpdir):
    path = tmpdir.join("foo.py")
    path.write_binary(b'"""(C) Copyright Corporate 2023 AG."""\nx = 1\n')

    assert main((str(path), "--remove")) == 1

    assert path.read_binary() == b"x = 1\n"


def test_integration_remove_ok(tmpdir):
    path = tmpdir.join("foo.py")
    path.write_binary(b"x = 1\n")
    assert main((str(path), "--remove")) == 0


@pytest.mark.parametrize(
    "input_str",
    (
        b"",
        (b'"""(C) Copyright Corporate 2023 AG."""\n' b"x = 1\n"),
        (
            b"#!/usr/bin/env python\n"
            b'"""(C) Copyright Corporate 2023 AG."""\n'
            b'foo = "bar"\n'
        ),
    ),
)
def test_ok_inputs(input_str):
    bytesio = io.BytesIO(input_str)
    assert fix_license_header(bytesio) == 0
    bytesio.seek(0)
    assert bytesio.read() == input_str


@pytest.mark.parametrize(
    ("input_str", "output"),
    (
        (
            b"import httplib\n",
            b'"""(C) Copyright Corporate 2023 AG."""\n' b"import httplib\n",
        ),
        (
            b"#!/usr/bin/env python\n" b"x = 1\n",
            b"#!/usr/bin/env python\n"
            b'"""(C) Copyright Corporate 2023 AG."""\n'
            b"x = 1\n",
        ),
        (
            b'"""(C)Copyright AG."""\n' b"x = 1\n",
            b'"""(C) Copyright Corporate 2023 AG."""\n' b"x = 1\n",
        ),
        (
            b"#!/usr/bin/env python\n" b'"""(C)Copyright AG."""\n' b"x = 1\n",
            b"#!/usr/bin/env python\n"
            b'"""(C) Copyright Corporate 2023 AG."""\n'
            b"x = 1\n",
        ),
        # These should each get truncated
        (b'"""(C)Copyright AG."""\n', b""),
        (b'"""(C) Copyright Corporate 2023 AG."""\n', b""),
        (b"#!/usr/bin/env python\n", b""),
        (b'#!/usr/bin/env python\n"""(C)Copyright AG."""\n', b""),
        (b'#!/usr/bin/env python\n"""(C) Copyright Corporate 2023 AG."""\n', b""),
    ),
)
def test_not_ok_inputs(input_str, output):
    bytesio = io.BytesIO(input_str)
    assert fix_license_header(bytesio) == 1
    bytesio.seek(0)
    assert bytesio.read() == output


def test_ok_input_alternate_license():
    input_s = b'"""(C) Copyright"""\nx = 1\n'
    bytesio = io.BytesIO(input_s)
    ret = fix_license_header(bytesio, expected_license=b'"""(C) Copyright"""')
    assert ret == 0
    bytesio.seek(0)
    assert bytesio.read() == input_s


def test_not_ok_input_alternate_license():
    bytesio = io.BytesIO(b"x = 1\n")
    ret = fix_license_header(bytesio, expected_license=b'"""(C) Copyright"""')
    assert ret == 1
    bytesio.seek(0)
    assert bytesio.read() == b'"""(C) Copyright"""\nx = 1\n'


@pytest.mark.parametrize(
    ("input_s", "expected"),
    (
        ('"""(C) Copyright"""', b'"""(C) Copyright"""'),
        # trailing whitespace
        ('"""(C) Copyright"""\n', b'"""(C) Copyright"""'),
    ),
)
def test_normalize_license(input_s, expected):
    assert _normalize_license(input_s) == expected


def test_integration_alternate_license(tmpdir, capsys):
    f = tmpdir.join("f.py")
    f.write("x = 1\n")

    license = '"""(C) Copyright"""'
    assert main((str(f), "--license", license)) == 1
    assert f.read() == '"""(C) Copyright"""\nx = 1\n'
    out, _ = capsys.readouterr()
    assert out == f'Added `"""(C) Copyright"""` to {str(f)}\n'


def test_crlf_ok(tmpdir):
    f = tmpdir.join("f.py")
    f.write_binary(b'"""(C) Copyright Corporate 2023 AG."""\r\nx = 1\r\n')
    assert not main((str(f),))


def test_crfl_adds(tmpdir):
    f = tmpdir.join("f.py")
    f.write_binary(b"x = 1\r\n")
    assert main((str(f),))
    assert f.read_binary() == b'"""(C) Copyright Corporate 2023 AG."""\r\nx = 1\r\n'
