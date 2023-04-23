#! /usr/bin/env python3

import os
import semopy
import pandas as pd
from sklearn.preprocessing import StandardScaler
import argparse
import yaml
import glob
import graphviz
from PIL import Image, ImageDraw
from run_causal_cmd import CausalWrap

class PlotModel:
    
    """
    class that plots a model
    
    """
    
    def __init__(self):
        pass

    def init(self,mdir='.', config='config.yaml'):
        
        # set the default arguments for causal-cmd reading from the config.yaml file
        """
        causal-cmd:
            alpha:
            algorithm: fges
            dataset: 
            data-type: continuous
            delimiter: comma
            out: output_fges
            penaltyDiscount: 1.0
            prefix:
            score: sem-bic
            skip-latest: True
            test:
            thread: 1
            version: 1.1.1
            cmdpath: ~/bin
        """
        
        with open(os.path.join(mdir, config)) as fp:
            self.cfg = yaml.safe_load(fp)
            self.causal_args = self.cfg['causal-cmd']


        
        self.args = {
            'mdir': mdir

            }
        
        self.edges = []
        self.model = ''

        # make the output directory
        self.make_out_dir()
        pass
        
    def make_out_dir(self):
        "Make the output directory"

        dirname = f"output_{self.causal_args['algorithm']}"
        os.makedirs(dirname, exist_ok=True)


    def generate_gv_model(self, semdf=pd.DataFrame(), min_pvalue=.05):
        """
        Generate a gv model from the causal-cmd txt output edges

        Include a label for the edge strength
        
        # can only do --> and o->

        """

        # load all the edges into a list of dictionaries for processing
        edge_d = []
        for edge in self.edges:
            tmp = edge
            # check if there is semdata
            if not semdf.empty:
                # check if there is data for this edge
                goodedge = semdf.query(f"lval=='{edge['b']}' & rval=='{edge['a']}'")

                if not goodedge.empty: # edge meets criteria
                    tmp['strength'] = float(goodedge.Estimate)
                    tmp['p_value'] = float(goodedge.p_value)
                else:
                    # place empty string
                    tmp['strength'] = ''
                    tmp['p_value'] = ''
            else:
                    # place empty string
                    tmp['strength'] = ''
                    tmp['p_value'] = ''

            # include this edge based on pvalue?
            if isinstance(tmp['p_value'],float):
                
                if (tmp['p_value'] <= min_pvalue):
                    edge_d.append(tmp)
            else:
                edge_d.append(tmp)
            pass

        # initialze variables
        edges_to_plot = self.cfg['plotting']['label_edge_types'] 
        gvstr = 'digraph G {\n'

        for edge in edge_d:
            # check if we want to plot it
            if edge['etype'] in edges_to_plot:
                if isinstance(edge['strength'],float):
                    strengthstr = f"r={edge['strength']:.3f}"

                    if self.cfg['plotting']['show_pvalue']:
                        pvaluestr = f"p={edge['p_value']:.3f}"
                    else:
                        pvaluestr = ''

                    #combine into single label
                    labelstr = f"{strengthstr}\n{pvaluestr}"
                    gvlabel = f'label=" {labelstr}"'
                else:
                    gvlabel = ''

                if edge['etype'] == '-->':
                        info = f"[ dir=forward {gvlabel}]"
                        e = '->'
                elif edge['etype'] == 'o->':
                    info = f"[ dir=both arrowtail=odot {gvlabel}]"
                    e = '->'
                elif edge['etype'] == '<->':
                    info = f"[ dir=both arrowtail=normal {gvlabel} ]"
                    e = '->'
                elif edge['etype'] == 'o-o':
                    if 'r=' in gvlabel:  # there is a sem result
                        # change from o-o to o-> with open arrow to show
                        # this was changed using the hint process
                        info = f"[ dir=both arrowhead=oarrow arrowtail=odot {gvlabel}]"
                        e = '->'
                    else:
                        info = f"[ dir=both arrowhead=odot arrowtail=odot {gvlabel}]"
                        e = '->'
                else:
                    print(f"Error: unknown edge {edge['etype']}")
                    exit(1)

                str1 = f"\t{edge['a']} {e} {edge['b']} {info}\n"

                gvstr += str1
                pass

       
        gvstr += '}\n'

        self.gv_model=gvstr
        pass

    def generate_gv_model2(self, semdf='', min_pvalue=.05):
        """
        Generate a gv model from the causal-cmd txt output edges

        Include a label for the edge strength
        
        # can only do --> and o->

        """

        # initialze variables
        gvstr = 'digraph G {\n'

        # check whether there is a dataframe and not empty
        if isinstance(semdf, pd.DataFrame) and len(semdf)>0:
            
            # add info from the SEM data
            for edge in self.edges:

                gvlabel = ' '  # initialize gvlabel to plot the edge with no label
                if isinstance(min_pvalue, float):
                    # check if there is data for this edge and meets pvalue criteria
                    res = semdf.query(f"lval=='{edge['b']}' & rval=='{edge['a']}' & p_value < {min_pvalue}")
                    # check if this is an edge we want to plot
                    if not res.empty and edge['etype'] in self.cfg['plotting']['label_edge_types']:
                        # create label of strength
                        gvlabel = f'label=" {float(res.Estimate):.3f}"'
                    else:
                        gvlabel = '' # empty gvlabel so that edge is not plotted


                """
                plot edge only if gvlabel is not empty
                """
                if gvlabel:
                    if edge['etype'] == '-->':
                        info = f"[ dir=forward {gvlabel}]"
                        e = '->'
                    elif edge['etype'] == 'o->':
                        info = f"[ dir=both arrowtail=odot {gvlabel}]"
                        e = '->'
                    elif edge['etype'] == '<->':
                        info = f"[ dir=both arrowtail=normal ]"
                        e = '->'
                    elif edge['etype'] == 'o-o':
                        info = f"[ dir=both arrowhead=odot arrowtail=odot ]"
                        e = '->'
                    else:
                        print(f"Error: unknown edge {edge['etype']}")
                        exit(1)

                    str1 = f"\t{edge['a']} {e} {edge['b']} {info}\n"

                    gvstr += str1

            #end

        else:
        # add the edges without benefit of sem data
            for edge in self.edges:
                gvlabel = ''

                if edge['etype'] == '-->':
                    info = f"[ dir=forward {gvlabel}]"
                    e = '->'
                elif edge['etype'] == 'o->':
                    info = f"[ dir=both arrowtail=odot {gvlabel}]"
                    e = '->'
                elif edge['etype'] == '<->':
                    info = f"[ dir=both arrowtail=normal ]"
                    e = '->'
                elif edge['etype'] == 'o-o':
                    info = f"[ dir=both arrowhead=odot arrowtail=odot ]"
                    e = '->'
                else:
                    print(f"Error: unknown edge {edge['etype']}")
                    exit(1)

                str1 = f"\t{edge['a']} {e} {edge['b']} {info}\n"

                gvstr += str1

            #end

        gvstr += '}\n'

        self.gv_model=gvstr
        pass

    def check_edges(self,df):
        "Check for edges defined in yaml file"

        for item in self.cfg['check']['edges'].keys():
            edge = self.cfg['check']['edges'][item]
            a = edge[0]
            e = edge[1]
            b = edge[2]

            # select rows based on edge info
            #newdf = df[(df['a'] == a)  and (df['etype'] == e) and (df['b'] == b)]
            # newdf = df.query(f"a=='{a}' and etype=='{e}' and b=='{b}' and id != 'all_cases'")
            newdf = df.query(f"a=='{a}' and etype=='{e}' and b=='{b}' and {self.cfg['check']['condition']}")
            print(f"{a} {e} {b}: {len(newdf)}")
        pass

    def render_newfile(self, file):
        #src = graphviz.Source.from_file(file)
        graphviz.render('dot','png', file)
        
        plotfile_png = file + '.png'
        # add the label to the plot
        img = Image.open(plotfile_png)
        d1 = ImageDraw.Draw(img)
        
        prefix = os.path.basename(file).split('_edit.gv')[0]
        d1.text((10, 10), prefix, fill=(128, 128, 128, 128))
        #img.show()
        img.save(plotfile_png)

    def parse_edges(self, prefix, file='output/sub_1066.txt'):
        """
        parse the  edges from the output file
        
        get edges and parse into a list of dict
        Graph Edges:
        1. drinks --> drinking dd nl
        
        {'a': 'drinks', 'etype': '-->', 'b': 'drinking', 'extra': ['dd','nl']}

        Parameters
        ----------
        file : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self.edges = []

        # open the file
        with open(file, 'r') as f:
            self.lines = f.readlines()
        
        in_edge = False  # boolean for in_edge section
        
        for line in self.lines:
            if line.startswith('Graph Attributes'):
                in_edge = False  
            # print("info: ", line)
            if in_edge:  # parse the line
                segs = line.split()
                if len(segs) > 0:
                    #print(segs)
                    edge = {}
                    edge['id'] = prefix
                    if len(segs) >= 4:
                        edge['a'] = segs[1]
                        edge['etype'] = segs[2]
                        edge['b'] =  segs[3]
                       
                    if len(segs) > 4:
                        edge['extra'] = [segs[4], segs[5]]
                    else:
                        edge['extra'] = []
                    
                    
                    self.edges.append(edge)
                
            if line.startswith('Graph Edges:'):
                in_edge = True
        



def main(index=[0,None], mdir='.', list=False, algo='gfci', check=False):
    # get the csv files from the data directory

    c = PlotModel()
    c.init(mdir=mdir, config='config.yaml')
 
    # define the output directory
    output = os.path.join(mdir, c.causal_args['out'])

    # get sorted list of files from output directory
    files = glob.glob(os.path.join(output, f"*[0-9].txt"))
    # exit if no files
    if not files:
        print(f"Error: no causal_cmd txt output files found in {output}")
        exit(1)

    files.sort()
    
    if list:
        i = 0
        for file in files:
            print(f"{i}: {file}")
        exit()

    alledges = ''

    for file in files[index[0]: index[1]]:

        c.causal_args['dataset'] = os.path.join(file)
        
        # set the prefix
        prefix = os.path.basename(file).split('.txt')[0]
        c.causal_args['prefix'] = prefix
        
        print(prefix)
        # read in the output file and get the edges
        outputfile = os.path.join( c.args['mdir'], c.causal_args['out'], 
                                  c.causal_args['prefix'] + '.txt')
        c.parse_edges(prefix, file=outputfile)

        # check if there is sem output
        semfile = os.path.join( c.args['mdir'], c.causal_args['out'], 
                                  c.causal_args['prefix'] + '_semopy.csv')     
        if os.path.exists(semfile):
            # read into a dataframe
            semdf = pd.read_csv(semfile)
            semdf.rename(columns={'p-value':'p_value'}, inplace=True)
        else:
            # create an empty Dataframe
            semdf = pd.DataFrame()

        # add to list of all edges 
        if alledges:
            # extend list
            alledges.extend(c.edges)
        else:
            alledges = c.edges

        if not check:
            # create graphviz model from edges  self.gv_model
            c.generate_gv_model(semdf=semdf)

            # write out the gvmodelfile
            gvmodelfile = os.path.join( c.args['mdir'], c.causal_args['out'], 
                                    c.causal_args['prefix'] + '_' +
                                    c.causal_args['algorithm'] + '.gv')
            with open(gvmodelfile, 'w') as fp:
                fp.write(c.gv_model) 
            
            # create a png or other output 
            c.render_newfile(gvmodelfile)

               
        pass
    # convert alledges into a df
    df = pd.DataFrame(alledges)
    # write out df to file
    fpath = os.path.join(c.args['mdir'], 'edges.csv')
    df.to_csv(fpath, index=False)

    if check:
        # check the edges
        c.check_edges(df)

    pass
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates plots using edges from causalc-cmd txt file output. \
            Currently supports just the gfci edges."
    )
    parser.add_argument("--start", type = int,
                        help="beginning file list index , default 0",
                        default = 0)
    parser.add_argument("--end", type = str,
                        help="end file list index, default None",
                        default=None)
    parser.add_argument("--mdir", type = str,
                     help="main directory, default is the current directory",
                     default='proj_bnbinge_gfci') 
    parser.add_argument("--algo", type = str,
                        help="set algorithm [gfci]. \
                            Output directory will have the algo \
                                appended - output_gfci.  default gfci",
                        default='gfci')
    parser.add_argument("--list", help="list the files to be processed",
                        action = "store_true")
    parser.add_argument("--check", help="check for edges listed in config",
                        action = "store_true",
                        default = False)

    """
    parser.add_argument("--test", help="test mode",
                        action = "store_true",
                        default = False) 
    """
    
    args = parser.parse_args()
    
    # setup default values
    if args.end != None:
        args.end = int(args.end)
    
    test = False

    if test:
        print("***** Running in test mode ****")
        main(index=[0,None], 
            #mdir = "./proj_bnbinge_gfci_lag_hints", # args.mdir, 
            mdir = "./proj_run3",
            list=args.list,
            algo = args.algo, 
            check=False)
    else:
        main(index=[args.start, args.end], mdir = args.mdir, list=args.list,
            algo = args.algo, check=args.check)