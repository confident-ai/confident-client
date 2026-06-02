from confidentai.types import ApiResponse, ConfidentApiError


def test_confident_api_error_preserves_link():
    err = ConfidentApiError("boom", "https://confident-ai.com/docs")
    assert str(err) == "boom"
    assert err.link == "https://confident-ai.com/docs"


def test_confident_api_error_link_optional():
    err = ConfidentApiError("boom")
    assert err.link is None
    assert isinstance(err, Exception)


def test_api_response_parses_envelope():
    response = ApiResponse(
        success=True, data={"value": 42}, link="https://x", deprecated=True
    )
    assert response.success is True
    assert response.data == {"value": 42}
    assert response.link == "https://x"
    assert response.deprecated is True


def test_api_response_defaults():
    response = ApiResponse(success=False, error="nope")
    assert response.error == "nope"
    assert response.data is None
    assert response.link is None
    assert response.deprecated is None
