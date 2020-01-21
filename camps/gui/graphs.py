#!/usr/bin/env python
import os
import sys
import numpy as np
import pandas as pd
import random
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid",palette='tab10')
from dataframe import *
from loc_dataframe import *

file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0,path)

import registry.util as cfg
from mospred import read_pred as read_pred
from core import Time as Time

#read graphs control file
ctrl = cfg.read_yaml('../registry/graphs.yaml')
date_range = ctrl.date_range
start,end,stride = read_pred.parse_range(date_range)
start = Time.str_to_datetime(start)
end = Time.str_to_datetime(end)

#--------------------------------------------------------------------------
#Checks if users are subsetting geographically
#If so, checks for file, if it doesn't find it, builds subsetted dataframe
#If no, just checks for file, if it doesn't find it, builds dataframed
#Creates suffix that will be in the name of all files created by this run
#--------------------------------------------------------------------------
#calls this if user inputs region based on lat/lon
if ctrl.input_loc == True:
	data_name = 'loc_' +  str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_'+str(ctrl.LCOlat)+'_'+str(ctrl.UCOlat)+'_'+str(ctrl.LCOlon)+'_'+str(ctrl.UCOlon)+'.csv'
	if not os.path.exists(data_name):
        	loc_dataframe(ctrl.LCOlat,ctrl.UCOlat,ctrl.LCOlon,ctrl.UCOlon)
	suffix = '_'+str(ctrl.lead_time)+'hr_lead_loc_subset_'+str(random.randint(1,50))

#calls this if user specifies saved region
elif ctrl.region == True:
	if ctrl.region_name == 'CONUS':
                data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_25_47_70_125.csv'
                if not os.path.exists(data_name):
                        loc_dataframe(25,47,70,125)
                suffix = '_'+str(ctrl.lead_time)+'hr_lead_CONUS_'+str(random.randint(1,50))
	if ctrl.region_name == 'SE':
		data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_-90_35_-180_100.csv'
		if not os.path.exists(data_name):
			loc_dataframe(-90,35,-180,100)
		suffix = '_'+str(ctrl.lead_time)+'hr_lead_SE_'+str(random.randint(1,50))
	if ctrl.region_name == 'SW':
                data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_-90_35_100_180.csv'
                if not os.path.exists(data_name):
                        loc_dataframe(-90,35,100,180)
        	suffix = '_'+str(ctrl.lead_time)+'hr_lead_SW_'+str(random.randint(1,50))
	if ctrl.region_name == 'NE':
                data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_35_50_-180_100.csv'
                if not os.path.exists(data_name):
                        loc_dataframe(35,50,-180,100)
                suffix = '_'+str(ctrl.lead_time)+'hr_lead_NE_'+str(random.randint(1,50))
	if ctrl.region_name == 'NW':
                data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_35_50_100_180.csv'
                if not os.path.exists(data_name):
                        loc_dataframe(35,50,100,180)
                suffix = '_'+str(ctrl.lead_time)+'hr_lead_NW_'+str(random.randint(1,50))
	if ctrl.region_name == 'FN':
                data_name = 'loc_' + str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time)+'hrs_50_90_-180_180.csv'
                if not os.path.exists(data_name):
                        loc_dataframe(50,90,-180,180)
                suffix = '_'+str(ctrl.lead_time)+'hr_lead_FN_'+str(random.randint(1,50))

else:
	data_name = str(start)[0:4]+str(start)[5:7]+str(start)[8:10]+str(start)[11:13] + '_' + str(end)[0:4]+str(end)[5:7]+str(end)[8:10]+str(end)[11:13] + '_' + str(ctrl.lead_time) + 'hrs.csv'
	if not os.path.exists(data_name):
        	dataframe()
	suffix = '_'+str(ctrl.lead_time)+'hr_lead_'+str(random.randint(1,50))

data = pd.read_csv(data_name,delimiter =',',index_col=0)

