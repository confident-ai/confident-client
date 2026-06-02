"""Fixtures for the live integration suite.

Unlike the unit tests (which mock ``Api._http_request``), these talk to the
real Confident AI API. Everything here is skipped unless
``CONFIDENT_ORG_API_KEY`` is set, so the suite is a no-op in environments
without credentials (e.g. fork PRs).
"""

import os

import pytest


@pytest.fixture(scope="session")
def live_client():
    api_key = os.getenv("CONFIDENT_ORG_API_KEY")
    if not api_key:
        pytest.skip(
            "CONFIDENT_ORG_API_KEY not set; skipping live integration tests"
        )

    from confidentai import ConfidentAI

    return ConfidentAI()
