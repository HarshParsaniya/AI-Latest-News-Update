from app.nodes.fetch import strip_html


def test_strip_html_removes_anchor_markup():
    raw = (
        '<a href="https://example.com/x">Gemini update</a>'
        '&nbsp;&nbsp;<font color="#6f6f6f">TechCrunch</font>'
    )
    assert strip_html(raw) == "Gemini update TechCrunch"
    assert "<a" not in strip_html(raw)
