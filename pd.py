#!/usr/bin/env python3

import argparse
import sys

from datetime import timedelta

import pandas as pd

def parse_arguments():
    parser = argparse.ArgumentParser(description='job analyzer')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('--type', help='task type', dest='typ',
                        choices=('test', 'project', 'any'),
                        default='any')
    parser.add_argument('--action', help='action type', dest='action',
                        choices=('preparing', 'executing', 'restoring', 'any'),
                        default='any')
    parser.add_argument('--top', help='show top 10 tasks',
                        action='store_true', default=False)
    parser.add_argument('--machine', help='selected machine', default='')
    parser.add_argument('--sum', help='summary', default=False,
                        action='store_true')
    return parser.parse_args()


def main(opts):

    df = pd.read_csv(opts.infile)

    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 120)

    values = {}
    if opts.machine:
        values['machine'] = [opts.machine]
    if opts.typ != 'any':
        values['type'] = [opts.typ]
    if opts.action != 'any':
        values['action'] = [opts.action]

    if values:
        mask = df[list(values.keys())].isin(values).all(axis=1)
        df = df[mask]

    if opts.top:
        res = df[['machine', 'duration', 'type', 'test', 'text']]. \
              sort_values(by=['duration'], ascending=False). \
                                 head(10)
        res['duration'] = res['duration'].map(lambda v: timedelta(seconds=v))
        print(res)

    if opts.sum:
        res = df[['machine', 'duration']].groupby('machine', as_index=False). \
              sum()
        for v in res.values:
            print('{0:<20s} {1}'.format(v[0], timedelta(seconds=v[1])))


if __name__ == '__main__':
    opts = parse_arguments()
    main(opts)
