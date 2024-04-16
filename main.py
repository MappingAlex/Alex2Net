#!/usr/bin/env python3

import argparse
import json
import math
import sys

import pyalex


def get_npages(query):
    return math.ceil(query.count()/args.per_page)


def get_result(query, page, npages):
    print(f'- page {page}/{npages}', file=sys.stderr)
    return query.get(page=page, per_page=args.per_page)


def print_results(values, query, start_expr, start_page):
    nvalues_per_expr = 49
    nexprs = math.ceil(len(values)/nvalues_per_expr)
    for i in range(start_expr-1, nexprs):
        print(f'query {i+1}/{nexprs}', file=sys.stderr)
        e = '|'.join(values[i*nvalues_per_expr:(i+1)*nvalues_per_expr])
        npages = get_npages(query(e))
        for p in range(start_page-1, npages):
            start_page = 1
            for r in get_result(query(e), p+1, npages):
                print(json.dumps(r))


def stderr_input(prompt):
    print(prompt, end='', file=sys.stderr)
    return input()


def print_author_ids(display_name, start_page):
    query = pyalex.Authors().search_filter(display_name=display_name)
    npages = get_npages(query)
    for p in range(start_page-1, npages):
        authors = get_result(query, p+1, npages)
        for a in authors:
            n = a['display_name']
            i = a['last_known_institution']['display_name']
            r = stderr_input(f'Do you want to include {n} ({i})? y/n ')
            while r not in ['y', 'n']:
                r = stderr_input('Write "y" or "n". ')
            if r == 'y':
                print(a['id'])


def print_works(author_ids, start_expr, start_page):
    print_results(
        author_ids,
        lambda x: pyalex.Works().filter(author={'id': x}),
        start_expr, start_page
    )


def print_cited_by(works, start_expr, start_page):
    print_results(
        sorted(list({w['id'] for w in works})),
        lambda x: pyalex.Works().filter(cited_by=x),
        start_expr, start_page
    )


def print_cites(works, start_expr, start_page):
    print_results(
        sorted(list({w['id'] for w in works})),
        lambda x: pyalex.Works().filter(cites=x),
        start_expr, start_page
    )


parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument(
    '--email',
    type=str, nargs='?',
    help=(
        'your email. '
        'Useful to get into the polite pool'
        ', that has much faster and more consistent response times'
    )
)
parent_parser.add_argument(
    '--api-key',
    type=str, nargs='?',
    help=(
        'your api key. '
        'Useful to get into the polite pool'
    )
)
parent_parser.add_argument(
    '--per-page',
    type=int, nargs='?', default=50,
    help=(
        'number of results per page. '
        'In principle, it can be up to 200. '
        'But sometimes the server can not return so big results, '
        'so it is recommended to use an smaller value (default: 50)'
    )
)
parent_parser.add_argument(
    '--max-retries',
    type=int, nargs='?', default=0,
    help='maximum number of retries to do if a query fails (default: 0)'
)
parent_parser.add_argument(
    '--retry-backoff-factor',
    type=float, nargs='?', default=0.1,
    help='factor to determine the delay between retries (default: 0.1)'
)
parent_parser.add_argument(
    '--retry-http-codes',
    type=int, nargs='*', default=[429, 500, 503],
    help='HTTP error codes that trigger a retry (default: 429, 500 and 503)'
)
parent_parser.add_argument(
    '-q', '--start-query',
    type=int, nargs='?', default=1,
    help='start at given query. Useful after an interruption (default: 1)'
)
parent_parser.add_argument(
    '-p', '--start-page',
    type=int, nargs='?', default=1,
    help='start first query at given page (default: 1)'
)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='cmd', required=True)
author = subparsers.add_parser(
    'author',
    parents=[parent_parser],
    help='prints the ids of the given author'
)
author.add_argument(
    'name',
    type=str,
    help='name of the author (display_name argument in OpenAlex)'
)
works = subparsers.add_parser(
    'works',
    parents=[parent_parser],
    help='prints the works of the given authors. Can print duplicates'
)
works.add_argument(
    'author_ids',
    type=argparse.FileType(), nargs='?', default=sys.stdin,
    help='file with one OpenAlex author id per line (default: standard input)'
)
cites = subparsers.add_parser(
    'cites',
    parents=[parent_parser],
    help='prints the works that cite the given works. Can print duplicates'
)
cites.add_argument(
    'works',
    type=argparse.FileType(), nargs='?', default=sys.stdin,
    help='JSONL file of OpenAlex works (default: standard input)'
)
cited_by = subparsers.add_parser(
    'cited_by',
    parents=[parent_parser],
    help='prints the works cited by the given works. Can print duplicates'
)
cited_by.add_argument(
    'works',
    type=argparse.FileType(), nargs='?', default=sys.stdin,
    help='JSONL file of OpenAlex works (default: standard input)'
)

args = parser.parse_args()
pyalex.config.email = args.email
pyalex.config.api_key = args.api_key
pyalex.config.max_retries = args.max_retries
pyalex.config.retry_backoff_factor = args.retry_backoff_factor
pyalex.config.retry_http_codes = args.retry_http_codes
if args.cmd == 'author':
    print_author_ids(args.name, args.start_page)
elif args.cmd == 'works':
    author_ids = args.author_ids.read().splitlines()
    print_works(author_ids, args.start_query, args.start_page)
elif args.cmd == 'cited_by':
    works = [json.loads(j) for j in args.works.read().splitlines()]
    print_cited_by(works, args.start_query, args.start_page)
elif args.cmd == 'cites':
    works = [json.loads(j) for j in args.works.read().splitlines()]
    print_cites(works, args.start_query, args.start_page)
