import re
from typing import Union
from socless_repo_updater.constants import SOCLESS_PYTHON_PIP_PATTERN


def build_replacement_pip_string(socless_python_release_tag: str) -> str:
    return f"git+https://github.com/twilio-labs/socless_python.git@{socless_python_release_tag}#egg=socless"


def update_socless_python_in_requirements_txt(
    requirements_txt: Union[str, bytes], release: str
) -> str:
    if isinstance(requirements_txt, bytes):
        requirements_txt = requirements_txt.decode("UTF-8")

    file_with_new_release = re.sub(
        SOCLESS_PYTHON_PIP_PATTERN,
        build_replacement_pip_string(release),
        requirements_txt,
    )
    return file_with_new_release


def requirements_txt_are_equal(first: Union[str, bytes], second: Union[str, bytes]):
    if isinstance(first, bytes):
        first = first.decode("UTF-8")
    if isinstance(second, bytes):
        second = second.decode("UTF-8")
    return first == second
