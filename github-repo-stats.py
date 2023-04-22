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

def main():
    parser = argparse.ArgumentParser(description='Process github contributor stats')
    parser.add_argument('input_file', metavar='INPUT_FILE', type=str,
                        help='File containing repos under a user or organization')
    parser.add_argument('-d', '--dest', metavar='DEST', type=str, default=os.getcwd(),
                        help='Destination directory to write repo data files')
    parser.add_argument('-t', '--token', metavar='TOKEN', type=str, required=False,
                        help='Sets API token, otherwise read from GITHUB_API_TOKEN environment variable')
    parser.add_argument('-w', '--wait', metavar='WAIT', type=float, default=3, required=False, help='Duration between API call retries')

    args = parser.parse_args()

    if args.token:
        token = args.token
    elif 'GITHUB_API_TOKEN' in os.environ:
        token = os.environ['GITHUB_API_TOKEN']
    else:
        print('Must pass token from --token option or GITHUB_API_TOKEN environment variable. Exiting.')
        sys.exit(1)

    with open(args.input_file, 'r') as infile:
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
                    time.sleep(args.wait)
 
            dest_dir = Path(args.dest) / owner
            dest_dir.mkdir(exist_ok=True)
            with open(dest_dir / f'{repo}.json', 'w') as outfile:
                outfile.write(req.text)

if __name__ == '__main__': main()
