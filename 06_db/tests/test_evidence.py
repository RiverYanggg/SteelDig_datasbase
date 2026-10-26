from steeldig_api.evidence import table_html


def test_table_values_and_safe_spans_are_preserved():
    assert table_html('<table><tr><td colspan="2">685(±1.5) &amp; 832.5</td></tr></table>') == '<table><tr><td colspan="2">685(±1.5) &amp; 832.5</td></tr></table>'


def test_source_html_cannot_inject_active_content():
    output = table_html('<table onclick="alert(1)"><tr><td style="color:red" rowspan="999">685<img src=x onerror=alert(1)><script>alert(2)</script></td></tr></table>')
    assert output == '<table><tr><td>685alert(2)</td></tr></table>'
    assert table_html("plain text < 685") == ""
