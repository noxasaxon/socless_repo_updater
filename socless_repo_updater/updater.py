import json
from typing import List, Tuple, Union
from github import GithubException
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Repository import Repository
from socless_repo_parser import SoclessGithubWrapper
from socless_repo_parser.helpers import parse_repo_names, get_github_domain
from socless_repo_parser.models import RepoMetadata
from socless_repo_updater.constants import (
    PACKAGE_JSON,
    REQUIREMENTS_FULL_PATH,
    SERVERLESS_YML,
)
from socless_repo_updater.exceptions import UpdaterError, VersionUpdateException
from socless_repo_updater.file_types.package_json import update_package_json_contents
from socless_repo_updater.file_types.requirements_txt import (
    requirements_txt_are_equal,
    update_socless_python_in_requirements_txt,
)
from socless_repo_updater.file_types.serverless_yml import (
    update_serverless_yml_content,
    yaml_files_are_equal,
)
from socless_repo_updater.utils import (
    commit_file_with_pr,
    make_branch_name,
)


class GithubUpdater:
    def __init__(self, gh_repo: Repository, head_branch: str = "") -> None:
        self.gh_repo = gh_repo
        self.head_branch = head_branch or make_branch_name()
        self.default_branch = self.gh_repo.default_branch
        self.all_prs: List[PullRequest] = []

    def get_github_file(self, file_path, branch_name) -> ContentFile:
        file_contents = self.gh_repo.get_contents(path=file_path, ref=branch_name)
        if isinstance(file_contents, list):
            raise UpdaterError(
                f"File path {file_path} branch: {branch_name} points to a directory"
            )
        return file_contents

    def _create_head_branch_if_nonexistent(self):
        try:
            _ = self.gh_repo.get_branch(self.head_branch)
        except GithubException as e:
            print(
                f"Branch {self.head_branch} does not exist on {self.gh_repo.name}. Creating.. ({e})"
            )
            gh_source = self.gh_repo.get_branch(self.default_branch)
            self.gh_repo.create_git_ref(
                ref="refs/heads/" + self.head_branch, sha=gh_source.commit.sha
            )

    def update_in_github(
        self,
        pj_deps: dict = None,
        pj_replace_only: bool = True,
        sls_yml_changes: dict = None,
        socless_python_version: str = "",
    ):
        self._create_head_branch_if_nonexistent()

        if pj_deps:
            ## update package.json
            self._update_package_json(pj_deps, pj_replace_only)

        if sls_yml_changes:
            ## update serverless.yml
            self._update_serverless_yml(sls_yml_changes)

        if socless_python_version:
            self._update_socless_python_version(socless_python_version)

    def report_pr_metrics(self):
        ## check if all update commits went to same PR
        pr_nums = [x.number for x in self.all_prs]
        if len(set(pr_nums)) > 1:
            print(
                f"DEBUG | PRs not the same, issue with commit logic- {self.gh_repo.name}: {self.all_prs}"
            )
        if len(pr_nums) > 0:
            return {"repo": self.gh_repo.name, "updated": True, "pr": self.all_prs[0]}
        else:
            return {"repo": self.gh_repo.name, "updated": False, "pr": False}

    def _update_package_json(self, pj_deps, pj_replace_only):
        gh_file_object = self.get_github_file(PACKAGE_JSON, self.head_branch)
        as_json = json.loads(gh_file_object.decoded_content)
        new_package_json = update_package_json_contents(
            as_json, pj_deps, pj_replace_only
        )

        if as_json == new_package_json:
            print("No changes made, package.json dependencies are current.")
        else:
            ## file has changed, commit changes & update PR
            new_content = json.dumps(new_package_json, indent=2)
            pr = self._commit_file_helper(
                gh_file_object,
                new_content,
                commit_message="updating versions for: "
                + " ".join(new_package_json["dependencies"].keys()),
            )
            # save pr for metrics analysis
            self.all_prs.append(pr)

    def _update_serverless_yml(self, sls_yml_changes: dict):
        gh_file_object = self.get_github_file(SERVERLESS_YML, self.head_branch)

        new_content = update_serverless_yml_content(
            gh_file_object.decoded_content, sls_yml_changes
        )

        if yaml_files_are_equal(gh_file_object.decoded_content, new_content):
            print("No changes made, serverless.yml files are the same.")
        else:
            pr = self._commit_file_helper(
                gh_file_object,
                new_content,
                commit_message=f"updating serverless.yml with: {json.dumps(sls_yml_changes)}",
            )
            # save pr for metrics analysis
            self.all_prs.append(pr)

    def _update_socless_python_version(self, socless_python_version: str):
        gh_file_object = self.get_github_file(REQUIREMENTS_FULL_PATH, self.head_branch)

        new_requirements = update_socless_python_in_requirements_txt(
            gh_file_object.decoded_content, socless_python_version
        )

        if requirements_txt_are_equal(gh_file_object.decoded_content, new_requirements):
            print("No changes made, requirements.txt files are the same.")
        else:
            pr = self._commit_file_helper(
                gh_file_object,
                new_requirements,
                commit_message=f"updating requirements.txt to socless_python v{socless_python_version}",
            )
            # save pr for metrics analysis
            self.all_prs.append(pr)

    def _commit_file_helper(
        self, gh_file_object: ContentFile, new_content: str, commit_message: str
    ) -> PullRequest:
        pr = commit_file_with_pr(
            self.gh_repo,
            gh_file_object,
            new_content,
            gh_file_object.path,
            self.head_branch,
            self.default_branch,
            commit_message,
        )
        return pr


