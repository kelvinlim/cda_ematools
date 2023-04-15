#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import networkx as nx
import os
import glob
import sys
import json
from pathlib import Path
import pandas as pd    
import pydoc_data

import sys
sys.path.append("../cda_ematools")

from graphmetrics import GraphMetrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="thin a graph based on key nodes"
    )
 
    parser.add_argument("--gfile", type = str,
                     help="path to semopy csv",
                     default='.') 

    parser.add_argument("--node", type = str,
                     help="keynode e.g. urge_kill_self",
                     default='') 
    
    args = parser.parse_args()

    test = False

    gtype = 'dot'

    if test:

        c = GraphMetrics()
        args.gfile = 'proj_enacts2/output_gfci/f72765_semopy.csv'
        args.gfile = '/Users/kolim/Projects/cda_avw_airp/proj_airp3/output_gfci/sub_00001_semopy.csv'
        edges = c.read_semfile_edges(args.gfile)
        # create a graph
        dg = c.create_graph(edges)
        keynode = 'HighPain_post'
        # keynode = 'urge_kill_self'

        newgraph = c.get_ancestor_edges(dg,keynode,verbose=True,type=gtype)

        # output a graph
        #graph = nx.drawing.nx_pydot.to_pydot(newdg)

        outfile = args.gfile.replace('py.csv','py_thin.gv')

        c.render_gv(newgraph, outfile)
        pass

    else:

        c = GraphMetrics()
        edges = c.read_semfile_edges(args.gfile)
        # create a graph
        dg = c.create_graph(edges)
        keynode = args.node

        newgraph = c.get_ancestor_edges(dg,keynode,verbose=True,type=gtype)

        # output a graph
        #graph = nx.drawing.nx_pydot.to_pydot(newdg)

        outfile = args.gfile.replace('py.csv','py_thin.gv')

        c.render_gv(newgraph, outfile)
        pass        