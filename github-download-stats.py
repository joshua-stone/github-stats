#!/usr/bin/env python3

import argparse
import requests
import sys
import os


bad_responses = {
  '[]',
  '{}'
}


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
        token = ''
    return token


def main():
    parser = argparse.ArgumentParser(description='Process github contributor stats',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('owner', metavar='OWNER', type=str,
                        help='Name of user or organization')
    parser.add_argument('repo', metavar='REPO', type=str,
                        help='Name of repository')
    parser.add_argument('extensions', metavar='EXTENSIONS', type=str, nargs='+',
                        help='File extension of download artifact, i.e., \'.tar.gz\'')                    
    parser.add_argument('-i', '--include-prereleases', action='store_true',
                        help='Include pre-release downloads')
    parser.add_argument('-t', '--token', metavar='TOKEN', type=str, required=False,
                              help='Sets API token, otherwise read from GITHUB_API_TOKEN environment variable')
    args = parser.parse_args()
    token = get_api_token(args.token)
    url = f'https://api.github.com/repos/{args.owner}/{args.repo}/releases'
    
    extensions = dict.fromkeys([ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions], 0)

    page_number = 1
    while True:
        params= {
            'per_page': 100,
            'page': page_number
        }
        if token:
            req = requests.get(url, headers=request_headers(token), params=params, allow_redirects=True)
        else:
            req = requests.get(url, params=params, allow_redirects=True)

        if req.text in bad_responses:
            break

        for download in req.json():
            if args.include_prereleases or not download['prerelease']:
                for asset in download['assets']:
                    download_url = asset['browser_download_url']
                    for extension in extensions:
                        if download_url.endswith(extension):
                            extensions[extension] += asset['download_count']
                            break
            else:
                continue

        page_number += 1

    offset = max(map(len, extensions))
    for extension, count in sorted(extensions.items(), key=lambda item: item[1], reverse=True):
        print(f'{extension:{offset}} - {count}')


if __name__ == '__main__':
    main()
