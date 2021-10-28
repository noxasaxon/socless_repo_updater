from .conftest import get_file_from_mock_repo
from socless_repo_updater.constants import REQUIREMENTS_FULL_PATH
from socless_repo_updater.file_types.requirements_txt import (
    update_socless_python_in_requirements_txt,
)


def load_mock_requirements_txt() -> str:
    requirements_txt = get_file_from_mock_repo(REQUIREMENTS_FULL_PATH)
    return requirements_txt


def test_requirements_txt():
    new_version = "9.9.9"
    modified_requirements_txt = update_socless_python_in_requirements_txt(
        load_mock_requirements_txt(), new_version
    )
    assert (
        "git+https://github.com/twilio-labs/socless_python.git@9.9.9#egg=socless"
        in modified_requirements_txt
    )
