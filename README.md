# Tools

## Spread jobs on Travis

### `analyze.py` 

The script will parse the log and maybe produce a CSV

```
analyze.py --output-csv -q ../travis-log-timeout.txt > out.csv
```

See `--help` for options.

### `pd.py`

The script uses Pandas to analyze the CSV produced by `analyze.py` and display
some information:

```
$ ./pd.py --sum --type project --machine ubuntu-14.04-64 < out.csv
ubuntu-14.04-64      0:40:42.389069
$ ./pd.py --sum --type test --machine ubuntu-14.04-64 < out.csv   
ubuntu-14.04-64      1:18:32.532702
$ ./pd.py --sum --type project --machine ubuntu-14.04-64 < out.csv
ubuntu-14.04-64      0:40:42.389069
$ ./pd.py --sum < out.csv          
debian-9-64          1:35:15.070500
debian-sid-64        0:42:29.183411
fedora-26-64         1:36:25.767790
ubuntu-14.04-64      1:59:14.921771
ubuntu-16.04-32      2:07:21.683569
ubuntu-16.04-64      2:03:27.462327
ubuntu-core-16-64    1:32:37.908490
$ ./pd.py --sum --type test < out.csv
debian-9-64          1:11:59.923472
debian-sid-64        0:35:29.537010
fedora-26-64         0:56:25.528770
ubuntu-14.04-64      1:18:32.532702
ubuntu-16.04-32      1:32:15.126243
ubuntu-16.04-64      1:35:18.275125
ubuntu-core-16-64    1:11:24.466457
$ ./pd.py --top --type test --machine debian-9-64 < out.csv
          machine        duration  type                         test  \
52    debian-9-64 00:06:08.280524  test                tests/unit/go   
2585  debian-9-64 00:05:54.580586  test   tests/main/interfaces-many   
245   debian-9-64 00:02:07.375277  test  tests/regression/lp-1721518   
23    debian-9-64 00:01:00.792648  test                  tests/main/   
25    debian-9-64 00:00:59.818215  test            tests/completion/   
98    debian-9-64 00:00:59.405301  test            tests/regression/   
1016  debian-9-64 00:00:58.706139  test        tests/main/completion   
28    debian-9-64 00:00:52.609423  test                  tests/unit/   
1115  debian-9-64 00:00:51.159301  test    tests/completion/indirect   
700   debian-9-64 00:00:50.992620  test    tests/completion/indirect   

                                                   text  
52    2017-12-13 20:07:59 Executing linode:debian-9-...  
2585  2017-12-13 20:23:27 Executing linode:debian-9-...  
245   2017-12-13 20:10:23 Executing linode:debian-9-...  
23    2017-12-13 20:06:35 Preparing linode:debian-9-...  
25    2017-12-13 20:06:52 Preparing linode:debian-9-...  
98    2017-12-13 20:08:46 Preparing linode:debian-9-...  
1016  2017-12-13 20:15:37 Executing linode:debian-9-...  
28    2017-12-13 20:07:01 Preparing linode:debian-9-...  
1115  2017-12-13 20:16:10 Executing linode:debian-9-...  
700   2017-12-13 20:13:48 Executing linode:debian-9-...  
```

See `--help** for options. 

**NOTE**: you need to have Pandas installed.
