#!/usr/bin/env python3

import argparse
import json
import sys

import networkx


def clean_gml(x):
    if isinstance(x, dict):
        x = {k: clean_gml(v) for k, v in x.items()}
        x = {k: v for k, v in x.items() if v is not None}
        x = {k: v for k, v in x.items() if k != 'abstract_inverted_index'}
        if len(x) > 0:
            return x
        else:
            return None
    elif isinstance(x, list):
        x = [clean_gml(v) for v in x]
        x = [v for v in x if v is not None]
        if len(x) > 0:
            return x
        else:
            return None
    else:
        return x


def clean_graphml(x, first_level=True):
    if isinstance(x, dict) and first_level:
        x = {k: clean_graphml(v, first_level=False) for k, v in x.items()}
        x = {k: v for k, v in x.items() if v is not None}
        return x
    elif isinstance(x, dict) and not first_level:
        return None
    elif isinstance(x, list):
        return None
    else:
        return x


def main(works, graph_format, path):
    g = networkx.DiGraph()

    for w in works:
        if graph_format == 'gml':
            w = clean_gml(w)
        elif graph_format == 'graphml':
            w = clean_graphml(w)
        g.add_node(w['id'], **w)

    for w in works:
        for r in w['referenced_works']:
            if r not in g:
                continue
            if 'publication_date' in w:
                g.add_edge(w['id'], r, date=w['publication_date'])
            else:
                g.add_edge(w['id'], r)

    if graph_format == 'gml':
        networkx.write_gml(g, path)
    elif graph_format == 'graphml':
        networkx.write_graphml(g, path)


parser = argparse.ArgumentParser()
parser.add_argument(
    'works',
    type=argparse.FileType(), nargs='?', default=sys.stdin,
    help='JSONL file of OpenAlex works (default: standard input)'
)
parser.add_argument(
    'output',
    type=argparse.FileType('wb'),
    help='file to output the graph'
)
parser.add_argument(
    '-f', '--format',
    choices=['gml', 'graphml'], default='gml',
    help=(
        'graph format to output. '
        'GML format can store more metadata (default: gml)'
    )
)

args = parser.parse_args()
works = [json.loads(j) for j in args.works.read().splitlines()]
main(works, args.format, args.output)
