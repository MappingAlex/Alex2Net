#!/usr/bin/env python3

import argparse
import json

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main(works, cites, per_year_of_citation, color_per_cite, path):
    works = {w['id']: {
        'id': w['id'],
        'publication_year': w['publication_year']
    } for w in works}

    cites = {c['id']: {
        'id': c['id'],
        'publication_year': c['publication_year'],
        'referenced_works': [r for r in c['referenced_works'] if r in works]
    } for c in cites}

    d = dict()
    for c in cites.values():
        i = c['id']
        for r in c['referenced_works']:
            if per_year_of_citation:
                y = c['publication_year']
            else:
                y = works[r]['publication_year']
            if y not in d:
                d[y] = dict()
            if i not in d[y]:
                d[y][i] = 0
            d[y][i] += 1
    d = pd.DataFrame(d)
    d = pd.melt(d, ignore_index=False).reset_index()
    d.columns = ['Paper', 'Year', 'n']
    d['Year'] = d['Year'].astype(str)
    if color_per_cite:
        sns.set_context(rc={'patch.linewidth': 0.0})
        f = sns.histplot(
            d, x='Year', weights='n',
            hue='Paper', multiple='stack'
        )
        plt.legend([], [], frameon=False)
    else:
        d = d[['Year', 'n']].groupby('Year').sum()
        f = sns.histplot(d, x='Year', weights='n')
    plt.xticks(rotation=90)
    plt.tight_layout()
    f.get_figure().savefig(path)


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
    type=argparse.FileType('wb'),
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
    '-c', '--color-per-cite',
    action='store_true', default=False,
    help=(
        'Plot each work that cites the studied works with a different color'
    )
)
args = parser.parse_args()
works = [json.loads(j) for j in args.works.read().splitlines()]
cites = [json.loads(j) for j in args.cites.read().splitlines()]
main(works, cites, args.per_year_of_citation, args.color_per_cite, args.output)
