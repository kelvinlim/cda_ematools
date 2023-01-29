#! /usr/bin/env python3

# 20210817 - kolim - use the ts_gfci
import os
import semopy
import pandas as pd
from sklearn.preprocessing import StandardScaler
import argparse
import yaml
import glob

class CausalWrap:
    
    """
    class that wraps the causal-cmd in a python wrapper
    
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
            'rawdata': 'data' ,
            'causal-cmd': 'causal-cmd ',
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

    def set_arg(self, argval):
        """
        set the arguments 

        Parameters
        ----------
        argval : a dictionary of arg value pairs.
            .

        Returns
        -------
        None.

        """
        
        for key in argval.keys():
            # change existing arg or add an arg
            self.causal_args[key] = argval[key]

            # # set the prefix based on the dataset name
            # if key == 'dataset':
            #     prefix = self.causal_args[key].split('.csv')[0]
            #     self.causal_args['prefix'] = prefix
                
                
    def create_cmd(self):
        """
        create the causal-cmd using the arguments

        Returns
        -------
        0 - if OK
        1 if  problem

        """
        
        self.cmd = self.args['causal-cmd']
        
        # check to make sure that critical arguments
        # are set
        
        if (self.causal_args['dataset'] == '') or (self.causal_args['prefix'] == ''):
                # missing args
                return 1
            
        for key in self.causal_args.keys():
            argstr =''
            if key == 'skip-latest':
                if self.causal_args[key] == True:
                    argstr = '--skip-latest '
            elif key == 'json-graph':
                if self.causal_args[key] == True:
                    argstr = '--json-graph '
            elif key == 'dataset':
                # add directory info
                argstr = '--%s %s '%(key, self.causal_args['dataset'])
            elif key == 'alpha':
                if self.causal_args['alpha'] != None:
                    argstr = f"--{key} {self.causal['alpha']} "
            elif key == 'test':
                if self.causal_args[key] != None:
                    argstr = f"--{key} {self.causal[key]} "
            elif key == 'version':
                pass
            else:
                argstr = "--%s %s "%(key, self.causal_args[key])
                
            self.cmd += argstr
            
        
        return 0
    
    def create_cmd_vers(self):
        """
        create the causal-cmd using the arguments including version

        Returns
        -------
        0 - if OK
        1 if  problem

        """
        # create the java command to run the causal-cmd jar
        # java -jar $SCRIPTPATH/causal-cmd-1.1.3-jar-with-dependencies.jar
        jarfile = os.path.join(self.causal_args['cmdpath'], 
                    f"causal-cmd-{self.causal_args['version']}-jar-with-dependencies.jar") 

        # check if jar file exists

        self.cmd = f"java -jar {jarfile} "

        # check to make sure that critical arguments
        # are set
        
        if (self.causal_args['dataset'] == '') or (self.causal_args['prefix'] == ''):
                # missing args
                return 1
            
        for key in self.causal_args.keys():
            argstr =''
            if key == 'skip-latest':
                if self.causal_args[key] == True:
                    argstr = '--skip-latest '
            elif key == 'json-graph':
                if self.causal_args[key] == True:
                    argstr = '--json-graph '
            elif key == 'dataset':
                # add directory info
                argstr = '--%s %s '%(key, self.causal_args['dataset'])
            elif key == 'alpha':
                if self.causal_args['alpha'] != None:
                    argstr = f"--{key} {self.causal_args['alpha']} "
            elif key == 'test':
                if self.causal_args[key] != None:
                    argstr = f"--{key} {self.causal_args[key]} "
            elif key == 'out':
                if self.causal_args[key] != None:
                    mdir = self.args['mdir']
                    #dirname = f"output_{self.causal_args['algorithm']}"
                    dirname = self.causal_args[key]
                    argstr = f"--{key} {os.path.join(mdir, dirname)} "
            elif key == 'knowledge':
                if self.causal_args[key] != None:
                    mdir = self.args['mdir']
                    filename = self.causal_args[key]
                    argstr = f"--{key} {os.path.join(mdir, filename)} "
            # args to ignore, not direct input for causal-cmd, for configuration
            elif key in ['cmdpath','version']:
                pass
            else:
                argstr = "--%s %s "%(key, self.causal_args[key])
                
            self.cmd += argstr
            
        
        return 0

    def parse_edges(self, file='output/sub_1066.txt'):
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
        
    def generate_model(self):
        # generate a model for sem in lavaan format text

        #TODO modify to accomodate different edge strings
        # eg. gfci has o-o
        # gfes has --- -->
        
        self.model = ''  # string to hold the model
        
        for edge in self.edges:
    
            ops = []  # list to hold multiple model edges

            # create the different edges needed
            # based on causal-cmd arguments in config.yaml
            # check if argument exists
            if 'include_model_edges' in self.cfg:
                include_edges = self.cfg['include_model_edges']
            else:
                # default edges to use
                include_edges = [ ['-->','~'] ]

            for include_edge in include_edges:
                if edge['etype'] == include_edge[0]:
                    # got match
                    ops.append(include_edge[1])
                    break  # break out of include_edges for loop

            # check for no usable edges
            if len(ops) > 0: 
                for op in ops:
                    str = '%s %s %s\n'%(edge['b'], op, edge['a'])
                    self.model += str  # append to model string
                    # print(edge, str)
            
        return self.model
    
    def run_sem(self):
        # run the sem to get the edge parameters
        sub = self.causal_args['prefix']
        #modelfile = os.path.join(self.causal_args['out'], "%s.lav"%(sub)
        # TODO write out the model file
        
        # read in the data
        datafile = os.path.join(self.args['rawdata'],
                                self.causal_args['dataset'])
        
        data = pd.read_csv(datafile)
        
        plotfile = os.path.join(self.causal_args['out'], "%s_plot.pdf"%(sub))
        edgefile = os.path.join(self.causal_args['out'], "%s_edge.json"%(sub))
        
        # fit model
        mod = semopy.Model(self.model, mimic_lavaan=False, baseline=False,
                           cov_diag=False)
        res = mod.fit(data)
        #print(res)
        
        # edges
        ins = mod.inspect()
        print(ins)
        
        # output into a json
        ins.to_json(path_or_buf=edgefile, orient='records')
        
        # plot
        g = semopy.semplot(mod, plotfile)

    def standardize_df_col(self, diag=False):
        """
        standardize the columns in the dataframe
        https://machinelearningmastery.com/normalize-standardize-machine-learning-data-weka/
        
        * get the column names for the dataframe
        * convert the dataframe into into just a numeric array
        * scale the data
        * convert array back to a df
        * add back the column names
        * set to the previous df
        """
        
        # describe original data - first two columns
        if diag:
            print(self.newdf.iloc[:,0:2].describe())
        # get column names
        colnames = self.newdf.columns
        # convert dataframe to array
        data = self.newdf.values
        # standardize the data
        data = StandardScaler().fit_transform(data)
        # convert array back to df, use original colnames
        self.newdf = pd.DataFrame(data, columns = colnames)
        # describe new data - first two columns
        if diag:
            print(self.newdf.iloc[:,0:2].describe())

              
 

def main3(index=[0,None], algo='fges', mdir='.', know='prior.txt'):
    # get the csv files from the data directory
    c = CausalWrap(mdir=mdir)
    
    # set standard arguments
    if know: 
        # add prior file argument if a file name is provided
        c.set_arg({'knowledge': os.path.join(mdir,know)})
        
    c.set_arg({'score': 'sem-bic'})
    
    
    # set arguments needed for different algorithms
    if algo =='fges':
        c.set_arg({'algorithm': 'fges'})
        c.causal_args.pop('test')  # no fisher-z-test

    elif algo == 'gfci':
        # for gfci
        c.set_arg({'algorithm': 'gfci'})   
        # test is fisher-z-test
        c.set_arg({'test': 'fisher-z-test'})
    
    elif algo == 'fci':
        # for fci
        c.set_arg({'algorithm': 'fci'})   
        # test is fisher-z-test
        c.set_arg({'test': 'fisher-z-test'})
        c.causal_args.pop('score')  # no score argument
            
            
    # set output directory
    output = os.path.join(mdir, 'output_' + algo)
    c.set_arg({'out': output})
    
    # check if directory exists if not create
    if not os.path.isdir(output):
        os.makedirs(output)
    # get sorted list of files in directory
    files = os.listdir( os.path.join(mdir,"data") )  
    files = list(filter(lambda f: f.endswith('.csv'), files))
    files.sort()
    
    #for file in ['sub_1001.csv']:
    for file in files[index[0]: index[1]]:

        c.set_arg({'dataset': os.path.join(file)})
        
        # set the prefix
        prefix = os.path.basename(file).split('.csv')[0]
        c.set_arg({'prefix': prefix})
        
        c.create_cmd()
        print(c.cmd)
        os.system(c.cmd)
        
        # read in the output file and get the edges
        outputfile = os.path.join( c.causal_args['out'], 
                                  c.causal_args['prefix'] + '.txt')
        c.parse_edges(file=outputfile)
        #print(c.edges)
        # create model from edges
        c.generate_model()
        
        # output the model file
        modelfile = os.path.join(mdir, c.causal_args['out'], 
                                  c.causal_args['prefix'] + '.lav')
        #print(c.model)
        fp = open(modelfile, 'w')
        fp.write(c.model)
        
        # run semopy to calculate the parameters
        #c.run_sem()

def main4(index=[0,None], mdir='.', list=False):
    # get the csv files from the data directory

    c = CausalWrap()
    c.init(mdir=mdir, config='config.yaml')
    
    # check if output directory exists if not create
    output = os.path.join(mdir, c.causal_args['out'])
    if not os.path.isdir(output):
        os.makedirs(output)

    # get sorted list of files from data directory
    files = os.listdir( os.path.join(mdir,"data") )  
    files = glob.glob(os.path.join(mdir,"data", f"*.csv"))
    files.sort()
    
    if list:
        i = 0
        for file in files:
            print(f"{i}: {file}")
        exit()

    for file in files[index[0]: index[1]]:

        c.causal_args['dataset'] = os.path.join(file)
        
        # set the prefix
        prefix = os.path.basename(file).split('.csv')[0]
        c.causal_args['prefix'] = prefix
        
        c.create_cmd_vers()
        print(c.cmd)
        os.system(c.cmd)
        
        # create output directory if it doesn't exist
        os.makedirs(os.path.join(c.args['mdir'],c.causal_args['out']),
            exist_ok=True)
        # read in the output file and get the edges
        outputfile = os.path.join( c.args['mdir'], c.causal_args['out'], 
                                  c.causal_args['prefix'] + '.txt')
        c.parse_edges(file=outputfile)
        #print(c.edges)
        # create model from edges
        c.generate_model()
        
        # output the model file if self.model is not empty
        if c.model != '':
            modelfile = os.path.join(mdir, c.causal_args['out'], 
                                    c.causal_args['prefix'] + '.lav')
            #print(c.model)
            with open(modelfile, 'w') as fp:
                fp.write(c.model)
        
        # run semopy to calculate the parameters
        #c.run_sem()                       
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="runs causal-cmd with fges"
    )
    parser.add_argument("--start", type = int,
                        help="beginning file list index , default 0",
                        default = 0)
    parser.add_argument("--end", type = str,
                        help="end file list index, default None",
                        default=None)
    parser.add_argument("--mdir", type = str,
                     help="main directory, default is the current directory",
                     default='') 
    parser.add_argument("--know", type = str,
                     help="name of the prior file to use, default prior.txt",
                     default='prior.txt') 
    parser.add_argument("--algo", type = str,
                        help="set algorithm [fges,fci,gfci]. \
                            Output directory will have the algo \
                                appended - output_fges.  default fges",
                        default='fges')
    parser.add_argument("--list", help="list the files to be processed",
                        action = "store_true")
    
    args = parser.parse_args()
    
    # setup default values
    if args.end != None:
        args.end = int(args.end)    
        
    test = False
    
    if test:
        main4(  index=[args.start, args.end],
                mdir = 'proj_meditate', # args.mdir, 
                list=args.list
                )
    else:
        main4(index=[args.start, args.end], mdir = args.mdir, list=args.list)