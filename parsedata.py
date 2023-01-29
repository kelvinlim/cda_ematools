#! /usr/bin/env python


import os
import pandas as pd
import numpy
import yaml
import argparse
from sklearn.preprocessing import StandardScaler
#from check_sampling import Sampling
import json
import numbers
from cmath import nan

class ParseData3:
    
    """
    parse data for CDA using a yaml configuration file 

    ParseData3 is designed to add additional outputs for debugging:
    1. data_raw directory - containing subject raw data and 
    subject data after na handling but before standardization
    
    2. Try different na value handling, include replacing with a value
    for a specific column.
    
    Can add configuration in the yaml file
    Should also specify the ordering of the processing by function label.
    e.g. rename  drop  

    3. 
    """
    
    def __init__(self,yamlpath = '', verbose=True):
        
        self.verbose = verbose
        self.no_std = False

        # parse the yamlpath to get directory and file
        self.yamlpath = yamlpath
        self.dir = os.path.dirname(yamlpath)
        self.yamlfile = os.path.basename(yamlpath)

        self.read_config()

        # set values based on config file
        if 'missing_raw' in self.cfg['variables']:
            if self.cfg['variables']['missing_raw'] =='pad':
                self.na_handle='pad'
            else:
                self.na_handle='drop'

        self.df = self.read_datafile()

        # create datadir
        self.create_directories()
        
       
        self.test1()

        pass

    def test1(self):
        """
        Do the test
        """

        # test step processing
        df = self.step_processing('global', self.df, self.cfg['steps_global'])
    

        # check if steps_case key exists
        if 'steps_case' in self.cfg.keys():
            # work on individual cases
            # get the cases
            cases = self.get_cases(df)

            all_cases = 0  # place holder for all cases

            case_summ = []  # store info on each case
            for case in cases:
                summ = {}
                # create ind df
                df_ind = df[df['id'] == case]

                # determine the type of case variable for how
                # to create the label
                if isinstance(case, str):
                    label = str
                elif isinstance(case, numpy.int64):
                    label = f"sub_{case:05d}"
                elif isinstance(case,float):
                    label = f"sub_{int(case):05d}"
                else:
                    print(f"Error: can't create label for {case}")
                    exit(1)

                summ['id'] = label
                summ['len_orig'] = len(df_ind)
                print(label)

                dftmp = self.step_processing(label, df_ind, self.cfg['steps_case'])
                summ['len_clean'] = len(dftmp)

                # append data to all_cases
                if isinstance(all_cases, pd.DataFrame):
                    # concat if df already exists
                    # result = pd.concat([df1, df4], ignore_index=True, sort=False)
                    all_cases = pd.concat([all_cases,dftmp],ignore_index=True, sort=False )
                else:
                    # make copy
                    all_cases = dftmp.copy()

                # append summary info
                case_summ.append(summ)

            # write out all_cases
            fname = f"all_cases.csv"
            path = os.path.join(self.datadir, fname )
            all_cases.to_csv(path, index=False)

            # write out case summary info
            summ = pd.DataFrame(case_summ)  # convert into dataframe
            fname = 'case_details.csv'
            path = os.path.join(self.dir,fname )
            summ.to_csv(path, index=False) 
            
        # create the prior file
        self.create_prior_file()
        pass

    def step_processing(self, label, df, steps):
        """
        Performs the processing steps described in the steps list
        on the dataframe df using the provided label
        """

        # loop through each step in the steps list
        for step in steps:
            # print out info for the step
            if self.verbose:
                print(step)

            oper = step['op']

            if oper == 'rename':
                df = self.step_rename(label,df, step)
            elif oper == 'clean':
                df = self.step_clean(label, df, step)
            elif oper == 'sort':
                df = self.step_sort(label, df, step)
            elif oper == 'drop':
                df = self.step_drop(label, df, step)
            elif oper == 'keep':
                df = self.step_keep(label, df, step)
            elif oper == 'missing_value':
                df = self.step_missing_value(label, df, step)
            elif oper == 'save':
                df = self.step_save(label, df, step)           
            elif oper == 'sum_columns':
                df = self.step_sum_columns(label, df, step)
            elif oper == 'add_lag':
                df = self.step_add_lag(label, df, step)
            elif oper == 'standardize':
                df = self.step_standardize(label, df, step)
            elif oper == 'recode':
                df = self.step_recode(label, df, step)
            elif oper == 'reverse':
                df = self.step_reverse(label, df, step)
            elif oper == 'query':
                """Perform a dataframe query"""
                df = self.step_query(label,df,step)
            else:
                print(f"Error: {oper} not found")
                exit(1)

            self.varlist = list(df.columns)
        return df

    def step_query(self, label, df, step):
        """
        Perform query on the dataframe

        Example to select time==1 
          - 
            op: query
            arg:
                txt: time==1
      
        """
        newdf = df.query(step['arg']['txt'])
        return newdf

    def step_rename(self, label, df, step):
        """
        Perform this step on the dataframe

        self.dft.rename(columns=self.cfg['variables']['rename'], inplace=True)
        pass
        """
        newdf = df.rename(columns=step['arg'], inplace=False)
        return newdf

    def step_sort(self, label, df, step):
        """
        Perform this step on the dataframe
        """
        newdf = df.sort_values(by=step['arg'], inplace=False)
        return newdf

 
    def step_clean(self,label, df, step):
        """
        for a df, check each column of type O.
        Convert an empty string or string with only spaces into 
        a nan
        """

        newdf = df.copy()

        for colname in newdf.columns:
            # check if colunn is type Object
            if newdf[colname].dtype == 'O': 
                # get the column into a list to operate on it
                dlist = list(newdf[colname])
                newdlist = [] # list to hold transformed data
                for item in dlist:
                    if type(item) == str:
                        if item.strip() == '':
                            # replace with a nan
                            newdlist.append(nan)
                        else:
                            newdlist.append(item)
                    else:
                        # keep original value
                        newdlist.append(item)
                # replace the column with newdlist
                newdf[colname] = newdlist
        
        return newdf
    def step_drop(self, label, df, step):
        """
        Perform this step on the dataframe
        """
        newdf = df.drop(columns=step['arg'], inplace=False)
        return newdf

    
    def step_keep(self, label, df, step):
        """
        Perform this step on the dataframe
        """
        newdf = df[step['arg']]
        return newdf

    def step_missing_value(self, label, df, step):
        """
        Perform this step on the dataframe
        """

        if step['arg'] == 'drop':
            # how to drop if empty string?
            newdf = df.dropna()
        elif step['arg'] == 'pad':
            newdf = df.fillna(axis='columns', method='pad')
        return newdf

    def step_save(self, label, df, step):
        """
        Perform this step on the dataframe
        """

        # number of rows in df
        nrows = len(df)

        # check for min_rows argument
        if 'min_rows' in step['arg'].keys():
            min_rows = step['arg']['min_rows']
        else:
            min_rows = 0

        if nrows < min_rows:
            print(f"Warning: {label} has less than {min_rows} rows, file not written")
        else:
            # file type from stub
            fstub = step['arg']['stub']
            ftype = fstub.split('.')[1]
            path = os.path.join(self.dir, step['arg']['dir'],
                            f"{label}{fstub}"
                    )
            with open(path, 'w') as fp:
                if ftype == 'csv':
                    df.to_csv(fp, index=False)
        
        return df

    def step_sum_columns(self, label, df, step):
        """
        Perform this step on the dataframe
        """

        newcolnames = list(step['arg'].keys())
        for newcolname in newcolnames:
            # get the columns to sum
            columns = step['arg'][newcolname]

            # initialize new column with insert
            # to avoid warning with df.loc
            # df.loc[:,newcolname] = 0
            df.insert(len(df.columns), newcolname, 0)

            # loop to sum
            for column in columns:
                df.loc[:,newcolname] += df[column]
                pass

        return df

    def step_add_lag(self, label, df, step):
        """
        Create a new df with lagged elements
        
        Lose the first row of data since it doesn't have any prior 
        (lagged) data.
        
        Parameters
        ----------
        df : TYPE
            DESCRIPTION.
        Returns
        -------
        new df with lagged variables added
        with _lag suffix
        """
        dfbase = df.copy()
        dfbase = dfbase[1:]  # drop first row
        dfbase = dfbase.reset_index(drop=True)  # reset the index
        
        # 2. make copy of df for lag and remove the last row
        dflag = df.copy()
        dflag = dflag[:-1]
        dflag = dflag.reset_index(drop=True)  # reset the index

        
        # 3. change the column names the dflag, adding lag to each column label
        colnames = list(dflag)
        # create list with new column names
        new_colnames = []
        for colname in colnames:
            new_colname = colname + '_lag'
            new_colnames.append(new_colname)
        
        # assign the new column names
        dflag.columns = new_colnames
        
        # concatenate the base and lag dataframes
        result = pd.concat([dfbase, dflag], axis=1, join='inner')
        return result

    def step_standardize(self, label, df, step):
        """
        standardize the columns in the dataframe
        https://machinelearningmastery.com/normalize-standardize-machine-learning-data-weka/
        
        * get the column names for the dataframe
        * convert the dataframe into into just a numeric array
        * scale the data
        * convert array back to a df
        * add back the column names
        * return the df
        """
        
        # describe original data - first two columns
        if self.verbose:
            print(df.iloc[:,0:2].describe())

        # get column names
        colnames = df.columns
        # convert dataframe to array
        data = df.values
        # standardize the data
        std_data = StandardScaler().fit_transform(data)
        # convert array back to df, use original colnames
        newdf = pd.DataFrame(std_data, columns = colnames)
        # describe new data - first two columns
        if self.verbose:
            print(newdf.iloc[:,0:2].describe())

        return newdf

    def step_recode(self, label, df, step):
        "Recode columns"

        colnames = list(step['arg'].keys())
        for colname in colnames:
            # get the column 
            col_old = df[colname]
            col_new = []

            for val in col_old:
                if pd.isna(val):
                    # set to string for key lookup
                    val = 'nan'

                # check if val is in the dict
                if val in step['arg'][colname]:
                    newval = step['arg'][colname][val]
                else:
                    # assume it is a number
                    newval = val
                col_new.append(newval)
        
            # replace with newdata
            df[colname] = col_new
        
        return df

    def step_reverse(self, label, df, step):
        "Reverse coding of columns providing intercept and slope"

        newdf = df.copy()  # create a copy of df

        colnames = list(step['arg'].keys())
        for colname in colnames:
            # get the args for this colname
            # expect orig, intercept and slope
            # only need to set once at beginning as
            # this should stay constant unless changed
            for arg in step['arg'][colname].keys():
                if arg == 'orig':
                    origcol = step['arg'][colname][arg]
                elif arg == 'intercept':
                    intercept = step['arg'][colname][arg]
                elif arg == 'slope':
                    slope = step['arg'][colname][arg]            
            
            # new create the new column using the arguments
            newdf[colname] = slope * newdf[origcol] + intercept
            pass

        return newdf

    def get_cases(self, df):
        "Returns the unique cases in df based on id"
        ids = df['id'].unique()
        ids = sorted(ids)
        return ids


    def create_prior_file(self, no_lag=False):
        "Create the prior.txt file needed by causal-cmd if it doesn't exist"

        # need the variables
        vars = []
        lagvars = []

        # extract the non lag vars
        for var in self.varlist:
            if '_lag' in var:
                lagvars.append(var)
            else:
                vars.append(var)

        # check if prior.txt file already exists
        path = os.path.join(self.dir, 'prior.txt')

        if not os.path.exists(path):
            
            s = ''
            s += '/knowledge\n'
            s += '\n'
            s += 'addtemporal\n'

            if not no_lag:
                s += '1 '
                s += " ".join(lagvars)
                s += '\n'
                s += '2 '
                s += " ".join(vars)
                s += '\n' 

            s += '\n'
            s += 'forbiddirect\n'
            s += '\n'
            s += 'requiredirect\n'

            # write text to file
            fp = open(path,'w')
            n = fp.write(s)
            fp.close()

        pass

    
    def create_directories(self):
        """
        Create the data directories specified in the config file under the 
        directories key
        """

        dirkey = "directories"
        # check if dirkey is present
        if dirkey in self.cfg.keys():
            
            self.datadir = os.path.join(self.dir, self.cfg[dirkey]['datadir'])
            
            for dir in self.cfg[dirkey]:
                # create the data directory
                newdir  = os.path.join(self.dir, self.cfg[dirkey][dir])
                os.makedirs(newdir, exist_ok=True)
  

    def create_directories_v1(self):
        """
        Create the data directories: data, data_raw
        """

        # create the data directory
        self.datadir = os.path.join(self.dir, self.cfg['datadir'])
        os.makedirs(self.datadir, exist_ok=True)

        # create the data_raw directory
        self.rawdatadir = os.path.join(self.dir, 
                                f"{self.cfg['datadir']}_raw")
        os.makedirs(self.rawdatadir, exist_ok=True)

   
    def read_config(self):
        "read in the yaml config file"
        with open(self.yamlpath, 'r') as file:
            self.cfg = yaml.safe_load(file)

        if self.cfg['version'] < 2.1:
            print("Error: mininimum version is 2.1")
            exit(1)

        pass
        
    def read_datafile(self):
        "Read the datafile into a dataframe"
        try:
            # open file
            file = self.cfg['datafile']
        except:
            print("Error opening file")
            exit(1)

        ext = os.path.splitext(self.cfg['datafile'])[1]
        if ext=='.csv':
            return pd.read_csv(file)
        elif ext=='.xlsx':
            return pd.read_excel(file)
        elif ext=='.sav':
            return pd.read_spss(file)


    def standardize_df_col(self, df, diag=True):
        """
        standardize the columns in the dataframe
        https://machinelearningmastery.com/normalize-standardize-machine-learning-data-weka/
        
        * get the column names for the dataframe
        * convert the dataframe into into just a numeric array
        * scale the data
        * convert array back to a df
        * add back the column names
        * return the df
        """
        
        # describe original data - first two columns
        if diag:
            print(df.iloc[:,0:2].describe())
        # get column names
        colnames = df.columns
        # convert dataframe to array
        data = df.values
        # standardize the data
        std_data = StandardScaler().fit_transform(data)
        # convert array back to df, use original colnames
        newdf = pd.DataFrame(std_data, columns = colnames)
        # describe new data - first two columns
        if diag:
            print(newdf.iloc[:,0:2].describe())

        return newdf


                       
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parses data for cda using a yaml file for configuration"
    )
    """
    parser.add_argument('yamlfile',  type=str, nargs=1,
                    help='yamlfile')
    """

    parser.add_argument("--yaml", type = str,
                     help="path to yaml config file",
                     default='') 
    parser.add_argument("--verbose", help="print diagnostic messages",
                        default=False, action = "store_true")   
   
    args = parser.parse_args()
    

    test = False

    if test:

        print("**** Warning - running in test mode")
        yamlpath = 'proj_bnbinge_gfci_lag_hints/config.yaml'
        yamlpath = 'proj_shui/config.yaml'
        p = ParseData3( yamlpath = yamlpath, 
                        verbose = True, #args.verbose,                        
                    )
    else:
        p = ParseData3(  yamlpath = args.yaml, 
                        verbose = args.verbose,
            )