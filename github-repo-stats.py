#!/usr/bin/env python3

import argparse
import json
import requests
import time
import os
import sys
import yaml
from pathlib import Path

bad_responses = {
  '[]',
  '{}'
}

error_message = {
    'message': 'Not Found',
    'documentation_url': 'https://docs.github.com/rest/metrics/statistics#get-all-contributor-commit-activity'
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def request_headers(token):
    return {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }


def get_api_token(api_token, api_token_env_var='GITHUB_API_TOKEN'):
    if api_token:
        token = api_token
    elif api_token_env_var in os.environ:
        token = os.environ[api_token_env_var]
    else:
        print(f'Must pass token from --token option or {api_token_env_var} environment variable. Exiting.')
        sys.exit(1)

    return token


def command_parser():
    parser = argparse.ArgumentParser(description='Process github contributor stats',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(title='commands', dest='command',
                                       help='Download Github repo data')

    fetch_parser = subparsers.add_parser(name='fetch-repo-list', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    fetch_parser.add_argument('owner', metavar='OWNER', type=str,
                              help='Name of user or organization')
    fetch_parser.add_argument('-t', '--token', metavar='TOKEN', type=str, required=False,
                              help='Sets API token, otherwise read from GITHUB_API_TOKEN environment variable')
    fetch_parser.add_argument('-o', '--outfile', metavar='OUTPUT', type=str, required=False,
                                 help='Output file')

    download_parser = subparsers.add_parser(name='download', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    download_parser.add_argument('input_file', metavar='INPUT_FILE', type=str,
                        help='File containing repos under a user or organization')
    download_parser.add_argument('-d', '--directory', metavar='DEST', type=str, default=os.getcwd(), required=False,
                        help='Destination directory for dumping repo data files')
    download_parser.add_argument('-t', '--token', metavar='TOKEN', type=str, required=False,
                        help='Sets API token, otherwise read from GITHUB_API_TOKEN environment variable')
    download_parser.add_argument('-w', '--wait', metavar='WAIT', type=float, default=3, required=False,
                                 help='Duration between API call retries')

    generate_parser = subparsers.add_parser(name='generate', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    generate_parser.add_argument('input_file', metavar='INPUT_FILE', type=str,
                        help='File containing repos under a user or organization')
    generate_parser.add_argument('-d', '--directory', metavar='DEST', type=str, default=os.getcwd(), required=False,
                        help='Source directory for reading repo data files')
    generate_parser.add_argument('-o', '--outfile', metavar='OUTPUT', type=str, required=False,
                                 help='Output file')
    generate_parser.add_argument('-s', '--sort-by', metavar='SORTTBY', type=str, required=False,
                                 choices=['commits', 'added', 'deleted', 'repos'], default='commits',
                                 help='Select field to sort results by')
    generate_parser.add_argument('-r', '--reverse', action='store_false')

    return parser

def fetch_repo_list(args):
    owner = args.owner
    token = get_api_token(args.token)
    outfile = args.outfile

    page_number = 1
    repos = set()

    url = f'https://api.github.com/orgs/{owner}/repos'
    while True:
        params= {
            'per_page': 100,
            'sort': 'full_name',
            'page': page_number
        }
        req = requests.get(url, headers=request_headers(token), params=params)
        if req.text not in bad_responses:
            page_number += 1
            for repo in [_ for _ in req.json()]:
                repos.add(repo['name'])
            print('.', end='', flush=True)
        else:
            break

    output = yaml.safe_dump({owner: sorted(repos)})

    if outfile:
        with open(outfile, 'w') as f:
            f.write(output)
    else:
        print(output)


def download(args):
    input_file = args.input_file
    directory = args.directory
    wait = args.wait

    token = get_api_token(args.token)

    with open(input_file, 'r') as infile:
        config = yaml.safe_load(infile)

    for owner, repos in config.items():
        for repo in repos:
            print(f'Getting info on {owner}/{repo} ..', end='')

            url = f'https://api.github.com/repos/{owner}/{repo}/stats/contributors'

            while True:
                req = requests.get(url, headers=request_headers(token))
                if req.text not in bad_responses:
                    print('.. done')
                    break
                else:
                    print('.', end='', flush=True)
                    time.sleep(wait)

            dest_dir = Path(directory) / owner
            dest_dir.mkdir(exist_ok=True)
            with open(dest_dir / f'{repo}.json', 'w') as outfile:
                outfile.write(req.text)


def generate(args):
    input_file = args.input_file
    directory = args.directory
    outfile = args.outfile
    field = args.sort_by
    reverse = args.reverse

    with open(input_file, 'r') as infile:
        config = yaml.safe_load(infile)

    repo_stats = {}

    for owner, repos in config.items():
        for repo in repos:
            infile = Path(directory) / owner / f'{repo}.json'
     
            if not infile.exists() or not infile.is_file():
                eprint(f'Warning: File \'{infile}\' is does not exist')
                continue

            with open(infile, 'r') as infile:
                dat = json.loads(infile.read())

            if dat == error_message:
                eprint(f'Warning: File \'{infile}\' is invalid')
                continue

            #res = [_ for _ in dat]
            for author in [_ for _ in dat]:
                name = author['author']['login']
                commits = author['total']
                added = 0
                deleted = 0
                for week in author['weeks']:
                    added += week['a']
                    deleted += week['d']

                if name in repo_stats:
                    repo_stats[name]['commits'] += commits
                    repo_stats[name]['added'] += added
                    repo_stats[name]['deleted'] += deleted
                    repo_stats[name]['repos'] += 1
                else:
                    repo_stats[name] = {
                        'commits': commits,
                        'added': added,
                        'deleted': deleted,
                        'repos': 1
                    }
    
    output = ''
    output += 'Contributor,Commits,Added,Deleted,Repos\n'
    for entry in sorted(repo_stats.items(), key=lambda item: item[1][field], reverse=reverse):
        author, stats = entry
        output += f"{author},{stats['commits']},{stats['added']},{stats['deleted']},{stats['repos']}\n"

    if outfile:
        with open(outfile, 'w') as f:
            f.write(output)
    else:
        print(output)


subcommands = {
    'fetch-repo-list': fetch_repo_list,
    'download': download,
    'generate': generate
}


def main():
    parser = command_parser()
    args = parser.parse_args()

    if args.command in subcommands:
        subcommands[args.command](args)
    else:
        parser.print_help()

 
if __name__ == '__main__':
    main()
