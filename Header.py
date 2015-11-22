#!/usr/bin/env python

"""
program for species tree estimation
computes four criteria - 
1) Level / internode count information
2) Accumulated Rank statistics 
"""

import dendropy
from optparse import OptionParser
#import math
import time
import os
import numpy
import sys
#import matplotlib.pyplot as plt

""" 
this dictionary defines the taxa pair relations
each entry is indexed by two nodes 
"""
TaxaPair_Reln_Dict = dict()

# these variables store the respective parameters of input gene trees
COMPLETE_INPUT_TAXA_LIST = []

# this is the debug level
# set for printing the necessary information
DEBUG_LEVEL = 0

"""
variables depicting the method employed for species tree construction
first two methods use average statistics of the coalescence rank or the internode count
last two methods employ the mode statistics
"""
"""
accumulated internode count with average statistics
plus average of excess gene count measure 
"""
NJSTXL = 1
"""
accumulated internode count with average statistics
plus minimum (median, average) of excess gene count measure 
"""
MNJSTXL = 2

# variables used to denote whether we use traditional NJ method
# or use a variant of it, namely the agglomerative clustering
TRADITIONAL_NJ = 1
AGGLO_CLUST = 2

##-----------------------------------------------------
""" 
this class defines the connectivity relationship between a pair of taxa
initially the information are obtained from the input source trees
"""
class Reln_TaxaPair(object):  
	def __init__(self):
		# this is the count of trees for which the couplet is supported
		self.tree_support_count = 0        
		# this list contains the number of levels (tree internodees) between individual couplets
		# computed for all the gene trees
		self.level_info_list = []
		# this is the extra lineage count list for this couplet
		self.XL_val_list = []
		
	# this function adds the count of tree according to the support of 
	# corresponding couplet in the input tree
	def _IncrSupportTreeCount(self):
		self.tree_support_count = self.tree_support_count + 1
					
	# this function returns the number of trees supporting the couplet
	def _GetSupportTreeCount(self):
		return self.tree_support_count        
				
	def _AddXLVal(self, val):
		self.XL_val_list.append(val)

	def _GetAvgXLVal(self):
		return (sum(self.XL_val_list) * 1.0) / self.tree_support_count
	
	def _MedianXLVal(self):
		return numpy.median(numpy.array(self.XL_val_list))
	
	#def _MinAvgMedianXLVal(self):
		#return min(self._MedianXLVal(), self._GetAvgXLVal())

	#def _MaxAvgMedianXLVal(self):
		#return max(self._MedianXLVal(), self._GetAvgXLVal())
					
	#def _GetMultiModeXLVal(self):
		#candidate_score_sum = 0
		#candidate_freq_sum = 0
		#curr_arr = numpy.array(self.XL_val_list)
		## returns the counts of individual elements
		## array size: max_elem + 1
		#counts = numpy.bincount(curr_arr)
		## remove the zero values 
		#values = numpy.nonzero(counts)[0]
		## mode value and corresponding frequency
		#mode_val = numpy.argmax(counts)
		#mode_count = numpy.max(counts)
		## check for the values having frequency at least half of the maximum frequency
		#for v in values:
			#if (counts[v] >= 0.5 * mode_count):
				#candidate_score_sum = candidate_score_sum + (v * counts[v])
				#candidate_freq_sum = candidate_freq_sum + counts[v]
		#return (candidate_score_sum * 1.0) / candidate_freq_sum        
				
	def _AddLevel(self, val):
		self.level_info_list.append(val)

	def _GetAvgSumLevel(self):
		return (sum(self.level_info_list) * 1.0) / self.tree_support_count
					
	#def _GetMultiModeSumLevel(self):
		#candidate_score_sum = 0
		#candidate_freq_sum = 0
		#curr_arr = numpy.array(self.level_info_list)
		## returns the counts of individual elements
		## array size: max_elem + 1
		#counts = numpy.bincount(curr_arr)
		## remove the zero values 
		#values = numpy.nonzero(counts)[0]
		## mode value and corresponding frequency
		#mode_val = numpy.argmax(counts)
		#mode_count = numpy.max(counts)
		## check for the values having frequency at least half of the maximum frequency
		#for v in values:
			#if (counts[v] >= 0.5 * mode_count):
				#candidate_score_sum = candidate_score_sum + (v * counts[v])
				#candidate_freq_sum = candidate_freq_sum + counts[v]
		#return (candidate_score_sum * 1.0) / candidate_freq_sum
																		
	# this function prints information for the current couplet
	def _PrintTaxaPairRelnInfo(self, key, out_text_file, METHOD_USED):
		fp = open(out_text_file, 'a')    
		fp.write('\n taxa pair key: ' + str(key))
		fp.write('\n supporting number of trees: ' + str(self._GetSupportTreeCount()))
		fp.write('\n *** average sum of internode count : ' + str(self._GetAvgSumLevel()))    
		fp.write('\n *** average XL val : ' + str(self._GetAvgXLVal()))   
		fp.write('\n *** median XL val : ' + str(self._MedianXLVal()))   
		fp.write('\n *** 50 percent mode XL val : ' + str(self._GetMultiModeXLVal()))   
		fp.close()
			
		## sourya - debug
		#if (key[0] == 'HOM' and key[1] == 'TAR') or (key[0] == 'MYO' and key[1] == 'TUR'):
		#fig1 = plt.figure()
		#n1, bins1, patches1 = plt.hist(self.level_info_list, 37, normed=0)	#, facecolor='green', alpha=0.75)
		#xlabel_str = 'I_G(' + str(key[0]) + ',' + str(key[1]) + ')'
		#plt.xlabel(xlabel_str)
		#plt.ylabel('Frequency')
		#plt.title('Histogram of the internode count across gene trees for the couplet ' + str(key[0]) + ' and ' + str(key[1]))
		#plt.grid(True)
		#plt.tight_layout()
		#fig1.set_size_inches(10, 6)
		#figname = 'internode_count_' + str(key[0]) + '_' + str(key[1]) + '.jpg'
		#print 'figname: ', figname
		#plt.savefig(figname)

		#fig2 = plt.figure()
		#n2, bins2, patches2 = plt.hist(self.XL_val_list, 37, normed=0)	#, facecolor='green', alpha=0.75)
		#xlabel_str = 'X_G(' + str(key[0]) + ',' + str(key[1]) + ')'
		#plt.xlabel(xlabel_str)
		#plt.ylabel('Frequency')
		#plt.title('Histogram of the extra lineage count across gene trees for the couplet ' + str(key[0]) + ' and ' + str(key[1]))
		#plt.grid(True)
		#plt.tight_layout()
		#fig2.set_size_inches(10, 6)
		#figname = 'extra_lineage_' + str(key[0]) + '_' + str(key[1]) + '.jpg'
		#print 'figname: ', figname
		#plt.savefig(figname)      
		## end sourya - debug
			
		
    
      