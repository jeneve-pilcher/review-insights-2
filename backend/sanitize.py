"""One place that cleans what people type or send.

What it does to every text field of a request body that uses SafeModel:
  - Unicode is normalised (NFC) and invisible/control characters are removed: NUL and other control codes,
    zero-width characters, and the "bidirectional override" characters used to disguise text.
  - Single-line fields: tabs and line breaks become spaces, runs of spaces collapse, and the ends are trimmed.
  - Multi-line fields (MULTILINE_FIELDS: message, csv_text, text, note, notes) keep their line breaks.
  - A field with no length limit of its own is capped at DEFAULT_MAX characters, so nothing is unbounded.

What it does NOT do: it does not HTML-escape. Text is stored as typed and escaped where it is shown (Vue escapes
everything it prints; the page never uses v-html), and the database is only ever called with parameters. Escaping
on the way in would double-escape on the way out.
"""
import re
import unicodedata
from typing import Any

from typing import Annotated

from pydantic import BaseModel, ConfigDict, field_validator

DEFAULT_MAX = 2000
MULTILINE_FIELDS = {"message", "csv_text", "text", "note", "notes"}

# C0/C1 control codes, zero-width characters, bidirectional overrides/isolates, the byte-order mark.
_INVISIBLE = "​-‏‪-‮⁠-⁤⁦-⁩﻿"
_BAD_SINGLE = re.compile(f"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f-\\x9f{_INVISIBLE}]")
_BAD_MULTI = _BAD_SINGLE
_WS = re.compile(r"\s+")

# Ids that arrive in a URL path or query string: letters, digits, dash, underscore.
ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"

try:
    from fastapi import Path
    SafeId = Annotated[str, Path(pattern=ID_PATTERN)]    # a route's {id} in the address: anything else is refused (422)
except ImportError:                                      # only when tested without FastAPI installed
    SafeId = str


def clean_text(value: Any, multiline: bool = False) -> Any:
    """Cleans one string (anything else is returned unchanged)."""
    if not isinstance(value, str):
        return value
    text = unicodedata.normalize("NFC", value)
    if multiline:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return _BAD_MULTI.sub("", text).strip()      # the pattern leaves tab (\x09) and newline (\x0a) alone
    text = _BAD_SINGLE.sub("", text.replace("\t", " ").replace("\r", " ").replace("\n", " "))
    return _WS.sub(" ", text).strip()


def _walk(value: Any, multiline: bool) -> Any:
    if isinstance(value, str):
        return clean_text(value, multiline)
    if isinstance(value, (list, tuple)):
        return [_walk(v, multiline) for v in value]
    return value


def csv_safe(cell: Any) -> Any:
    """Stops a spreadsheet from running a cell as a formula (=, +, -, @ at the start) when a CSV is opened."""
    if isinstance(cell, str) and cell[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + cell
    return cell


class SafeModel(BaseModel):
    """A request body whose text fields are cleaned (see the top of this file) before any other check runs."""
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def _clean_fields(cls, value, info):
        multiline = info.field_name in MULTILINE_FIELDS
        value = _walk(value, multiline)
        if not multiline:
            items = value if isinstance(value, list) else [value]
            for v in items:
                if isinstance(v, str) and len(v) > DEFAULT_MAX:
                    raise ValueError(f"That is too long (the limit is {DEFAULT_MAX} characters).")
        return value
