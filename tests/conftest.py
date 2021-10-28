import pytest
from dotenv import load_dotenv

MOCK_DIR_PATH = "tests/mock_files/"
PATH_TO_LOCAL_MOCK_REPO = f"{MOCK_DIR_PATH}/mock_socless_repo"


@pytest.fixture(scope="session", autouse=True)
def load_dotenv_if_exists():
    load_dotenv()


def get_mock_file(file_name: str) -> str:
    file_path = f"{MOCK_DIR_PATH}{file_name}"
    with open(file_path) as f:
        python_file_as_string = f.read()
    return python_file_as_string


def get_file_from_mock_repo(file_path: str) -> str:
    file_path = f"{PATH_TO_LOCAL_MOCK_REPO}/{file_path}"
    with open(file_path) as f:
        file_as_string = f.read()
    return file_as_string


def pytest_addoption(parser):
    # `tox -- --github`
    parser.addoption(
        "--github",
        action="store_true",
        default=False,
        help="run slow tests that touch github.com",
    )


def pytest_configure(config):
    # `tox -- --github`
    config.addinivalue_line("markers", "github: marks tests that touch github.com")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--github"):
        # `tox -- --github`
        # --github given in cli: do not skip slow tests
        return
    skip_github = pytest.mark.skip(reason="need --github option to run")
    for item in items:
        if "github" in item.keywords:
            item.add_marker(skip_github)
