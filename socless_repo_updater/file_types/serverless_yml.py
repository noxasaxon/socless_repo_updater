from io import StringIO
from typing import Union
import ruamel.yaml
from socless_repo_updater.utils import dict_merge


# setup yaml parser
yaml = ruamel.yaml.YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = False
yaml.preserve_quotes = True


def update_serverless_yml_content(
    raw_file: Union[bytes, str], update_data: dict, add_keys=False
) -> str:
    serverless_yaml_as_dict = yaml.load(raw_file)
    modified_serverless_yml_dict = dict_merge(
        serverless_yaml_as_dict, update_data, add_keys
    )
    new_serverless_yaml = object_to_yaml_str(modified_serverless_yml_dict)
    return new_serverless_yaml


def yaml_files_are_equal(first, second) -> bool:
    return yaml.load(first) == yaml.load(second)


def object_to_yaml_str(obj, options=None):
    if options is None:
        options = {}
    string_stream = StringIO()
    yaml.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    return output_str
