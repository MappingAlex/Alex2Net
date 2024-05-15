#!/usr/bin/env python3

import argparse
import collections
import json
import pathlib

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main(works, cites, per_year_of_citation, color, ncolors, path):
    works = {w['id']: {
        'id': w['id'],
        'publication_year': w['publication_year']
    } for w in works}

    cites = {c['id']: {
        'id': c['id'],
        'publication_year': c['publication_year'],
        'referenced_works': [r for r in c['referenced_works'] if r in works]
    } for c in cites}

    if color == 'cites':
        top = {c['id']: len(c['referenced_works']) for c in cites.values()}
    else:
        top = sum([c['referenced_works'] for c in cites.values()], [])
        top = collections.Counter(top)
    top = sorted(top.items(), key=lambda x: -x[1])
    top = [t[0] for t in top[:ncolors-1]]

    d = dict()
    for c in cites.values():
        for r in c['referenced_works']:
            if per_year_of_citation:
                y = c['publication_year']
            else:
                y = works[r]['publication_year']

            if y not in d:
                d[y] = {t: 0 for t in top}
                d[y]['Other'] = 0

            if color == 'cites':
                t = c['id']
            else:
                t = r

            if t in d[y]:
                d[y][t] += 1
            else:
                d[y]['Other'] += 1

    d = pd.DataFrame(d)
    d = pd.melt(d, ignore_index=False).reset_index()
    d.columns = ['Paper', 'Year', 'n']
    d['Year'] = d['Year'].astype(str)
    d = d.sort_values(by='Year')
    sns.set_context(rc={'patch.linewidth': 0.0})
    if color:
        sns.histplot(
            d, x='Year', weights='n',
            hue='Paper', multiple='stack'
        )
        plt.legend([], [], frameon=False)
    else:
        d = d[['Year', 'n']].groupby('Year').sum()
        sns.histplot(d, x='Year', weights='n')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(path)


parser = argparse.ArgumentParser()
parser.add_argument(
    'works',
    type=argparse.FileType(),
    help='JSONL file of studied works'
)
parser.add_argument(
    'cites',
    type=argparse.FileType(),
    help='JSONL file of works that cite the studied works'
)
parser.add_argument(
    'output',
    type=pathlib.Path,
    help='file to output the plot'
)
parser.add_argument(
    '-y', '--per-year-of-citation',
    action='store_true', default=False,
    help=(
        'Plot the number of citations by the year of the citation '
        'instead of the year of the work'
    )
)
parser.add_argument(
    '-c', '--color',
    choices=['works', 'cites'], default=None,
    help=(
        'If the value is works, colors the citations by the cited work. '
        'If the value is cites, colors the citations by the work that cites. '
        '(default: no color)'
    )
)
parser.add_argument(
    '-n', '--ncolors',
    type=int, default=10,
    help=(
        'When -c is used, -n is the number of colors to use. '
        'If there are more works to color than colors available, '
        'less cited works or works that cite less '
        'are painted with the same color.'
    )
)

args = parser.parse_args()
works = [json.loads(j) for j in args.works.read().splitlines()]
cites = [json.loads(j) for j in args.cites.read().splitlines()]
main(
    works, cites,
    args.per_year_of_citation, args.color, args.ncolors,
    args.output
)
