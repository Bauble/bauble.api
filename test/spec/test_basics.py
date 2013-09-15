
from test.api import *

def test_parse_accept_header():
    from bauble.server import parse_accept_header

    result = parse_accept_header("application/json;q=0;depth=1")
    assert result == {"application/json": {'q': '0', 'depth': '1'}}

    result = parse_accept_header("application/json;q=0;depth=1, */*")
    assert result == {"application/json": {'q': '0', 'depth': '1'},
                      "*/*": {}}

    result = parse_accept_header("application/json;q=0;depth=1, */*, text/html;depth=2")
    assert result == {"application/json": {'q': '0', 'depth': '1'},
                      "*/*": {},
                      "text/html": {'depth': '2'}}
