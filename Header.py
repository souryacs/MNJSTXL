#!/usr/bin/env python

"""
program for species tree estimation
computes following two measures
1) Internode count
2) Excess gene leaf count
"""

import dendropy
from optparse import OptionParser
import math
import time
import os
import numpy
import sys
#import matplotlib.pyplot as plt	# add - debug - sourya

#-------------------------------------------------------------
""" 
this dictionary defines the taxa pair relations
each entry is indexed by two leaves 
"""
TaxaPair_Reln_Dict = dict()

"""
Stores the complete set of input taxa covered in the input gene trees
"""
COMPLETE_INPUT_TAXA_LIST = []

"""
this is the debug level
set for printing the necessary information
"""
DEBUG_LEVEL = 0

#-----------------------------------------------------
"""
******** sourya *******
in the communicated paper to TCBB (Jan 2016)
we have used average of internode count
and the avg(avg, median) of XL measure
we did not use the filtered (mode based average) of XL
"""
"""
In the communicated paper of ACM-BCB 2016
we have used mode based filtered average of the XL measure
"""
"""
these two variables are used to define the mode based average of the XL measure
this was originally not used
we can check two different values of mode percentage: 0.25 and 0.5

Note: After experiments, we have fixed following two values
0.25 and 40
"""
MODE_PERCENT = 0.5	#0.5
MODE_BIN_COUNT = 40

