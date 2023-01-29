#! /usr/bin/env python

import semopy 
import pandas as pd
import os
import pathlib
import argparse
import datetime
import sys
import yaml
from PIL import Image, ImageDraw


class Sem:
    
    def __init__(self, noplot=False, mdir='.', nolabel=False, config='config.yaml'):

        # read in the config file
        with open(os.path.join(mdir, config)) as fp:
            self.causal_args = yaml.safe_load(fp)['causal-cmd']
        
        self.algo = self.causal_args['algorithm']
        
        self.noplot_flag = noplot  #  set plot flag
        self.nolabel = nolabel
        self.mdir = mdir  # main working directory
        self.outputdir = os.path.join(self.mdir,'output_' + self.algo)
        # check if directory exists if not create
        if not os.path.isdir(self.outputdir):
            os.makedirs(self.outputdir)
        
    def run_sem(self, prefix, data_prefix=''):  
        modelfile = os.path.join(self.outputdir, prefix + '.lav')
        plotfile_png = os.path.join(self.outputdir, prefix + '.png')
        plotfile_label_png = os.path.join(self.outputdir, prefix + '_label' + '.png')

        plotfile_pdf = os.path.join(self.outputdir, prefix + '.pdf')
        
        fp = open(modelfile, 'r')
        desc = fp.read()
        
        # read in data
        if not data_prefix:
            # use prefix for data file
            data_prefix = prefix
        
        datafile = os.path.join(self.mdir, 'data', data_prefix + '.csv')
        data = pd.read_csv(datafile)
        model = semopy.Model(desc)
        ## TODO - check if there is a usable model,
        ## for proj_dyscross2/config_v2.yaml - no direct edges!
        ## TODO - also delete output files before writing to them so that
        ## we don't have hold overs from prior runs.
        opt_res = model.fit(data)
        estimates = model.inspect()
        stats = semopy.calc_stats(model)

        
        if not self.noplot_flag:
            g = semopy.semplot(model, plotfile_png,  plot_covs = True)
            
            if not self.nolabel:
                # add label to the png
                # https://www.tutorialspoint.com/python_pillow/python_pillow_writing_text_on_image.htm
                img = Image.open(plotfile_png)
                d1 = ImageDraw.Draw(img)
                d1.text((10, 10), prefix, fill=(128, 128, 128, 128))
                #img.show()
                img.save(plotfile_label_png)

            # create pdf    
            g = semopy.semplot(model, plotfile_pdf, plot_covs = True)
            
            # rename the gv file from no prefix to prefix + '.gv'
            gvfile_no_suff = os.path.join(self.outputdir, prefix)
            gv_file = os.path.join(self.outputdir, prefix + '.gv')
            if os.path.isfile(gvfile_no_suff):
                os.rename( gvfile_no_suff, gv_file)
                

        # write out estimates
        estimates.to_csv(os.path.join(self.outputdir, prefix +'_semopy.csv'),
                         index=False)
        estimates.to_json(path_or_buf=os.path.join(self.outputdir, prefix + '_semopy.json'),
                          orient='records')
        # write out the fit indices
        with open(os.path.join(self.outputdir, prefix +'_semopyfit.txt'), 'w') as f:
            print(stats.T, file=f)
        
def main(index=[0,None], noplot=False , show_error=False, use_lav=True,
         mdir = '.', nolabel=False, flist=False):
    c = Sem(noplot=noplot, mdir=mdir, nolabel=nolabel)


    if use_lav:  # use the lavaan files as input
        files = os.listdir(os.path.join(mdir,c.causal_args['out']))   
        files = list(filter(lambda f: f.endswith('.lav'), files))
        files.sort()
    else:
        files = os.listdir(os.path.join(mdir,"data"))   
        files = list(filter(lambda f: f.endswith('.csv'), files))
        files.sort()

    if flist:
        count = 0
        for file in files:
            print(f"{count}: {file}")
            count += 1
        exit()

    
    #for file in ['sub_1001.csv']:
    count = index[0]
    for file in files[index[0]:index[1]]:
        # run semopy to calculate the parameters
        now = datetime.datetime.now()
        print("=====================================")
        print ('start:', now.strftime("%Y-%m-%d %H:%M:%S"))

        prefix = pathlib.Path(file).stem
        print(f"{count}: {prefix}")
        
        # if model is is filename, use the first part of fname as data_prefix
        # this allows us to use the same data file but for a different model file
        if 'model' in file:
            data_prefix = file.split('_')[0]
        else:
            data_prefix = ''

        if show_error:
            # no error trapping
            c.run_sem(prefix,data_prefix=data_prefix )
        else:
            # use try/except so that program continues running
            try:
                c.run_sem(prefix,data_prefix=data_prefix)
            except: # catch *all* exceptions
                e = sys.exc_info()[0]
                print( "Error: ", e )

                
        now = datetime.datetime.now()
        print ('finish:', now.strftime("%Y-%m-%d %H:%M:%S"))
        count += 1
 
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description = "Does the sem estimates for the lavaan model. \
            The semopy package is used."
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
    parser.add_argument("--showerror", type = str,
                        help="show full error and halts instead of catching",
                        default=True)
    parser.add_argument("--list", help="list the files to be processed",
                        action = "store_true")
    parser.add_argument("--noplot", help="do not create the plot files, \
        default is to create the plot files",
        action = "store_true", default = False)
    parser.add_argument("--nolabel", help="do not add subject label to plots, \
        default is  to add labels",
        action = "store_true", default = False)  
    parser.add_argument("--test", help="test mode",
        action = "store_true", default = False)    
    args = parser.parse_args()

    # setup default values
    if args.end != None:
        args.end = int(args.end)

    if args.test:
        main( index = [args.start, args.end], noplot=args.noplot,
            show_error = args.showerror, 
            mdir= 'proj_dyscross2', # args.mdir, 
            nolabel=args.nolabel,
            flist=args.list)    
    else:     
        main( index = [args.start, args.end], noplot=args.noplot,
            show_error = args.showerror, mdir=args.mdir, nolabel=args.nolabel,
            flist=args.list)
  

        
