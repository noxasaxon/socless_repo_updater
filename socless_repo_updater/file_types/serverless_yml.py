import json, base64
from io import StringIO
import ruamel.yaml
from src.constants import SERVERLESS_YML
from src.exceptions import VersionUpdateException
from src.gh_helpers import setup_for_file_update, update_file_and_pr, dict_merge
from src.structs import BumpDependencyResult

# setup yaml parser
yaml = ruamel.yaml.YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = False
yaml.preserve_quotes = True


def object_to_yaml_str(obj, options=None):
    if options is None:
        options = {}
    string_stream = StringIO()
    yaml.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    return output_str


def update_serverless_yml(
    repo: str,
    update_data: dict,
    replace_only: bool = False,
    org="twilio-labs",
    head_branch: str = "",
    main_branch: str = "master",
    ghe: bool = False,
) -> BumpDependencyResult:

    setup_info = setup_for_file_update(
        repo=repo,
        org=org,
        file_path=SERVERLESS_YML,
        head_branch=head_branch,
        main_branch=main_branch,
        ghe=ghe,
    )

    gh_repo = setup_info.gh_repo
    contentfile = setup_info.contentfile
    head_branch = setup_info.branch_name

    if not contentfile.content:  # type: ignore
        raise VersionUpdateException("File content is empty or doesnt exist")

    raw_file = base64.b64decode(contentfile.content)  # type: ignore
    modified_serverless_yml = dict_merge(yaml.load(raw_file), update_data)

    if modified_serverless_yml == yaml.load(raw_file):
        result_msg = "No changes made, dependencies are current."
        result_updated = False
        pull_request = False
    else:
        raw_content = object_to_yaml_str(modified_serverless_yml)

        commit_message = "updating versions for: " + "".join(update_data.keys())

        result = update_file_and_pr(
            file_path=contentfile.path,
            commit_msg=commit_message,
            raw_content=raw_content,
            file_sha=contentfile.sha,
            pr_title="CLI- dependency version bump",
            pr_body=f"updating versions for \n```{json.dumps(update_data)}```",
            head_branch=head_branch,
            main_branch=main_branch,
            gh_repo=gh_repo,
        )
        result_updated = True
        result_msg = result.result_msg
        pull_request = result.pr

    return BumpDependencyResult(
        file_updated=result_updated,
        message=result_msg,
        repo_name=repo,
        pull_request=pull_request,  # type: ignore
        setup_info=setup_info,
    )
