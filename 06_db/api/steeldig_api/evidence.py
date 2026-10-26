"""Display extracted table evidence without trusting source HTML."""
from html import escape
from html.parser import HTMLParser


class _TableHTML(HTMLParser):
    tags = {"table", "caption", "thead", "tbody", "tfoot", "tr", "th", "td", "sup", "sub", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.has_table = False

    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            return
        self.has_table |= tag == "table"
        spans = ""
        if tag in {"th", "td"}:
            for name, value in attrs:
                if name in {"colspan", "rowspan"} and value and value.isascii() and value.isdigit() and len(value) <= 3 and 1 <= int(value) <= 100:
                    spans += f' {name}="{int(value)}"'
        self.parts.append(f"<{tag}{spans}>")

    def handle_endtag(self, tag):
        if tag in self.tags and tag != "br":
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(escape(data))


def table_html(source: str) -> str:
    """Allow only inert table markup, dropping all source links/styles/events."""
    parser = _TableHTML()
    parser.feed(source)
    parser.close()
    return "".join(parser.parts) if parser.has_table else ""
