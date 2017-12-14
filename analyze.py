#!/usr/bin/python3

import datetime
import re
import sys
import argparse
import logging


log = logging.getLogger('analyzer')

def parse_arguments():
    parser = argparse.ArgumentParser(description='travis log analyzer')
    parser.add_argument('--top', help='show top 10 tasks',
                        action='store_true', default=False)
    parser.add_argument('--summarize', help='summarize by machine type',
                        action='store_true', default=False)
    parser.add_argument('-d', '--debug', help='debugging',
                        action='store_true', default=False)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    return parser.parse_args()

class TravisInfo:
    id = ""
    info = ""
    duration = datetime.timedelta(0)
    machine = "unknown"
    action = ''
    error = ''

    def __str__(self):
        return '{}: {} {} "{}" took: {} {}'.format(self.id, self.action,
                                                   self.test if self.test else self.project,
                                                   self.info, self.duration, self.machine)

def extract_spread_info(line):

    match = re.search(r'(?P<error>Error )?(?P<action>[pP]reparing|[Ee]xecuting|[Rr]estoring)(?P<project> project)?.*linode:(?P<system>[a-z0-9.-]+)?(?P<test>:tests/[-a-z/0-9]+)?', line)
    if match:
        matches = match.groupdict()
        log.debug('matches: %s', matches)
        # fedora-26-64...
        if matches['system'] and matches['system'].endswith('...'):
            matches['system'] = matches['system'][0:-3]
        # :tests/main/...
        if matches['test']:
            matches['test'] = matches['test'][1:]
        return matches

    return None

def scan(infile):
    info_map = {}
    id = ""

    for line in infile:
        line = line.strip().replace("\x1b[0K","")
        if line.startswith("travis_time:start:"):
            id = line.split(":")[2]
            if not id in info_map:
                log.debug('-- new travis info id %s', id)
                ti = TravisInfo()
                ti.id = id
                info_map[id] = ti

        elif id and line.startswith("travis_time:end:"):
            id = line.split(":")[2]
            if id not in info_map:
                log.debug('-- unknown id %s', id)
                continue

            duration = int(line.split("duration=")[1])/1000.0

            ti = info_map[id]
            # print(info_map[id])
            ti.duration = datetime.timedelta(microseconds=duration)
            log.info(ti)
            log.debug('-- duration %s', ti.duration)
            log.debug('--     line "%s"', line)
        elif id:
            if id not in info_map:
                log.debug('-- unknown id %s', id)
                continue
            # print(id)
            # print(line)
            ti = info_map[id]

            if not ti.info:
                info = extract_spread_info(line)
                if not info:
                    log.debug('discard non spread line "%s"', line)
                    # not coming from spread, get rid of it
                    del info_map[id]
                    id = ""
                    continue
                else:
                    # otherwise keep the first line of a fold only
                    ti.info = line
                    ti.machine = info['system']
                    ti.action = info['action'].lower()
                    ti.error = info['error']
                    ti.project = info['project']
                    ti.test = info['test']
                    log.debug('-- fill starting travis info %s', ti)

    return info_map


def output_sorted_by_duration(info_map, n=sys.maxsize):
    sorted_by_duration = sorted(info_map, key=lambda k: info_map[k].duration, reverse=True)
    i = 0
    for k in sorted_by_duration:
        ti = info_map[k]
        print(ti.machine, ti.duration, ti.info[:120]+"...\n\n")
        if i > n:
            break
        i += 1


def summarize_by_machine(info_map):
    sorted_by_machine = sorted(info_map, key=lambda k: info_map[k].machine)
    info_map_for_machine = {}
    current = {}
    machine = "unknown"
    for k in sorted_by_machine:
        ti = info_map[k]
        if machine != ti.machine:
            if len(current) > 0:
                info_map_for_machine[machine] = current
            machine = ti.machine
            current = {}
        current[k] = ti
    return info_map_for_machine


def output_total_time(descr, info_map):
    total = datetime.timedelta(0)
    for id, ti in info_map.items():
        total += ti.duration
    print("total time for {}: {}".format(descr, total))


if __name__ == "__main__":

    opts = parse_arguments()

    logging.basicConfig(level=logging.DEBUG if opts.debug else logging.INFO)
    info_map = scan(opts.infile)
    # for k, v in info_map.items():
    #     print(v)

    output_total_time("total", info_map)
    #output_sorted_by_duration(info_map)

    if opts.summarize or opts.top:
        info_map_for_machine = summarize_by_machine(info_map)

    if opts.summarize:
        for k, machine_info_map in info_map_for_machine.items():
            output_total_time(k, machine_info_map)

    if opts.top:
        print("\n\ntop-10 for each machine:\n")
        for k, machine_info_map in info_map_for_machine.items():
            output_sorted_by_duration(machine_info_map, 10)
            print("------------------------------------------------------\n\n")
