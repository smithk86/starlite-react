import pytest
from pathlib import Path

from starlite.controller import Controller
from starlite.enums import MediaType
from starlite.exceptions import NotFoundException
from starlite.handlers import get
from starlite.testing import create_test_client


from starlite_react import ReactController


react_build_directory = Path(__file__).parent / "react-build"


react_file_suffixes = {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/vnd.microsoft.icon",
    ".js": "application/javascript",
    ".json": "application/json",
    ".map": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
}


@pytest.fixture(scope="session")
def react_files() -> list[tuple[Path, bytes]]:
    filterd_files = filter(lambda x: x.is_file(), react_build_directory.rglob("**/*"))
    files = [
        (
            x.relative_to(react_build_directory),
            x.read_bytes(),
        )
        for x in filterd_files
    ]
    assert len(files) > 0
    assert len([path for path, content in files if b"{{ROOT_PATH}}" in content]) > 0

    return files


def test_with_additional_routes() -> None:
    class TestReactController(ReactController):
        directory = react_build_directory

    class ApiController(Controller):
        path = "/api"

        @get(media_type=MediaType.TEXT)
        def api_root(self) -> str:
            return "Hello, World!"

        @get(path="/{_:path}")
        def not_found(self) -> None:
            raise NotFoundException()

    with create_test_client(
        route_handlers=[TestReactController, ApiController]
    ) as test_client:
        response = test_client.get(f"/api")
        assert response.status_code == 200, f"payload: {response.text}"
        assert response.text == "Hello, World!"

        response = test_client.get(f"/api/test")
        assert response.status_code == 404, f"payload: {response.text}"

        response = test_client.get("/")
        assert response.status_code == 200, f"payload: {response.text}"
        assert response.headers.get("content-type") == "text/html; charset=utf-8"

        response = test_client.get(f"/some/arbitrary/path")
        assert response.status_code == 200, f"payload: {response.text}"
        assert response.headers.get("content-type") == "text/html; charset=utf-8"


def test_all_react_files(react_files: list[tuple[Path, bytes]]) -> None:
    class TestReactController(ReactController):
        directory = react_build_directory

    with create_test_client(route_handlers=[TestReactController]) as test_client:
        for path, content in react_files:
            expected_content_type = react_file_suffixes[path.suffix]
            response = test_client.get(f"/{path}")
            assert response.status_code == 200, f"payload: {response.text}"

            # confirm the correct content-type is set
            assert (
                response.headers.get("content-type") == expected_content_type
            ), f"file: {path}"

            # confirm ROOT_PATH is being replaced
            if b"{{ROOT_PATH}}" in content:
                assert "{{ROOT_PATH}}" not in response.text


def test_controller_path(react_files: list[tuple[Path, bytes]]) -> None:
    class TestReactController(ReactController):
        path = "/react"
        directory = react_build_directory

    with create_test_client(route_handlers=[TestReactController]) as test_client:
        for path, content in react_files:
            expected_content_type = react_file_suffixes[path.suffix]
            response = test_client.get(f"/react/{path}")
            assert response.status_code == 200, f"payload: {response.text}"

            # confirm the correct content-type is set
            assert (
                response.headers.get("content-type") == expected_content_type
            ), f"file: {path}"

            # confirm ROOT_PATH is being replaced
            if b"{{ROOT_PATH}}" in content:
                assert "{{ROOT_PATH}}" not in response.text


def test_root_path(react_files: list[tuple[Path, bytes]]) -> None:
    class TestReactController(ReactController):
        directory = react_build_directory

    with create_test_client(
        route_handlers=[TestReactController], root_path="/testpath"
    ) as test_client:
        for path, content in react_files:
            expected_content_type = react_file_suffixes[path.suffix]
            response = test_client.get(f"/{path}")
            assert response.status_code == 200, f"payload: {response.text}"

            # confirm the correct content-type is set
            assert (
                response.headers.get("content-type") == expected_content_type
            ), f"file: {path}"

            # confirm ROOT_PATH is being replaced
            if b"{{ROOT_PATH}}" in content:
                assert "/testpath" in response.text


def test_controller_and_root_path(react_files: list[tuple[Path, bytes]]) -> None:
    class TestReactController(ReactController):
        path = "/react"
        directory = react_build_directory

    with create_test_client(
        route_handlers=[TestReactController], root_path="/testpath"
    ) as test_client:
        for path, content in react_files:
            expected_content_type = react_file_suffixes[path.suffix]
            response = test_client.get(f"/react/{path}")
            assert response.status_code == 200, f"payload: {response.text}"

            # confirm the correct content-type is set
            assert (
                response.headers.get("content-type") == expected_content_type
            ), f"file: {path}"

            # confirm ROOT_PATH is being replaced
            if b"{{ROOT_PATH}}" in content:
                assert "/testpath/react" in response.text

    #     for path, content in react_files:
    #         request_path = f"{controller_path}/{path}"
    #         expected_content_type = react_file_suffixes[path.suffix]
    #         response = test_client.get(request_path)
    #         assert response.status_code == 200, f"payload: {response.text}"

    #         # confirm the correct content-type is set
    #         assert (
    #             response.headers.get("content-type") == expected_content_type
    #         ), f"file: {path}"

    #         # confirm ROOT_PATH is being replaced
    #         if b"{{ROOT_PATH}}" in content:
    #             assert "{{ROOT_PATH}}" not in response.text
    #             assert root_path in response.text, f"file: {path}"

    #         response = test_client.get(f"/api")
    #         assert response.status_code == 200, f"payload: {response.text}"
    #         assert response.text == "Hello, World!"

    #     # validate arbirary paths work as well
    #     # this is required for React Router DOM to function
    #     for index_path in [
    #         controller_path,
    #         f"{controller_path}/testpath1",
    #         f"{controller_path}/testpath2",
    #         f"{controller_path}/path1/path2/path3",
    #     ]:
    #         response = test_client.get(index_path)
    #         assert response.status_code == 200, f"payload: {response.text}"
    #         assert response.headers.get("content-type") == "text/html; charset=utf-8"
    #         assert "You need to enable JavaScript to run this app." in response.text
