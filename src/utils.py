from typing import List
from github import Repository, GitRelease
from github.WorkflowRun import WorkflowRun
import re


def get_running_workflows(repo: Repository,
                          shas: List[str] = [],
                          workflow_ids: List[int] = [],
                          branches: List[str] = []
                          ) -> List[WorkflowRun]:

    running_workflows = []

    # Filter by status
    running_workflows.extend([x for x in repo.get_workflow_runs() if x.status in ['queued', 'in_progress']])

    # Filter by branches
    if branches:
        running_workflows = [x for x in running_workflows if x.head_branch in branches]

    # Filter by specific workflow ids instead of all
    if workflow_ids:
        running_workflows = [x for x in running_workflows if x.workflow_id in workflow_ids]

    # Filter by specific shas
    if shas:
        running_workflows = [x for x in running_workflows if x.head_sha in shas]

    return running_workflows


def get_previous_version(repo: Repository) -> str | None:
    """Return the most recent version tag found"""
    # Look at releases to find the previous version
    releases = list(repo.get_releases())

    # Sort releases by created date, most recent first
    releases.sort(reverse=True, key=lambda x: x.created_at)

    # Get the latest release
    if releases:
        print(f'Found release {releases[0].tag_name}')
        return releases[0].tag_name

    print('Can\'t find release')


def bump_version(previous_version: str, bump_type: str, build_name: str) -> str:
    default = 'v0.0.1'

    # Return the default if no previous version found
    if not previous_version:
        return default

    # Official semantic version regex from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    reg = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')
    # Strip out the v in the version number and match it to the regex
    match = reg.match(previous_version.replace('v', ''))
    assert match

    if bump_type == 'build':
        build_meta = match['buildmetadata']
        build_count = (build_meta or '.-1').split('.')[1]
        increment_bc = int(build_count) + 1
        current_version = f'{match["major"]}.{match["minor"]}.{match["patch"]}+{build_name}.{increment_bc}'
    elif bump_type == 'patch':
        patch = int(match['patch']) + 1
        current_version = f'{match["major"]}.{match["minor"]}.{patch}'
    elif bump_type == 'minor':
        minor = int(match['minor']) + 1
        current_version = f'{match["major"]}.{minor}.{match["patch"]}'
    elif bump_type == 'major':
        major = int(match['major']) + 1
        current_version = f'{match["major"]}.{major}.{match["patch"]}'

    return f'v{current_version}'


def create_release(repo: Repository, version: str, sha: str, bump_type: str) -> GitRelease:
    # Get changelog
    # TODO
    change_log = ''

    # Create the tag and release
    if bump_type == 'build':
        return repo.create_git_tag_and_release(
            version,
            version,
            version,
            change_log,
            sha,
            'commit',
            prerelease=True,
        )
    else:
        return repo.create_git_tag_and_release(
            version,
            version,
            version,
            change_log,
            sha,
            'commit',
        )
