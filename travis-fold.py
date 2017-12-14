#!/usr/bin/python3

import datetime
import fileinput
import re
import sys


class TravisInfo:
    id = ""
    info = ""
    duration = datetime.timedelta(0)
    machine = "unknown"

    
def scan(fname):
    info_map = {}
    with fileinput.input() as fp:
        id = ""
        for line in fp:
            line = line.strip().replace("\x1b[0K","")
            if line.startswith("travis_time:start:"):
                ti = TravisInfo()
                id = ti.id = line.split(":")[2]
                info_map[ti.id] = ti
            elif line.startswith("travis_time:end:"):
                id = line.split(":")[2]
                info_map[id].duration = datetime.timedelta(microseconds=int(line.split("duration=")[1])/1000.0)
            elif id:
                ti = info_map[id]
                match = re.search(r"linode:([a-z0-9.-]+)...", line)
                if match and ti.machine == "unknown":
                    ti.machine = match.group(1)
                ti.info += line + "\n"
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
    info_map = scan(sys.argv[1])
    output_total_time("total", info_map)
    #output_sorted_by_duration(info_map)
    info_map_for_machine = summarize_by_machine(info_map)
    for k, machine_info_map in info_map_for_machine.items():
        output_total_time(k, machine_info_map)

    print("\n\ntop-10 for each machine:\n")
    for k, machine_info_map in info_map_for_machine.items():
        output_sorted_by_duration(machine_info_map, 10)
        print("------------------------------------------------------\n\n")

