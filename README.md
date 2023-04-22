# github-collaborator-stats

Extract and process stats of github collaborator stats for a given user or organization

## Basic usage

```
$ ./github-repo-stats.py --dest repos repos/flathub-apps.yml
```

## Generating input data

A YAML dict is used to represent one owner to any number of repos:

```
$ mkdir repos
$ echo "flathub:" > repos/flathub.yml
$ flatpak remote-ls --app --system --columns=application flathub | uniq | while read LINE; do echo "- $LINE"; done >> repos/flathub-apps.yml
```

## Setting up a personal access token

A [personal access token](https://github.com/settings/tokens) is required to read Github repo statistics.

Once a token generated, it can be passed as an environment variable:

```
$ export GITHUB_API_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Or as a CLI flag:

```
$ ./github-repo-stats.py repos/flathub-apps.txt --token="ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```
