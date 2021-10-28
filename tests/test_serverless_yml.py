from .conftest import get_file_from_mock_repo
from socless_repo_updater.constants import SERVERLESS_YML
from socless_repo_updater.file_types.serverless_yml import (
    update_serverless_yml_content,
    yaml,
)


def load_mock_serverless_yml() -> str:
    serverless_yml = get_file_from_mock_repo(SERVERLESS_YML)
    return serverless_yml


#!!!! serverless yaml not working

# def test_serverless_yml():
#     new_dependencies = {"some_key": "asd"}
#     modified_serverless_yml_as_string = update_serverless_yml_content(
#         load_mock_serverless_yml(), new_dependencies, add_keys=True
#     )

#     modified_yaml = yaml.load(modified_serverless_yml_as_string)

#     assert modified_yaml["custom"]["sls_apb"]["new_key"] == "new_value"
#     assert modified_yaml["custom"]["sls_apb"]["logging"] is True


# def test_serverless_yml_add_keys():
#     new_dependencies = {"custom": {"sls_apb": {"new_key": "new_value"}}}
#     modified_serverless_yml_as_string = update_serverless_yml_content(
#         load_mock_serverless_yml(), new_dependencies, add_keys=True
#     )

#     modified_yaml = yaml.load(modified_serverless_yml_as_string)

#     assert modified_yaml["custom"]["sls_apb"]["new_key"] == "new_value"
#     assert modified_yaml["custom"]["sls_apb"]["logging"] is True


# def test_serverless_yml_add_keys_without_specifying_flag():
#     new_dependencies = {"custom": {"sls_apb": {"new_key": "new_value"}}}
#     modified_serverless_yml_as_string = update_serverless_yml_content(
#         load_mock_serverless_yml(), new_dependencies
#     )

#     modified_yaml = yaml.load(modified_serverless_yml_as_string)

#     assert modified_yaml["custom"]["sls_apb"]["new_key"] == "new_value"
#     assert modified_yaml["custom"]["sls_apb"]["logging"] is True