#-----------------------------------------------------
""" 
this class defines the relationship between a pair of taxa
initially the information are obtained from the input gene trees
"""
class Reln_TaxaPair(object):  
	def __init__(self):
		"""
		this is the count of trees supporting (containing) the couplet
		"""
		self.tree_support_count = 0        
		"""
		this list contains the sum of internode counts between this couplet
		computed for all the supporting gene trees
		"""
		self.sum_internode_count = 0
		"""
		this is the excess gene leaf count list for this couplet
		"""
		self.XL_val_list = []
		"""
		this is a variable containing the binned (filtered) average of the XL values
		of very high frequency
		initially the value is set as -1, to signify that the computation is not done
		once the computation (for a couplet) is done, the value is subsequently used and returned
		"""
		self.binned_avg_XL = -1
		self.avg_XL = -1
		self.median_XL = -1

	#-----------------------------------------------
	"""
	this function adds the count of supporting tree containing this particular couplet
	"""
	def _IncrSupportTreeCount(self):
		self.tree_support_count = self.tree_support_count + 1
	
	"""
	this function returns the number of trees supporting the couplet
	"""
	def _GetSupportTreeCount(self):
		return self.tree_support_count        
	
	#-----------------------------------------------
	"""
	inserts the XL measure for the current tree in the XL list
	"""
	def _AddXLVal(self, val):
		self.XL_val_list.append(val)

	"""
	average of the XL values for all the gene trees
	"""
	def _GetAvgXLVal(self):
		if (self.avg_XL == -1):
			self.avg_XL = (sum(self.XL_val_list) * 1.0) / self.tree_support_count
		return self.avg_XL

	"""
	Median of the XL values for all the gene trees
	"""
	def _MedianXLVal(self):
		if (self.median_XL == -1):
			self.median_XL = numpy.median(numpy.array(self.XL_val_list))
		return self.median_XL
	
	"""
	Filtered average of the XL values for all the gene trees
	"""
	def _GetMultiModeXLVal(self, Output_Text_File=None):
		if (self.binned_avg_XL == -1):
			
			Bin_Width = (1.0 / MODE_BIN_COUNT)
			len_list = [0] * MODE_BIN_COUNT
			
			if Output_Text_File is not None:
				fp = open(Output_Text_File, 'a') 
			
			# sort the XL list
			self.XL_val_list.sort()
			
			for j in range(len(self.XL_val_list)):
				curr_xl_val = self.XL_val_list[j]
				bin_idx = int(curr_xl_val / Bin_Width)
				if (bin_idx == MODE_BIN_COUNT):
					bin_idx = bin_idx - 1
				len_list[bin_idx] = len_list[bin_idx] + 1
			
			if Output_Text_File is not None:
				for i in range(MODE_BIN_COUNT):
					fp.write('\n bin idx: ' + str(i) + ' len:  ' + str(len_list[i]))
			
			# this is the maximum length of a particular bin
			# corresponding to max frequency
			max_freq = max(len_list)
			
			if Output_Text_File is not None:
				fp.write('\n Max freq: ' + str(max_freq))
			
			num = 0
			denom = 0
			for i in range(MODE_BIN_COUNT):
				if (len_list[i] >= (MODE_PERCENT * max_freq)):
					list_start_idx = sum(len_list[:i])
					list_end_idx = list_start_idx + len_list[i] - 1
					value_sum = sum(self.XL_val_list[list_start_idx:(list_end_idx+1)])
					num = num + value_sum
					denom = denom + len_list[i]
					if Output_Text_File is not None:
						fp.write('\n Included bin idx: ' + str(i) + ' starting point: ' + str(list_start_idx) \
							+ 'ending point: ' + str(list_end_idx) + ' sum: ' + str(value_sum))
			
			self.binned_avg_XL = (num / denom)
			
			if Output_Text_File is not None:
				fp.write('\n Final binned average XL: ' + str(self.binned_avg_XL))
				fp.close()
			
		return self.binned_avg_XL
	#------------------------------------------
	"""
	insert the internode count for the current input tree supporting this couplet
	"""
	def _AddLevel(self, val):
		self.sum_internode_count = self.sum_internode_count + val

	"""
	average internode count for this couplet
	"""
	def _GetAvgSumLevel(self):
		return (self.sum_internode_count * 1.0) / self.tree_support_count

	# this function prints information for the current couplet
	def _PrintTaxaPairRelnInfo(self, key, out_text_file):
		fp = open(out_text_file, 'a')    
		fp.write('\n\n taxa pair key: ' + str(key) + ' Couplet: (' + COMPLETE_INPUT_TAXA_LIST[key[0]] \
			+ ',' + COMPLETE_INPUT_TAXA_LIST[key[1]] + ')')
		fp.write('\n supporting number of trees: ' + str(self._GetSupportTreeCount()))
		fp.write('\n average internode count: ' + str(self._GetAvgSumLevel()))    
		fp.write('\n average XL: ' + str(self._GetAvgXLVal()))   
		fp.write('\n median XL : ' + str(self._MedianXLVal()))   
		fp.write('\n Mode based filtered average XL: ' + str(self._GetMultiModeXLVal()))   
		fp.close()
			
		## sourya - debug
		#if (key[0] == 'HOM' and key[1] == 'TAR') or (key[0] == 'MYO' and key[1] == 'TUR'):
			#print 'printing the file'
			#print 'current directory: ', os.getcwd()
			
			##fig1 = plt.figure()
			##n1, bins1, patches1 = plt.hist(self.sum_internode_count, 37, normed=0)	#, facecolor='green', alpha=0.75)
			##xlabel_str = 'I_G(' + str(key[0]) + ',' + str(key[1]) + ')'
			##plt.xlabel(xlabel_str)
			##plt.ylabel('Frequency')
			##plt.title('Histogram of the internode count across gene trees for the couplet ' + str(key[0]) + ' and ' + str(key[1]))
			##plt.grid(True)
			##plt.tight_layout()
			##fig1.set_size_inches(10, 6)
			##figname = 'internode_count_' + str(key[0]) + '_' + str(key[1]) + '.jpg'
			##print 'figname: ', figname
			##plt.savefig(figname)
			##plt.clf()	# clear the current figure memory
			##plt.close()	# close the figure window
			

			#fig2 = plt.figure()
			#n2, bins2, patches2 = plt.hist(self.XL_val_list, 37, normed=0, facecolor='green', alpha=0.75)
			#xlabel_str = 'X_G(' + str(key[0]) + ',' + str(key[1]) + ')'
			#plt.xlabel(xlabel_str, fontsize=24)
			#plt.ylabel('Frequency', fontsize=24)
			#title_str = 'Distribution of XL for ' + str(key[0]) + ' and ' + str(key[1])
			#plt.title(title_str, fontsize=24)
			#plt.grid(True)
			#plt.tight_layout()
			#fig2.set_size_inches(10, 6)
			#figname = 'extra_leaf_' + str(key[0]) + '_' + str(key[1]) + '.jpg'
			#print 'figname: ', figname
			#plt.savefig(figname)      
			#plt.clf()	# clear the current figure memory
			#plt.close()	# close the figure window
			
		## end sourya - debug
    
      