#!/usr/bin/python3

import datetime
import re
import sys
import argparse
import logging
import csv


log = logging.getLogger('analyzer')


def parse_arguments():
    parser = argparse.ArgumentParser(description='travis log analyzer')
    parser.add_argument('--top', help='show top 10 tasks',
                        action='store_true', default=False)
    parser.add_argument('--summarize', help='summarize by machine type',
                        action='store_true', default=False)
    parser.add_argument('--type', help='task type', dest='typ',
                        choices=('test', 'project', 'any'),
                        default='any')
    parser.add_argument('-d', '--debug', help='debugging',
                        action='store_true', default=False)
    parser.add_argument('--output-csv', help='dump parsed data into csv',
                        action='store_true', default=False)
    parser.add_argument('-q', '--quiet', help='quiet',
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
    error = False
    typ = '<none>'
    test = '<none>'
    line_num = 0
    start = None
    end = None
    travis_job = ''

    def __str__(self):
        return '{}: {} {} {} "{}" took: {} {}'.format(self.id, self.action,
                                                      self.typ, self.test,
                                                      self.info, self.duration, self.machine)

    def from_info(self, info):
        self.machine = info['system']
        self.action = info['action'].lower()

        if info['error']:
            self.error = True

        if info['project']:
            self.typ = 'project'
        if info['test']:
            self.typ = 'test'
            self.test = info['test']

    def set_line_location(self, line_num, text):
        self.line_num = line_num
        self.info = text

    def line(self):
        return "{}:'{}'".format(self.line_num, self.info)


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
    in_env = False
    travis_job = ""

    slog = logging.getLogger('analyzer.scanner')

    for num, line in enumerate(infile):
        line = line.strip().replace("\x1b[0K", "")
        if line.startswith("travis_fold:start:env"):
            in_env = True
            slog.debug('env start, line %d', num)

        elif line.startswith("travis_fold:end:env"):
            in_env = False
            slog.debug('env end, line %d', num)

        elif in_env:
            match = re.match(r'TRAVIS_JOB_NUMBER=(?P<job>[0-9.]+)', line)
            if match:
                travis_job = match['job']
                slog.info("TRAVIS JOB: %s", travis_job)

        elif line.startswith("travis_time:start:"):
            id = line.split(":")[2]
            if id not in info_map:
                slog.debug('-- new travis info id %s', id)
                ti = TravisInfo()
                ti.id = id
                ti.travis_job = travis_job
                info_map[id] = ti

        elif id and line.startswith("travis_time:end:"):
            id, times = line.split(":")[2:4]
            if id not in info_map:
                slog.debug('-- unknown id %s', id)
                continue

            textstart, textend, textduration = times.split(",")
            duration = int(textduration.split("duration=")[1])/1000.0
            start = float(textstart.split('start=')[1])
            end = float(textend.split('finish=')[1])

            ti = info_map[id]
            # print(info_map[id])
            ti.duration = datetime.timedelta(microseconds=duration)
            ti.start = datetime.datetime.fromtimestamp(start/1000000000)
            ti.end = datetime.datetime.fromtimestamp(end/1000000000)

            slog.info(ti)
            slog.debug('-- duration %s', ti.duration)
            slog.debug('--     line "%s"', line)

        elif id:
            if id not in info_map:
                slog.debug('-- unknown id %s', id)
                continue
            # print(id)
            # print(line)
            ti = info_map[id]

            if not ti.info:
                info = extract_spread_info(line)
                if not info:
                    slog.debug('discard non spread line "%s"', line)
                    # not coming from spread, get rid of it
                    del info_map[id]
                    id = ""
                    continue
                else:
                    # otherwise keep the first line of a fold only
                    ti.from_info(info)
                    ti.set_line_location(num, line)
                    slog.debug('-- fill starting travis info %s', ti)

    return info_map


def output_sorted_by_duration(info_map, n=sys.maxsize):
    sorted_by_duration = sorted(info_map, key=lambda k: info_map[k].duration, reverse=True)
    i = 0
    for k in sorted_by_duration:
        ti = info_map[k]
        print(ti.machine, ti.duration, ti.typ, ti.action, ti.line())
        if i > n:
            break
        i += 1


def summarize_by_machine(info_map, typ):
    sorted_by_machine = sorted(info_map, key=lambda k: info_map[k].machine)
    info_map_for_machine = {}
    for k in sorted_by_machine:
        ti = info_map[k]
        log.debug('ti typ: %s line: "%s"', ti.typ, ti.line())
        if typ != 'any' and ti.typ != typ:
            continue

        if ti.machine not in info_map_for_machine:
            info_map_for_machine[ti.machine] = {}

        current = info_map_for_machine[ti.machine]
        current[k] = ti
    return info_map_for_machine


def output_total_time(descr, info_map):
    total = datetime.timedelta(0)
    for id, ti in info_map.items():
        total += ti.duration
    print("total time for {}: {}".format(descr, total))


def dump_csv(info_map):
    fieldnames=['id', 'travis_job',
                'machine',
                'duration', 'start', 'end',
                'type', 'action', 'error', 'test',
                'line', 'text']
    out = csv.DictWriter(sys.stdout, fieldnames)
    out.writeheader()
    for ti in info_map.values():
        out.writerow({
            'id': ti.id,
            'machine': ti.machine,
            'duration': ti.duration.total_seconds(),
            'start': ti.start.timestamp() if ti.start else 0,
            'end': ti.end.timestamp() if ti.end else 0,
            'type': ti.typ,
            'action': ti.action,
            'error': ti.error,
            'test': ti.test,
            'line': ti.line_num,
            'text': ti.info,
            'travis_job': ti.travis_job,
        })


def main(opts):
    info_map = scan(opts.infile)

    if opts.output_csv:
        dump_csv(info_map)
        return

    output_total_time("total", info_map)

    if opts.summarize or opts.top:
        info_map_for_machine = summarize_by_machine(info_map, opts.typ)

    if opts.summarize:
        for k, machine_info_map in info_map_for_machine.items():
            output_total_time(k, machine_info_map)

    if opts.top:
        print("\n\ntop-10 for each machine:\n")
        for k, machine_info_map in info_map_for_machine.items():
            print('{}:\n'.format(k))
            output_sorted_by_duration(machine_info_map, 10)
            print("------------------------------------------------------\n\n")


if __name__ == "__main__":

    opts = parse_arguments()

    lvl = logging.INFO
    if opts.quiet:
        lvl = logging.WARNING
    else:
        lvl = logging.DEBUG if opts.debug else logging.INFO
    logging.basicConfig(level=lvl)

    main(opts)
