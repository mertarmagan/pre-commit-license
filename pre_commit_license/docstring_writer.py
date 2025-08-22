import ast
from _ast import Module
from datetime import datetime

from pre_commit_license.constants import DEFAULT_LICENSE


class LicenseHeader:
    def __init__(
        self,
        copyright_text: str = DEFAULT_LICENSE,
        company: str = "",
        year: int | None = None,
    ) -> None:
        self.copyright_text = copyright_text
        self.company = company
        self.year = year
        self.current_year = datetime.now().year

    def value(self):
        value = self.copyright_text

        if self.year:
            value = value + f" {self.year}"
        else:
            value = value + f" {self.current_year}"

        if self.company:
            value = value + f" {self.company}"

        return value + "."


class DocstringWriter(ast.NodeTransformer):
    def visit_Module(self, node: Module):
        self.license_header_added = False

        license_header = LicenseHeader(
            copyright_text=DEFAULT_LICENSE,
            company="MARS AG",
            year=None,
        )
        license_header_value = license_header.value()
        self.license_header_value = license_header_value

        docstring = ast.get_docstring(node)

        if docstring:
            if license_header_value not in docstring:
                content = f"{docstring}\n\n{license_header_value}\n"
                node.body[0] = ast.Expr(value=ast.Str(content))
                self.license_header_added = True
        else:
            content = license_header_value
            node.body.insert(0, ast.Expr(value=ast.Str(content)))
            self.license_header_added = True

        return node


# TODO: write a function for checking if license exists in docstring correctly
