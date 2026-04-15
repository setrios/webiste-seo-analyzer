import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import patch, MagicMock
from worker import analyze_url


def make_mock_response(html: str) -> MagicMock:
    mock = MagicMock()
    mock.text = html
    return mock


class TestAnalyzeUrl:
    def test_returns_title(self):

        html = '<html><head><title>My Page</title></head><body></body></html>'
        with patch('worker.requests.get', return_value=make_mock_response(html)):

            result = analyze_url('https://example.com')

        assert result['title'] == 'My Page'

    def test_returns_description(self):

        html = '<html><head><meta name="description" content="SEO desc"></head><body></body></html>'
        with patch('worker.requests.get', return_value=make_mock_response(html)):
            result = analyze_url('https://example.com')
        assert result['description'] == 'SEO desc'

    def test_missing_title_returns_none(self):

        html = '<html><head></head><body></body></html>'
        with patch('worker.requests.get', return_value=make_mock_response(html)):
            result = analyze_url('https://example.com')
        assert result['title'] is None

    def test_missing_description_returns_none(self):

        html = '<html><head><title>T</title></head><body></body></html>'
        with patch('worker.requests.get', return_value=make_mock_response(html)):
            result = analyze_url('https://example.com')
        assert result['description'] is None

    def test_counts_headings_and_links(self):

        html = '''<html><body>
            <h1>A</h1><h1>B</h1>
            <h2>C</h2>
            <a href="#">link1</a><a href="#">link2</a><a href="#">link3</a>
        </body></html>'''
        with patch('worker.requests.get', return_value=make_mock_response(html)):
            result = analyze_url('https://example.com')
        assert result['h1_count'] == 2
        assert result['h2_count'] == 1
        assert result['link_count'] == 3
