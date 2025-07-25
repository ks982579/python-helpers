# Python Helpers

> Sort of personal helpers for myself, but I'd like to use where ever needed.

## Contents

Section to outline what to find and ideas I have.

### Done

- Nothing yet...

### In Progress

- Parse and aggregate time spent on tasks daily.
- YAML config
- Config creater - for starting first time and for updates
- Creating a new day - no other features
- Helper to comment out code in an XML file

### Backlog

- Create new day - remove completed list items.
- Ending day - find the file, add "Bye" and the end time, then run calculation.
- Adding new ticket w/standard tasks AND to brag book
- Completing a work ticket, update brag book - should it be JSON file - KDL?

### Bugs

- Create Config seems to loop again after creating first config?
- Create new day does not copy the previous day.
  - seems to get "Sprints Root" twice

## Idea: How to Use

Hoping to work for Bash and PowerShell.

First, you must clone the repository into a path on your computer.
Then do the `python3.13 -m venv venv` to create a virtual environment.

### PowerShell

Instructions soon...

### Bash

Instructions soon...

## How to Tag for Release

A tag is like a git branch that is frozen;
once created, you cannot change the history of commits.
You can create annotated tags with:

```bash
git tag -a v0.1.0
# Opens commit editor to fill up metadata
# OR
git tag -a v0.1.0 -m "Releasing version v0.1.0"
# OR - for lightweight tags that only store the commit hash
git tag v0.1.0
```

Other useful commands:

```bash
git tag -l 'v0.*' # list with wildcard
git tag -l -n3 # list
git show <tag-id>

# Fix tags
git tag -a -f <tag_identifier> <commit_id>
# if error pushed to server - make sure local is correct
git push origin -f --tags
# delete tag
git tag -d <tag-id>
# remove remove tag
git push origin :v1.0
# publish tags
git push origin v1.0
```
