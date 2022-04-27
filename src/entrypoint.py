#!/usr/bin/env python3

from github import Github
import os
import utils
import time

# Get inputs
token = os.getenv('token', None)
repository = os.getenv('repository', None)
build_name = os.getenv('build_name', 'build')
bump_type = os.getenv('type', 'build')
branch_name = os.getenv('branch', 'main')
current_sha = os.getenv('current_sha', None)
previous_sha = os.getenv('previous_sha', None)

# Validate inputs
assert isinstance(token, str)
assert isinstance(repository, str)
assert isinstance(current_sha, str)
assert isinstance(previous_sha, str)

# Get the Repo
G = Github(token)
repo = G.get_repo(repository)

# Check if another workflow is running
workflow_ids = []  # Pass in names and we convert?
workflows = utils.get_running_workflows(repo, [previous_sha], workflow_ids)
watch_dog = 0
while workflows:
    print(f'Waiting on workflows ({watch_dog*30}s):')
    for flow in workflows:
        flow_name = repo.get_workflow(flow.workflow_id).name
        print(f'[{flow.id}] NAME: {flow_name} STATUS: {flow.status} SHA: {flow.head_sha}')
    time.sleep(30)

    # Keep track of how long we are doing this and exit if number reaches too high
    watch_dog = watch_dog + 1
    assert watch_dog < 70

    # Update running workflows
    workflows = utils.get_running_workflows(repo, [previous_sha], workflow_ids)

# Get most recent tag
previous_tag = utils.get_previous_version(repo)
print(f'Previous release: {previous_tag}')

# Increment the tag
current_tag = utils.bump_version(previous_tag, bump_type, build_name)
print(f'New release: {current_tag}')

# Push tag and create github release
release = utils.create_release(repo, current_tag, current_sha, bump_type)

# Output formatting function
print('::set-output name=current_tag::{}'.format(current_tag))
print('::set-output name=previous_tag::{}'.format(previous_tag))
print('::set-output name=release_id::{}'.format(release.id))
