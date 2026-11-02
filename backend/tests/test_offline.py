"""Application tests must fail before any unexpected external connection."""

import socket

import pytest


def test_external_connections_fail_fast():
    with pytest.raises(AssertionError, match="External network access is forbidden"):
        socket.create_connection(("api.anthropic.com", 443))
