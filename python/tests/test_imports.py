def test_public_exports_are_importable():
    import confidentai
    from confidentai import (
        ConfidentAI,
        ConfidentApiError,
        Organization,
        Project,
    )

    assert confidentai.__version__
    assert ConfidentAI is not None
    assert issubclass(ConfidentApiError, Exception)
    assert Organization is not None
    assert Project is not None


def test_api_primitives_exported():
    from confidentai import (
        Api,
        ApiResponse,
        ConfidentApiError,
        Endpoints,
        HttpMethods,
    )

    assert Api is not None
    assert ApiResponse is not None
    assert issubclass(ConfidentApiError, Exception)
    assert Endpoints is not None
    assert HttpMethods is not None
