# ==============================================
# HTTP CLIENT - urllib wrapper
# ==============================================
# Replaces 'requests' library to avoid recursion issues on Render
# ==============================================

import urllib.request
import urllib.error
import urllib.parse
import json

# Default User-Agent to avoid Cloudflare blocks
DEFAULT_USER_AGENT = 'Adzsend/1.0'


class HTTPResponse:
    """Simple response object mimicking requests.Response"""
    def __init__(self, status_code, content, headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300

    def json(self):
        return json.loads(self.content.decode('utf-8'))

    @property
    def text(self):
        return self.content.decode('utf-8')


class TimeoutError(Exception):
    """Raised when a request times out"""
    pass


def get(url, headers=None, timeout=10):
    """Make a GET request using urllib"""
    try:
        request_headers = headers.copy() if headers else {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = DEFAULT_USER_AGENT
        req = urllib.request.Request(url, headers=request_headers, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return HTTPResponse(
                status_code=response.status,
                content=response.read(),
                headers=dict(response.headers)
            )
    except urllib.error.HTTPError as e:
        return HTTPResponse(
            status_code=e.code,
            content=e.read(),
            headers=dict(e.headers) if e.headers else {}
        )
    except urllib.error.URLError as e:
        if 'timed out' in str(e.reason).lower():
            raise TimeoutError(str(e.reason))
        raise


def post(url, data=None, json_data=None, headers=None, timeout=10):
    """Make a POST request using urllib"""
    try:
        request_headers = headers.copy() if headers else {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = DEFAULT_USER_AGENT

        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            request_headers['Content-Type'] = 'application/json'
        elif data is not None:
            body = urllib.parse.urlencode(data).encode('utf-8')
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = None

        req = urllib.request.Request(url, data=body, headers=request_headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return HTTPResponse(
                status_code=response.status,
                content=response.read(),
                headers=dict(response.headers)
            )
    except urllib.error.HTTPError as e:
        return HTTPResponse(
            status_code=e.code,
            content=e.read(),
            headers=dict(e.headers) if e.headers else {}
        )
    except urllib.error.URLError as e:
        if 'timed out' in str(e.reason).lower():
            raise TimeoutError(str(e.reason))
        raise
