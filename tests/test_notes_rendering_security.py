"""Check that note font names remain data in rendered HTML and CSS."""

from html.parser import HTMLParser

import pytest

from pyicloud.services.notes.protobuf import notes_pb2 as pb
from pyicloud.services.notes.rendering.renderer import NoteRenderer, _css_font_stack


class _Elements(HTMLParser):
    """Collect parsed start tags and decoded attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Keep each element and its attributes for inspection."""
        self.elements.append((tag, dict(attrs)))


@pytest.mark.parametrize(
    ("font_name", "expected"),
    [
        ("Reader's Font", '"Reader\'s Font", sans-serif'),
        ('A"B', '"A\\"B", sans-serif'),
        ("A\\B", '"A\\\\B", sans-serif'),
        ("A\nB", '"A\\a B", sans-serif'),
        ("A\rB", '"A\\d B", sans-serif'),
        ("A\fB", '"A\\c B", sans-serif'),
        ("A\tB", '"A\\9 B", sans-serif'),
        ("A\x00B", '"A\ufffdB", sans-serif'),
        ("A\x7fB", '"A\\7f B", sans-serif'),
        ("Code Font", '"Code Font", monospace'),
        ("Georgia Custom", '"Georgia Custom", serif'),
        ("Hand Font", '"Hand Font", cursive'),
        (
            "Comic Sans MS",
            '"Comic Sans MS", "Comic Sans", "Chalkboard SE", "Comic Neue", cursive',
        ),
    ],
)
def test_font_name_is_a_css_string(font_name: str, expected: str) -> None:
    """Quotes, backslashes and controls cannot terminate a CSS string."""
    assert _css_font_stack(font_name) == expected


@pytest.mark.parametrize(
    "font_name",
    [
        "Reader's Font",
        "x' onmouseover='alert(1)",
        "x'><img src=x onerror=alert(1)><span style='",
        "x'>&lt;script&gt;alert(1)&lt;/script&gt;",
        'x"; background-image:url(https://example.invalid/track); /*',
        'x\\"; color:red; /*',
        "x\n\r\t\f\x00\x7f'<>\"&",
        "Comic Sans MS",
    ],
)
def test_font_name_cannot_inject_html(font_name: str) -> None:
    """Inspect actual protobuf rendering through an HTML parser."""
    note = pb.Note(note_text="safe")
    run = note.attribute_run.add(length=4)
    run.font.font_name = font_name
    rendered = NoteRenderer().render(note)
    parser = _Elements()
    parser.feed(rendered)
    assert [tag for tag, _ in parser.elements] == ["p", "span"]
    spans = [attrs for tag, attrs in parser.elements if tag == "span"]
    assert spans == [{"style": f"font-family:{_css_font_stack(font_name)}"}]
