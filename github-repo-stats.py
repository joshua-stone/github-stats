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


def parse_args():
    parser = argparse.ArgumentParser(description='Process github contributor stats',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(title='commands', dest='command',
                                       help='Download Github repo data')
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

    return parser.parse_args()


def download(args):
    input_file = args.input_file
    directory = args.directory
    wait = args.wait

    if args.token: 
        token = args.token
    elif 'GITHUB_API_TOKEN' in os.environ:
        token = os.environ['GITHUB_API_TOKEN']
    else:
        print('Must pass token from --token option or GITHUB_API_TOKEN environment variable. Exiting.')
        sys.exit(1)

    with open(input_file, 'r') as infile:
        config = yaml.safe_load(infile)

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    for owner, repos in config.items():
        for repo in repos:
            print(f'Getting info on {owner}/{repo} ..', end='')

            url = f'https://api.github.com/repos/{owner}/{repo}/stats/contributors'

            while True:
                req = requests.get(url, headers=headers)
                if req.text not in bad_responses:
                    print('.. done')
                    break
                else:
                    print('.', end='')
                    time.sleep(wait)

            dest_dir = Path(directory) / owner
            dest_dir.mkdir(exist_ok=True)
            with open(dest_dir / f'{repo}.json', 'w') as outfile:
                outfile.write(req.text)


def generate(args):
    input_file = args.input_file
    directory = args.directory
    outfile = args.outfile

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
    for entry in sorted(repo_stats.items(), key=lambda item: item[1]['commits'], reverse=True):
        author, stats = entry
        output += f"{author},{stats['commits']},{stats['added']},{stats['deleted']},{stats['repos']}\n"

    if outfile:
        with open(outfile, 'w') as f:
            f.write(output)
    else:
        print(output)


def main():
    args = parse_args()

    if args.command == 'download':
        download(args)
    elif args.command == 'generate':
        generate(args)
    else:
        print(f'Invalid command \'{args.command}\'. Exiting.')
        sys.exit(1)

 
if __name__ == '__main__':
    main()
