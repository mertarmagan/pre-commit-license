# -*- coding: utf-8 -*-
import ast
import io

import pytest

from pre_commit_license.__main__ import _normalize_license, main
from pre_commit_license.docstring_writer import DocstringWriter, LicenseHeader


def test_find_docstring():
    root = ast.parse(
        '''def foo():
            """the foo function
            
            Does nothing.
            """
            pass'''
    )

    doc = ast.get_docstring(root)

    for node in ast.walk(root):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Str)
            ):
                print(
                    node.end_lineno, node.body[0].value.end_lineno, node.body[0].value.s
                )


def test_find_oneline_docstring(tmp_path):
    path = tmp_path / "foo.py"
    print(path)
    with open(path, "wb") as file:
        file.write(
            b"#!/usr/bin/env python\n"
            b"# -*- coding: utf-8 -*-\n\n"
            b'"""(C) Copyright 2023"""\n'
            b"x = 1\n"
        )

    with open(path, "rb") as file:
        content = file.read()

    root = ast.parse(content)
    doc = ast.get_docstring(root)

    print(doc)


def test_find_multiline_docstring(tmp_path):
    path = tmp_path / "foo.py"
    print(path)
    with open(path, "wb") as file:
        file.write(
            b"#!/usr/bin/env python\n"
            b"# -*- coding: utf-8 -*-\n\n"
            b'"""This module contains nothing.\n'
            b"\n"
            b"(C) Copyright 2023.\n"
            b'"""\n'
            b"x = 1\n"
        )

    with open(path, "rb") as file:
        content = file.read()

    root = ast.parse(content)
    doc = ast.get_docstring(root)

    print(doc)


def test_append_license_to_docstring(tmp_path):
    license = "(C) Copyright 2023.\n"
    path = tmp_path / "foo.py"
    print(path)
    with open(path, "wb") as file:
        file.write(
            b"#!/usr/bin/env python\n"
            b"# -*- coding: utf-8 -*-\n\n"
            b'"""This module contains nothing."""\n'
            b"\n"
            b"x = 1\n"
        )

    with open(path, "rb") as file:
        content = file.read()

    root = ast.parse(content)
    docstring = ast.get_docstring(root)
    print(docstring)

    docstring_with_license = docstring + "\n" + license

    root.body.insert(0, ast.Expr(value=ast.Str(docstring_with_license)))

    new_docstring = ast.get_docstring(root)
    print(new_docstring)


@pytest.fixture
def file_path(tmp_path):
    return tmp_path / "module.py"


@pytest.fixture
def file_empty(file_path):
    with open(file_path, "w") as file:
        file.write("")
    return file


@pytest.fixture
def file_shebang(file_path):
    with open(file_path, "wb") as file:
        file.write(b"#!/usr/bin/env python\n")


@pytest.fixture
def file_shebang_pragma(file_path):
    with open(file_path, "wb") as file:
        file.write(b"#!/usr/bin/env python\n" b"# -*- coding: utf-8 -*-\n\n")


@pytest.fixture
def file_shebang_pragma_docstring(file_path):
    with open(file_path, "wb") as file:
        file.write(
            b"#!/usr/bin/env python\n"
            b"# -*- coding: utf-8 -*-\n\n"
            b'"""This module contains nothing."""'
        )


@pytest.fixture
def file_shebang_pragma_multiline_docstring(file_path):
    with open(file_path, "wb") as file:
        file.write(
            b"#!/usr/bin/env python\n"
            b"# -*- coding: utf-8 -*-\n\n"
            b'"""This module contains nothing.\n\n'
            b"Extra explanation for a module.\n"
            b'"""\n'
        )


@pytest.mark.parametrize(
    "file_input",
    [
        "file_empty",
        "file_shebang",
        "file_shebang_pragma",
        "file_shebang_pragma_docstring",
        "file_shebang_pragma_multiline_docstring",
    ],
)
def test_docstring_write(file_path, file_input, request):
    file_input = request.getfixturevalue(file_input)
    with open(file_path, "rb") as file:
        root_tree = ast.parse(file.read())
    writer = DocstringWriter()
    writer.visit(root_tree)
    ast.fix_missing_locations(root_tree)

    new_docstring = ast.get_docstring(root_tree)

    with open(file_path, "w") as file:
        file.write(ast.unparse(root_tree))

    assert True


def test_main_success(file_path, file_empty):
    assert main(
        file_path.absolute(),
    )

    with open(file_path, "rb") as file:
        content = file.read()

    root_tree = ast.parse(content)
    docstring = ast.get_docstring(root_tree)

    license_header_value = LicenseHeader().value

    assert license_header_value in docstring


@pytest.mark.parametrize(
    "input_line, expected",
    [
        (b"#!/usr/bin/env python\n", False),
        (b"import httplib\n", False),
        (b'"""Test module with oneline docstring"""\n', False),
        (b'"""Test module with oneline docstring"""', False),
        (b'"""Test module with multiline docstring\n', True),
        (b'"""Test module with multiline docstring', True),
        (b'"""', True),
    ],
)
def test_has_multiline_docstring(input_line, expected):
    assert has_multiline_docstring(input_line) == expected


def test_integration_inserting_license(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b"import httplib\n")

    assert main((str(path),)) == 1

    with open(path, "rb") as file:
        assert file.read() == (
            b'"""(C) Copyright Corporate 2023 AG."""\n' b"import httplib\n"
        )


def test_integration_ok(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b'"""(C) Copyright Corporate 2023 AG."""\nx = 1\n')

    assert main((str(path),)) == 0


def test_integration_remove(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b'"""(C) Copyright Corporate 2023 AG."""\nx = 1\n')

    assert main((str(path), "--remove")) == 1

    with open(path, "rb") as file:
        assert file.read() == b"x = 1\n"


def test_integration_remove_ok(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b"x = 1\n")

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


def test_integration_alternate_license(tmp_path, capsys):
    path = tmp_path / "foo.py"

    with open(path, "wb") as file:
        file.write(b"x = 1\n")

    license = '"""(C) Copyright"""'
    assert main((str(path), "--license", license)) == 1

    with open(path, "rb") as file:
        assert file.read() == b'"""(C) Copyright"""\nx = 1\n'

    out, _ = capsys.readouterr()
    assert out == f'Added `"""(C) Copyright"""` to {str(path)}\n'


def test_crlf_ok(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b'"""(C) Copyright Corporate 2023 AG."""\r\nx = 1\r\n')

    assert main((str(path),)) == 0


def test_crfl_adds(tmp_path):
    path = tmp_path / "foo.py"
    with open(path, "wb") as file:
        file.write(b"x = 1\r\n")

    assert main((str(path),)) == 1

    with open(path, "rb") as file:
        assert file.read() == b'"""(C) Copyright Corporate 2023 AG."""\r\nx = 1\r\n'
