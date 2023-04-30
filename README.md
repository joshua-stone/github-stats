# github-stats

Download and process stats of github stats for a given user or organization

## Contribution stats

### Basic usage

```
$ ./github-repo-stats.py download repos/flathub-apps.yml --directory repos/
$ ./github-repo-stats.py generate repos/flathub-apps.yml --directory repos/ --outfile results/flathub-apps-stats.csv
```

### Generating input data

A YAML file is used to represent one owner to any number of repos:

```
$ mkdir repos/
$ ./github-repo-stats.py fetch-repo-list flathub --outfile repos/flathub.yml
```

Or for a more specific listing:

```
$ mkdir repos/
$ echo "flathub:" > repos/flathub-apps.yml
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

## Download stats

### Getting download stats by file extension

```
$ ./github-download-stats.py obsidianmd obsidian-releases --include-prereleases AppImage asar.gz deb dmg exe snap tar.gz
```
