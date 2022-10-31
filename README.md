## What is it?

Profiling tool to know how much time your application is spending in the kernel, and where.

## How to use

### SystemTap

You need to be able to use SystemTap. So you need to run it either using super-user privilege, or your user needs to be in the `stapsys` and `stapusr` groues (or `stapdev`, which I have not tried).

You might run into a bug, in which case I am sorry, you can only run as root:
https://sourceware.org/bugzilla/show_bug.cgi?id=27224

```
Pass 5: starting run.
ERROR: Cannot attach to module stap_6638b4694fd6fbe2db2fb1bcd25a2194_9538 control channel; not running?
ERROR: Cannot attach to module stap_6638b4694fd6fbe2db2fb1bcd25a2194_9538 control channel; not running?
ERROR: 'stap_6638b4694fd6fbe2db2fb1bcd25a2194_9538' is not a zombie systemtap module.
WARNING: /usr/bin/staprun exited with status: 1
```

### Dependencies (for SystemTap)

Your system needs to have the kernel headers with debug info. For instance, on my Debian 11:

```
sudo apt install linux-headers-5.10.0-18-amd64
sudo apt install linux-image-$(uname -r)-dbg
```

Otherwise, SystemTap will complain about  `/..../.config` missing or about debug info:

```
WARNING: cannot find module kernel debuginfo: No DWARF information found [man warning::debuginfo]
```

if /boot/System.map-`uname -r` contains weird stuff:
```
sudo cp /usr/lib/debug/boot/* /boot
```

Otherwise, see: 
https://manpages.ubuntu.com/manpages/bionic/man7/warning::symbols.7stap.html

### Test your installation

Run something using:

```
stap -v -e 'probe vfs.read {printf("read performed\n"); exit()}'
```

## How to use STaKTAU

### Example program

In the directory `examples`, you can find a mini example. Compile it with `make` or:
```
gcc -g -o toto toto.c -lpthread
```

### Collecting data

Run your program using the following command:
```
stap -o traces.txt                    \
     -d kernel -d example/toto --ldd  \  
     src/staktau.stp                  \
     -c example/toto
```
* In this example, you are running the program `examples/toto`
* You need to tell SystemTap to embed information with `-d kernel -d examples/toto --ldd`
* The information collected by STaKTAU will be put into traces.txt

### Analyze this data

The tool `staktau-prof.py` reads the traces and displays the time spent in every syscall:

```
src/staktau-prof.py traces.txt
```

The output gives the data for each thread:

```
----- TID 9392 -----
call                    | time
---------------------------------
STaK-TAU application    | 51276805
rt_sigsuspend           | 2712233
rt_sigaction            | 211359
rt_sigprocmask          | 128551
[...]
```

## Coming soon

* VFS
* merging with TAU traces

## Author

Licence: GPL
2022 Camille Coti, Université du Québec à Montréal