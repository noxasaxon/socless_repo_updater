import json
from .conftest import get_file_from_mock_repo
from socless_repo_updater.constants import PACKAGE_JSON
from socless_repo_updater.file_types.package_json import update_package_json_contents


def load_mock_package_json() -> dict:
    package_json = json.loads(get_file_from_mock_repo(PACKAGE_JSON))
    return package_json


def test_package_json():
    new_dependencies = {"serverless": "9.9.9"}
    modified_package_json = update_package_json_contents(
        load_mock_package_json(), new_dependencies
    )
    assert modified_package_json["dependencies"]["serverless"] == "9.9.9"


def test_package_json_replace_only_true():
    new_dependency_name = "some_new_dep"

    new_dependencies = {"serverless": "9.9.9"}
    new_dependencies[new_dependency_name] = "0.1.0"

    modified_package_json = update_package_json_contents(
        load_mock_package_json(), new_dependencies
    )
    assert modified_package_json["dependencies"]["serverless"] == "9.9.9"
    assert new_dependency_name not in modified_package_json["dependencies"]


def test_package_json_replace_only_false():
    new_dependency_name = "some_new_dep"

    new_dependencies = {"serverless": "9.9.9"}
    new_dependencies[new_dependency_name] = "0.1.0"

    modified_package_json = update_package_json_contents(
        load_mock_package_json(), new_dependencies, False
    )
    assert modified_package_json["dependencies"]["serverless"] == "9.9.9"
    assert modified_package_json["dependencies"][new_dependency_name] == "0.1.0"
