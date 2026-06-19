from scrape_common import html_to_text, to_dollars


def test_html_to_text_paragraphs():
    assert html_to_text("<p>First para.</p><p>Second para.</p>") == "First para.\n\nSecond para."


def test_html_to_text_empty_inputs():
    assert html_to_text(None) == ""
    assert html_to_text("") == ""


def test_html_to_text_unescapes_entities():
    assert html_to_text("<p>Tom&amp;Jerry &gt; cats</p>") == "Tom&Jerry > cats"


def test_to_dollars_minor_units():
    assert to_dollars("395", 2) == 3.95
    assert to_dollars("1000", 2) == 10.0


def test_to_dollars_blank_or_none():
    assert to_dollars("", 2) is None
    assert to_dollars(None, 2) is None