def scatter(data,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#creates scatterplot of given variables
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
	plt.clf()
	data = data[pd.notnull(data[x])]
	data = data[pd.notnull(data[y])]
	plt.scatter(data[x],data[y])
	plt.xlabel(x)
	plt.ylabel(y)
	if show == True:
		plt.show()
	if save == True:
		plt.savefig('scatter_'+x+'_'+y+suffix+'.png')


def corr_matrix(data,variables,names = [],show=False,save=True):
	#--------------------------------------------------------------------------
	#creates a diagonal correlation matrix using given variables
	#uses inputted names for axis if given
	#--------------------------------------------------------------------------
        plt.clf()
	arr = data.loc[:,variables]
        if names != []:
                arr.columns=names
        corr = arr.corr()
        mask = np.zeros_like(corr,dtype=np.bool)
        mask[np.triu_indices_from(mask)]=True
        sns.heatmap(corr,mask=mask,annot=True)
        plt.yticks(va='center')
        if show == True:
                plt.show()
        if save == True:
                plt.savefig('diag_corr_matrix'+suffix+'.png')


def scatter_matrix(data,variables,show=False,save=True):
	#--------------------------------------------------------------------------
	#creates matrix of scatterplots for all combinations of variables
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
	plt.clf()
	arr = data.loc[:,variables]
        arr = arr.dropna()
        sns.pairplot(arr,plot_kws=dict(linewidth=0))
	if show == True:
		plt.show()
	if save == True:
		plt.savefig('scatter_matrix'+suffix+'.png')


def corr_table(data,variables):
	#--------------------------------------------------------------------------
	#saves correlation values to csv
	#--------------------------------------------------------------------------
	arr = data.loc[:,variables]
	arr.corr().to_csv('correlation'+suffix+'.csv')


def line_plot(data,stations,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#line plot of two variables at given stations
	#--------------------------------------------------------------------------
        plt.clf()
	stat = data.loc[data['Station'].isin(stations)]
        sns.lineplot(x=x,y=y,hue='Station',data = stat)
        if show == True:
                plt.show()
        if save == True:
                plt.savefig('line_plot_'+x+'_'+y+suffix+'.png')

def time_series(data,stations,var,show=False,save=True):
	#--------------------------------------------------------------------------
	#time series of variable at given stations
	#--------------------------------------------------------------------------
	plt.clf()
        stat = data.loc[data['Station'].isin(stations)]
        sns.lineplot(x='Time',y=var,hue='Station',data = stat)
        plt.xticks([stat['Time'].iloc[0], stat['Time'].iloc[-1]], visible=True, rotation="horizontal")
        if show == True:
                plt.show()
        if save == True:
                plt.savefig('time_series_'+var+suffix+'.png')

def time_scatter(data,x,y,time1,time2,show=False,save=True):
	#--------------------------------------------------------------------------
	#overlaid scatterplot of two time periods
	#removes rows with no data
	#--------------------------------------------------------------------------
        plt.clf()
	data = data[pd.notnull(data[x])]
        data = data[pd.notnull(data[y])]
        dates = data.set_index(['Time'])
        range1 = dates.loc[time1[0]:time1[1]]
        range2 = dates.loc[time2[0]:time2[1]]
        plot1  = plt.scatter(range1[x],range1[y], color='C4')
        plot2  = plt.scatter(range2[x],range2[y], color='C9')
        plt.legend((plot1,plot2),(time1[0][:-5]+'-'+time1[1][:-5],time2[0][:-5]+'-'+time2[1][:-5]),scatterpoints=1,fontsize=8)
        plt.xlabel(x)
        plt.ylabel(y)
        if show == True:
                plt.show()
        if save == True:
                plt.savefig('time_scatter_'+x+'_'+y+suffix+'.png')


def violin_plot(data,stations,var,show=False,save=True):
	#--------------------------------------------------------------------------
	#side-by-side violinplots of a variable at given stations
	#--------------------------------------------------------------------------
	plt.clf()
	stat = data.loc[data['Station'].isin(stations)]
	sns.violinplot(x='Station',y=var,data = stat)
	if show == True:
                plt.show()
        if save == True:
                plt.savefig('violin_plot_'+var+suffix+'.png')


def split_violin(data,stations,var1,var2,var_type,show=False,save=True):
	#--------------------------------------------------------------------------
	#side-by-side violinplots of given stations comparing two variables
	#of the same type
	#--------------------------------------------------------------------------
        plt.clf()
        stat1 = data.loc[data['Station'].isin(stations),['Station',var1]]
        stat2 = data.loc[data['Station'].isin(stations),['Station',var2]]
        stat1 = stat1.rename(columns = {var1:var_type})
        stat2 = stat2.rename(columns = {var2:var_type})
        label_1 = [var1]*len(stat1)
        label_2 = [var2]*len(stat2)
        stat1 = stat1.assign(Variable = label_1)
        stat2 = stat2.assign(Variable = label_2)
        stat = pd.concat([stat1,stat2])
        sns.violinplot(x='Station',y=var_type,hue = 'Variable',split=True,inner = 'quart',palette = ['C4','C9'],data = stat)
        if show == True:
                plt.show()
        if save == True:
                plt.savefig('split_violin_'+var_type+suffix+'.png')


def joint_plot(data,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#scatterplot of given variables with histogram of each plot on the edges
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
        plt.clf()
	data = data[pd.notnull(data[x])]
        data = data[pd.notnull(data[y])]
        j=sns.jointplot(x=x,y=y,data=data)
        if show == True:
                plt.show()
        if save == True:
                j.savefig('joint_plot_'+x+'_'+y+suffix+'.png')


def joint_reg_plot(data,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#scatterplot of given variables with histogram of each plot on the edges
	#includes line of best fit and approximate distribution curves
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
        plt.clf()
	data = data[pd.notnull(data[x])]
        data = data[pd.notnull(data[y])]
       	j=sns.jointplot(x=x,y=y,data=data,kind='reg')
        if show == True:
                plt.show()
        if save == True:
                j.savefig('joint_reg_plot_'+x+'_'+y+suffix+'.png')


def hexbin_distribution(data,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#hexbin density plot of variables with histograms on edges
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
	plt.clf()
        data = data[pd.notnull(data[x])]
        data = data[pd.notnull(data[y])]
        j=sns.jointplot(x=x,y=y,data=data,kind='hex')
        if show == True:
                plt.show()
        if save == True:
                j.savefig('hexbin_distribution_plot_'+x+'_'+y+suffix+'.png')


def density_plot(data,x,y,show=False,save=True):
	#--------------------------------------------------------------------------
	#contour density plot of given variables
	#removes rows with no predictand data
	#--------------------------------------------------------------------------
        plt.clf()
        data = data[pd.notnull(data[x])]
        data = data[pd.notnull(data[y])]
        sns.kdeplot(data[x],data[y],shade=True, shade_lowest=False)
	if show == True:
                plt.show()
        if save == True:
                plt.savefig('density_plot_'+x+'_'+y+suffix+'.png')

#--------------------------------------------------------------------------
#calls functions based on control file
#--------------------------------------------------------------------------
if ctrl.scatter == True:
	scatter(data,ctrl.scatter_x,ctrl.scatter_y,ctrl.show,ctrl.save)

if ctrl.corr_matrix == True:
	corr_matrix(data,ctrl.corr_matrix_vars,ctrl.corr_matrix_names,ctrl.show,ctrl.save)

if ctrl.corr_table == True:
	corr_table(data,ctrl.corr_table_vars)

if ctrl.all_corr == True:
	corr_matrix(data,ctrl.corr_vars,ctrl.corr_names,ctrl.show,ctrl.save)
	scatter_matrix(data,ctrl.corr_vars,ctrl.show,ctrl.save)	
	corr_table(data,ctrl.corr_vars)	

if ctrl.line_plot == True:
	line_plot(data,ctrl.line_stations,ctrl.line_x,ctrl.line_y,ctrl.show,ctrl.save)

if ctrl.time_series == True:
	time_series(data,ctrl.time_stations,ctrl.time_var,ctrl.show,ctrl.save)

if ctrl.time_scatter == True:
	time_scatter(data,ctrl.time_scatter_x,ctrl.time_scatter_y,ctrl.time_scatter_range1,ctrl.time_scatter_range2,ctrl.show,ctrl.save)

if ctrl.violin == True:
	violin_plot(data,ctrl.violin_stations,ctrl.violin_var,ctrl.show,ctrl.save)

if ctrl.split_violin == True:
	split_violin(data,ctrl.split_violin_stations,ctrl.split_violin_var1,ctrl.split_violin_var2,ctrl.split_violin_var_type,ctrl.show,ctrl.save)

if ctrl.joint == True:
	joint_plot(data,ctrl.joint_x,ctrl.joint_y,ctrl.show,ctrl.save)

if ctrl.joint_reg == True:
	joint_reg_plot(data,ctrl.joint_reg_x,ctrl.joint_reg_y,ctrl.show,ctrl.save)

if ctrl.hexbin == True:
        hexbin_distribution(data,ctrl.hexbin_x,ctrl.hexbin_y,ctrl.show,ctrl.save)

if ctrl.density == True:
        density_plot(data,ctrl.density_x,ctrl.density_y,ctrl.show,ctrl.save)

#needs to be last, otherwise messes with the size of the other plots
if ctrl.scatter_matrix == True:
        scatter_matrix(data,ctrl.scatt_matrix_vars,ctrl.show,ctrl.save)

