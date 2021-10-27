import json
from typing import List, Optional, Union
from github import GithubException
from github.ContentFile import ContentFile
from github.Repository import Repository
from socless_repo_parser import SoclessGithubWrapper
from socless_repo_parser.helpers import parse_repo_names, get_github_domain
from file_types.requirements_txt import validate_socless_python_release
from socless_repo_updater.constants import PACKAGE_JSON
from socless_repo_updater.exceptions import UpdaterError, VersionUpdateException
from socless_repo_updater.file_types.package_json import update_package_json_contents
from socless_repo_updater.utils import check_github_file_exists, make_branch_name


class RepoUpdater:
    def get_github_file(
        self, gh_repo: Repository, file_path, branch_name
    ) -> ContentFile:
        file_contents = gh_repo.get_contents(path=file_path, ref=branch_name)
        if isinstance(file_contents, list):
            raise UpdaterError(
                f"File path {file_path} branch: {branch_name} points to a directory"
            )
        return file_contents

    def update_in_github(
        self,
        gh_repo: Repository,
        pj_deps: dict = None,
        pj_replace_only: bool = True,
        sls_yml_changes: dict = None,
        socless_python_version: str = "",
        head_branch="",
    ):
        head_branch = head_branch or make_branch_name()
        default_branch = gh_repo.default_branch

        # check head_branch exists. if not, create new branch from default branch
        try:
            branch_query = gh_repo.get_branch(head_branch)
        except GithubException as e:
            print(e)
            print(f"Branch {head_branch} does not exist on {gh_repo.name}. Creating..")
            gh_source = gh_repo.get_branch(default_branch)
            gh_repo.create_git_ref(
                ref="refs/heads/" + head_branch, sha=gh_source.commit.sha
            )

        prs = []
        if pj_deps:
            ## update package.json

            # file_check = check_github_file_exists(
            #     gh_repo, file_path=PACKAGE_JSON, branch_name=head_branch
            # )

            # ????? TODO
            file_contents = self.get_github_file(gh_repo, PACKAGE_JSON, head_branch)
            as_json = json.loads(file_contents.decoded_content)
            new_package_json = update_package_json_contents(
                as_json, pj_deps, pj_replace_only
            )

            # pj_result = update_package_json(
            #     repo=name,
            #     updated_dependencies=pj_deps,
            #     replace_only=pj_replace_only,
            #     org=org,
            #     main_branch=main_branch,
            #     head_branch=branch_name,
            #     ghe=ghe,
            # )
            # if pj_result.pull_request:
            #     prs.append(pj_result.pull_request)
            pass

        if sls_yml_changes:
            ## update serverless.yml

            # sls_result = update_serverless_yml(
            #     repo=name,
            #     update_data={},
            #     replace_only=True,
            #     org=org,
            #     main_branch=main_branch,
            #     head_branch=branch_name,
            #     ghe=ghe,
            # )
            # if sls_result.pull_request:
            #     prs.append(sls_result.pull_request)
            pass

        if socless_python_version:
            ## update socless_python (requirements.txt)

            # try:
            #     socless_python_result = bump_socless_python(
            #         repo=name,
            #         release=socless_python_version,
            #         org=org,
            #         bypass_release_validation=True,
            #         main_branch=main_branch,
            #         head_branch=branch_name,
            #         ghe=ghe,
            #     )
            #     if socless_python_result.pull_request:
            #         prs.append(socless_python_result.pull_request)
            # except FileNotFoundError:
            #     continue
            pass

        ## check if all update commits went to same PR
        # pr_nums = [x.number for x in prs if isinstance(x, PullRequest)]
        # if len(set(pr_nums)) > 1:
        #     print(f"DEBUG | PRs not the same- {name}: {prs}")
        # if len(pr_nums) > 0:
        #     results.append({"repo": name, "updated": True, "pr": prs[0]})
        # else:
        #     results.append({"repo": name, "updated": False, "pr": False})

    # # report metrics
    # skipped = [x for x in results if not x["updated"]]
    # updated = [x for x in results if x["updated"]]
    # print(f"INFO | Number of repos in batch: {len(results)}")
    # print(f"INFO | Number of PRs opened: {len(updated)}")
    # print(f"INFO | Number of repos skipped: {len(skipped)}")
    # for x in updated:
    #     print(x["pr"].url)
    # return {"all_results": results, "skipped": skipped, "updated": updated}

    def _fetch_and_parse_package_json_from_github(self, gh_repo: Repository):
        pass


class SoclessUpdater(SoclessGithubWrapper):
    def update_with_github_enterprise(
        self,
        repo_list: Union[str, List[str]],
        token: str = "",
        domain: str = "",
        pj_deps: dict = None,
        pj_replace_only: bool = True,
        sls_yml_changes: dict = None,
        socless_python_version: str = "",
        head_branch="",
    ):
        self.get_or_init_github_enterprise(token, domain)

        # use private attributes to get the github enterprise domain
        ghe_domain = get_github_domain(self.github_enterprise)  # type: ignore

        # validate args to update TODO
        if socless_python_version:
            socless_python_version = validate_socless_python_release(
                socless_python_version
            )

        # update each repo
        for repo_meta in parse_repo_names(cli_repo_input=repo_list):
            # select correct github instance
            if ghe_domain in repo_meta.url:
                gh = self.get_or_init_github_enterprise()
            else:
                gh = self.get_or_init_github(required=True)

            gh_repo = gh.get_repo(repo_meta.get_full_name())

            RepoUpdater().update_in_github(
                gh_repo,
                pj_deps,
                pj_replace_only,
                sls_yml_changes,
                socless_python_version,
                head_branch,
            )

        #     integration_family = IntegrationFamilyBuilder().build_from_github(gh_repo)

        #     all_integrations.integrations.append(integration_family)

        # return all_integrations

    def validate_socless_python_release(self, release_tag_or_latest: str) -> str:
        if release_tag_or_latest == "latest":
            open_source_github = self.get_or_init_github()
            socless_python_repo = open_source_github.get_repo(
                "twilio-labs/socless_python"
            )
            release = socless_python_repo.get_latest_release().tag_name
            return release
        elif not release_tag_or_latest:
            raise VersionUpdateException("No version specified for socless_python")
        # elif not check_release_exists(
        #     repo="socless_python",
        #     org="twilio-labs",
        #     release=release_tag_or_latest,
        #     ghe=False,
        # ):
        #     raise VersionUpdateException(
        #         f"Release {release_tag_or_latest} not found for twilio-labs/socless_python"
        #     )

        return release_tag_or_latest