class SoclessUpdater(SoclessGithubWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.prs_for_all_repos: List[PullRequest] = []
        self.metrics_for_all_repos: List[dict] = []
        self.errors: List[Tuple[RepoMetadata, Exception]] = []
        self.all_repos: List[RepoMetadata] = []

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
        ghe_domain = get_github_domain(self.github_enterprise)  # type: ignore

        # TODO validate args to update _before_ starting the batch
        # if socless_python_version:
        #     socless_python_version = validate_socless_python_release(
        #         socless_python_version
        #     )

        # update each repo

        repos_metadata = parse_repo_names(cli_repo_input=repo_list)
        repos_metadata.sort(key=lambda x: x.url)
        self.all_repos = repos_metadata

        for repo_meta in repos_metadata:
            # select correct github instance
            if ghe_domain in repo_meta.url:
                gh = self.get_or_init_github_enterprise()
            else:
                gh = self.get_or_init_github(required=True)

            try:
                gh_repo = gh.get_repo(repo_meta.get_full_name())

                repo_updater = GithubUpdater(gh_repo, head_branch)
                repo_updater.update_in_github(
                    pj_deps,
                    pj_replace_only,
                    sls_yml_changes,
                    socless_python_version,
                )

                # ensure that if no branch was provided, we use the newly created branch name
                head_branch = repo_updater.head_branch
                self.metrics_for_all_repos.append(repo_updater.report_pr_metrics())
                self.prs_for_all_repos = self.prs_for_all_repos + repo_updater.all_prs
            except Exception as e:
                print(
                    f"ERROR | skipping repo due to error during update of {repo_meta.name} - {e}."
                )
                self.errors.append((repo_meta, e))

        self.report_all_metrics()

    def update_with_regular_github(
        self,
        repo_list: Union[str, List[str]],
        token: str = "",
        pj_deps: dict = None,
        pj_replace_only: bool = True,
        sls_yml_changes: dict = None,
        socless_python_version: str = "",
        head_branch="",
    ):
        # TODO validate args to update _before_ starting the batch
        # if socless_python_version:
        #     socless_python_version = validate_socless_python_release(
        #         socless_python_version
        #     )

        # update each repo

        repos_metadata = parse_repo_names(cli_repo_input=repo_list)
        repos_metadata.sort(key=lambda x: x.url)
        self.all_repos = repos_metadata

        for repo_meta in repos_metadata:
            gh = self.get_or_init_github(token=token, required=True)

            try:
                gh_repo = gh.get_repo(repo_meta.get_full_name())

                repo_updater = GithubUpdater(gh_repo, head_branch)
                repo_updater.update_in_github(
                    pj_deps,
                    pj_replace_only,
                    sls_yml_changes,
                    socless_python_version,
                )

                # ensure that if no branch was provided, we use the newly created branch name
                head_branch = repo_updater.head_branch
                self.metrics_for_all_repos.append(repo_updater.report_pr_metrics())
                self.prs_for_all_repos = self.prs_for_all_repos + repo_updater.all_prs
            except Exception as e:
                print(
                    f"ERROR | skipping repo due to error during update of {repo_meta.name} - {e}."
                )
                self.errors.append((repo_meta, e))

        self.report_all_metrics()

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

    def report_all_metrics(self):
        # # report metrics
        skipped = []
        updated = []
        for report in self.metrics_for_all_repos:
            if report["updated"]:
                updated.append(report)
            else:
                skipped.append(report)

        print(f"INFO | Number of repos in batch: {len(self.metrics_for_all_repos)}")
        print(f"INFO | Number of PRs opened: {len(updated)}")
        print(f"INFO | Number of repos skipped: {len(skipped)}")

        for report in updated:
            print(report["pr"].url)

        return {
            "all_results": self.metrics_for_all_repos,
            "skipped": skipped,
            "updated": updated,
        }

    def report_all_errors(self, raise_errors=False):
        for repo_meta, err in self.errors:
            print(f"ERROR | {repo_meta.url} - {err}")

        if raise_errors:
            raise UpdaterError(
                f"{len(self.errors)} found during update of {len(self.all_repos)} repos. read logs above ^"
            )
