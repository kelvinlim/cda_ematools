#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import os
import glob
import sys
import json
from pathlib import Path
import pandas as pd
import graphviz


"""

# generate all the edges
./check_paths.py 1> pathcheck.txt
# count unique cases
awk '{print $5}'  pathcheck.txt | sort  | uniq - | wc
# count all edges
awk '{print $5}'  pathcheck.txt | sort  |  wc

"""
class GraphMetrics:
    
    def __init__(self):
        
        
        pass


        
    def degree_centrality(self,DG):
        
        info = {}  # dict for results
        # degree_centrality
        degree = (nx.degree_centrality(DG))
        # in degree
        degree_in = DG.in_degree()
        degree_out = DG.out_degree()
        
        info['degree'] = degree
        info['degree_in'] = degree_in
        info['degree_out'] = degree_out
        
        """
        # sort the dictionary, returns as list
        s = sorted(nx.degree_centrality(DG).items(),key=lambda x:x[1],
                   reverse=True)
        """
        pass
        return info
        
    def analyze_graph(self, DG):
        # given a directed graph, provide information about graph
        
        # get degree centrality
        deg_cen = self.degree_centrality(DG)
        
        return deg_cen
        
           
    def analyze_path(self, DG):
        # given a directed graph, provide information about the path
        # between the source and destination.  overall weight, 
        # number of edges
        
        try:
            path = nx.dijkstra_path(DG, self.src, self.des)
            pass
        except:
            print("path not found", file=sys.stderr)
            path = []

        info = {}

        info['src'] = self.src
        info['des'] = self.des
        info['case'] = self.basename
        info['nodes'] = path
             
        if path:
            # get info on path
            info['pathlength'] = len(path)           
            # compute the cumulative weight for src to des
            info['weight'] = self.compute_path_weight(DG, path)
        else:
            # set pathlength and weight to 0 since  so no path found
            info['pathlength'] = 0
            info['weight'] = 0
                    
        return  info
        
    def compute_path_weight(self, DG, path):
        # compute the total weight which is product of all edge weights
        # step through the path retrieving weight of each edge
        
        weight = 1  # initialize weight
        for i in range(len(path)-1):
            # remember we are looking at pairs so stop one before end
            src = path[i]
            des = path[i+1]
            weight *= DG[src][des]['weight']
        
        return weight
        
 
    def create_graph2(self, edges):
        DG = nx.DiGraph()
        for edge in edges:
            # add edges to graph
            DG.add_edge(edge['src'], edge['des'], weight=edge['weight'])
        
        return DG          
        
    def create_graph(self, edges):
        DG = nx.DiGraph()
        for edge in edges:
            # add edges to graph
            DG.add_edge(edge['src'], edge['des'], weight=edge['weight'])
        
        return DG
    
    
    
    def read_semfile_edges(self, filepath):
        # read in the edges from semopy csv output file
        # lval,op,rval,Estimate,Std. Err,z-value,p-value
        try:
            fp = open(filepath)
            self.lines = fp.readlines()
        except:
            pass
        
        # place each edge into a list of dicts
        self.edges = []
        
        # drop the first 
        for line in self.lines[1:-1]:
            edge = {}
            parts = line.split(',')
            if parts[1] == '~':
                # L_PI_ROI,~,AMYGDALA_RIGHT,0.2374754445472335,0.03794506605914075,6.258401136286034,3.889444322169311e-10
                # found an edge
                edge['src'] = parts[2]
                edge['des'] = parts[0]
                
                # get the weight                
                edge['weight'] = parts[3]
                edge['err'] = parts[4]    
                edge['zvalue'] = parts[5]    
                edge['pvalue'] = parts[6]    
                             
                self.edges.append(edge)
                #print(self.edges)
            
        return self.edges    
    
    def read_gvfile_edges(self):
        # read in the edges from the gv file into a structure
        try:
            fp = open(self.gvfilepath)
            self.lines = fp.readlines()
        except:
            #print(f'Error in reading {self.gvfilepath}', file=sys.stderr)
            pass
        
        # place each edge into a list of dicts
        self.edges = []
        
        # drop the first and last line
        for line in self.lines[1:-1]:
            edge = {}
            parts = line.split()
            if parts[1] == '->':
                # 'PANAS_NA_lag -> PANAS_PA_lag [label="-0.597\np-val: 0.00"]'
                # found an edge
                edge['src'] = parts[0]
                edge['des'] = parts[2]
                
                # get the weight from this '[label="-0.597'                
                edge['weight'] = float(parts[3].split("\\")[0].split('=')[1].split('"')[1])
                
                # get the pvalue from this '0.00"]' 
                edge['pvalue'] =float( parts[4].split('"')[0])
                
                self.edges.append(edge)
                #print(self.edges)
            
        return self.edges
    
    def get_ancestor_edges(self, G, keynode, verbose=False,type='dot'):
        """
        get the ancestor edges for a keynode in the graph
        """
        newG = nx.DiGraph()
        gv = graphviz.Digraph("mygraph")

        ancestors = nx.ancestors(G, keynode)
        allnodes = ancestors.copy()
        allnodes.add(keynode)
    
        for edge in G.edges:
            if verbose: print(edge)

            for node in ancestors:
                if verbose: print(node)
                if node == edge[0] and   edge[1] in allnodes:
                    # add to newG
                    # get the weight
                    weight = float(G[edge[0]][edge[1]]['weight'])
                    newG.add_edge(edge[0],edge[1], weight=weight)
                    # add to gv graph
                    label = f'r={weight:.3f}'
                    gv.edge(edge[0],edge[1], label=label)
                    if verbose: print(f"ancestor {edge}")
        pass
        
        if type=='dot':
            return gv
        else:
            return newG 
        
    def get_ancestor_edges_mult(self, G, key_list, verbose=False,type='dot'):
        """
        get the ancestor edges for multiple keynodes in the graph

        key_list is a list of the keynodes
        """
        newG = nx.DiGraph()
        gv = graphviz.Digraph("mygraph")

        # initialize an empty set
        allnodes = set()

        for keynode in key_list:
            ancestors = nx.ancestors(G, keynode)
            allnodes |= ancestors
            allnodes.add(keynode)
    
        for edge in G.edges:
            if verbose: print(edge)

            for node in ancestors:
                if verbose: print(node)
                if node == edge[0] and   edge[1] in allnodes:
                    # add to newG
                    # get the weight
                    weight = float(G[edge[0]][edge[1]]['weight'])
                    newG.add_edge(edge[0],edge[1], weight=weight)
                    # add to gv graph
                    label = f'r={weight:.3f}'
                    gv.edge(edge[0],edge[1], label=label)
                    if verbose: print(f"ancestor {edge}")
        pass
        
        if type=='dot':
            return gv
        else:
            return newG 

    def render_gv(self,gv, filename, format='png'):
        """
        write dot commands for graphviz to the filename

        """

        gv.format = format
        gv.render(filename)

    def nx_plot(self,G, outfile):
        """
        Generate a plot file from networkx graph
        https://groups.google.com/g/networkx-discuss/c/hw3OVBF8orc?pli=1
        """    

        # generate pos for the plot
        pos = nx.spring_layout(G)
        nx.draw(G,pos)
        # specify the edges explicitly
        edge_labels=dict([((u,v,),d['weight'])
            for u,v,d in G.edges(data=True)])       
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels)
        plt.savefig(outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="run graph metrics on sem edge data"
    )
    parser.add_argument("--start", type = int,
                        help="beginning file list index , default 0",
                        default = 0)
    parser.add_argument("--end", type = str,
                        help="end file list index, default None",
                        default=None)
    parser.add_argument("--mdir", type = str,
                     help="main directory, default is the current directory",
                     default='.') 
    parser.add_argument("--study", type = str,
                    help="study to analyze - s263 (default), s266, all",
                    default = 's263')
    parser.add_argument("--algo", type = str,
                    help="set algorithm [fges,fci,gfci]. \
                            Output directory will have the algo \
                                appended - output_fges.  default fges",
                    default='fges')

    
    args = parser.parse_args()


    c = GraphMetrics(study=args.study)
