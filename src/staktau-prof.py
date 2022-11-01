#!/usr/bin/env python3

###
# STaKTAU, performance analyzing tool for the kernel
# Trace analyzing tool.
# Licence: GPL
# Camille Coti, 2022, Université du Québec à Montréal
##

import sys
from anytree import Node, RenderTree, PreOrderIter # Needed for the tree stuff

'''
' Usage:
' stak-tau.py filename [options]
' Possible options:
' -l: long output (default: short)
'''

'''
' export:
>>> from anytree.exporter import DotExporter
>>> # graphviz needs to be installed for the next line!
>>> DotExporter(udo).to_picture("udo.png")
'''


opt = {
    'long': False
}    

def print_dico( dic ):    
    for t, v in dic.items():
        print( t )
        for k,l in v.items():
            print( '\t', k )
            for e,f in l.items():
                print( '\t\t', e, ':', f )

def print_tree( root ):
    for pre, fill, node in RenderTree( root ):
        print("%s%s" % (pre, node.name))

# New call: read the line
# format:
# 0 rt_sigsuspend([EMPTY], 8) [2899] time 1665535875621246262 1849647674295

def split_probe( line ):
    ln = line.split( ')' )

    # are we entering or exiting the call
    if line[0] == '0': enter = True
    else             : enter = False

    # the call itself
    ll = ln[0].split()
    if len( ll ) > 2 : call = ''.join( ll[1:] )
    else             : call = ll[1]
    call += ')'  # this parenthesis was removed by the split( ')' )

    # pid / tid
    ewhje = ln[1].split() 
    tid = ewhje[0]
    tid = int( tid[1:-1] ) # remove the brackets

    # TSC: last field
    tsc = int( ewhje[-1] )

    return( enter, call, tid, tsc )

# Read a stack (user or kernel)
# Format:
# KERNEL backtrace from kprobe.function("__x64_sys_rt_sigsuspend")?:
# 0xffffffffbae9e0f0 : __x64_sys_rt_sigsuspend+0x0/0x70 [kernel]
# 0xffffffffbb6e5683 : do_syscall_64+0x33/0x80 [kernel]
# 0xffffffffbb8000a9 : entry_SYSCALL_64_after_hwframe+0x61/0xc6 [kernel]
# 0xffffffffbb8000a9 : entry_SYSCALL_64_after_hwframe+0x61/0xc6 [kernel] (inexact)

def read_stack( fd, ln ):
    stack = []
    #l1 = ln.split( '\"' )
    l1 = ln.split( )
    call = l1[-1]
    for line in fd:
        if line.startswith( '--' ):
            return call, stack

        stack.append( line )


# Read the file and act upon what we find

def readfile( fn ):
    probes = {}    
    with open( fn ) as fd:
        for line in fd:
           if line[0] == '0' or line[0] =='1':
               enter, call, tid, tsc = split_probe( line )
               #_ = fd.readline() # not used yet
               if not tid in probes:
                   probes[ tid ] = {}
               probes[ tid ][ ( tsc, enter ) ] = { 'call': call }
           # print( tsc )
           if line.startswith( '--' ):
               pass
               #line = fd.readline() ## discard the line
           if line.startswith( 'KERNEL' ):
                call, kernel_btrace = read_stack( fd, line )
                probes[ tid ][ ( tsc, enter )  ][ 'kernel btrace' ] = kernel_btrace
           if line.startswith( 'USER' ):
                call, user_btrace = read_stack( fd, line )
                probes[ tid ][ ( tsc, enter )  ][ 'user btrace' ] = user_btrace
            #fd.readline() ## discard the last line
    return probes

# Take a list of timestamps and build a tree
# Actually, build a tree for each thread
# Pass a dict: tid: probes
# probes is a dict: (timestamp, enter): info
# info is a dict containing: call, user btrace, kernel btrace

# TODO we never exit exit()
# -> duration in the root node

def build_tree( probes ):
    trees = {}
    for tid in probes:
        prev_ts = 0
        total = sys.maxsize
        prev_enter = False
        root = Node( { 'call': "STaK-TAU application", 'time': 0 } )
        parent = root
        current = root

        trace = probes[ tid ]
        # Timestamps might not be sorted: sort keys
        # keys are two-element tuples, Python sorts them by first element by default
        for toto in sorted( trace.keys() ):
            ts, enter = toto
            total = min( total, ts )
            info = trace[ toto ]
            if not enter:
                # Exiting a call -> go up
                # and close the timer
                current.name[ 'time' ] = ts - current.name[ 'time' ]
                current = parent
                parent = current.parent
            if enter:                
                # TODO add more info in the node
                # Enter a call. Are we already in a call?
                # yes -> the parent is the current call
                call = Node( info, parent = current )
                current = call
                if not current.name[ 'call' ].startswith( "exit" ):
                    current.name[ 'time' ] = ts
                else:
                    total = ts - total
                    current.name[ 'time' ] = 0
                parent = current.parent
              #  print( "enter ", current.name )
                                    
            prev_enter = enter

        # print_tree( root )
        root.name[ 'time' ] = total
        trees[ tid ] = root

    return trees
                
# Compute the traces, ie how much time is spent in each call
def compute_trace( trees ):
    accumulate = {}
    for tid in trees:
        accumulate[ tid ] = {}
        tree = trees[ tid ]
        for node in PreOrderIter( tree ):
            # What is the name of the measured call?
            call_name = node.name[ 'call' ]
            if not opt[ 'long' ]:
                call_name = call_name.split( '(' )[0]
            # Accumulate the times spent in this given call
            if not call_name in accumulate[ tid ]:
                accumulate[ tid ][ call_name ] = 0
            accumulate[ tid ][ call_name ] += node.name[ 'time' ]

    return accumulate

# Print these traces
def print_trace( trace ):
    maxlen = max( [ len( k ) for tid in trace for k in trace[ tid ] ] )
    formt =  3 + maxlen
    
    for tid in trace:
        print( "----- TID %d -----" % tid )
        call = 'call'
        print( f'{call:<{formt}} | time')
        print( '-' * formt + '-' * 10 )
        #  print( trace[ tid ] )
        for call, dur in trace[ tid ].items():
            print( f'{call:<{formt}} | {dur}')

            
            
def main():
    filename = sys.argv[1]
    options = sys.argv[2:]
    if '-l' in options:
        opt[ 'long' ] = False
    
    # print( "Open ", filename )
    probes = readfile( filename )

 #   print_dico( probes )

    trees = build_tree( probes )
    trace = compute_trace( trees )
    print_trace( trace )
    
    return

if __name__ == "__main__":
    main()
    
