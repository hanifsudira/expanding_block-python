# -*- coding: utf-8 -*-
"""
Created on Sat May  7 18:20:55 2016

@author: efron
"""

import numpy as np
from block_class import Block, ExpandingBlockInit
from scipy.stats.distributions import chi2  

def process_bucket(bucket:list[Block], init:ExpandingBlockInit):

    # subfunctions
    def find_overlap(bucket:list[Block]) -> np.ndarray[bool]:
        ''' 
        calculate whether blocks are pulled from overlapping
        regions of the image '''
        row = [block.row for block in bucket]
        col = [block.col for block in bucket]       

        # broadcast to an len(bucket) by len(bucket) array    
        rowDistance = np.abs(row - np.reshape(row, (-1, 1)))
        colDistance = np.abs(col - np.reshape(col, (-1, 1)))
        
        rowOverlap = rowDistance < init.blockSize
        colOverlap = colDistance < init.blockSize

        return np.logical_or(rowOverlap, colOverlap)
        
    def calculate_testStatistic(subBlocks:  np.ndarray[float]
            ) -> np.ndarray[float]:
        ''' calculate the test statistic of block-to-block similarity: 
        for each ordered pair subBlocki, subBlockj. this is 
        sum(pixeli-pixelj)**2 / (.5*variancei+vareiancej* size(subBlock))'''
        testStatistic = np.zeros((len(subBlocks), len(subBlocks)))
        variance = [np.var(block) for block in subBlocks]
        
        for index, subBlock in enumerate(subBlocks):
            pixel_diff = np.sum((subBlock - subBlocks)**2, axis=(1, 2))
            sigmaSq = (variance[index] + variance) / 2.
            
        try:
            testStatistic[index] = pixel_diff / (sigmaSq*subSize)
        except ZeroDivisionError:
            print('''Zero division error! Filtering of low-variance blocks 
            is not working. Setting testStatistic to 0.''')
            testStatistic[index] = 0
            
        return testStatistic
    
        


    
    def find_connection(testStatistic:np.ndarray[float], 
                        overlap:np.ndarray[bool]) -> np.ndarray[bool]:  
        '''calculate whether blocks are too similar to have occured by chance
        blocks are "connected" if they occur by chance < 1% of the time and
        do not overlap.'''
        testStatistic = calculate_testStatistic(bucket)        
        pValThreshold = chi2.ppf(.01, (subSize**2))
        tooSimilar = testStatistic < pValThreshold

        connection = np.ones_like(tooSimilar)
        connection = np.logical_xor(connection,
            np.logical_or(overlap, np.logical_not(tooSimilar)))
        
        return connection
    
    """
    process_bucket body
    """
    
   
    subSize = 1
    while subSize < init.blockSize:
        if len(bucket)*init.blockSize < init.minArea:
            return []
        # expanding block: we start with a 2x2 subblock of the image,
        # test for similarity to other 2x2 subblocks,
        # then continue with 4x4, etc. until we hit blockSize
        subSize = min(subSize << 1, init.blockSize)
        subBlocks = [1.*block.pixel[0:subSize, 0:subSize] for block in bucket]
        connection = find_connection(
            testStatistic = calculate_testStatistic(subBlocks),
            overlap = find_overlap(bucket) )
        connection = np.any(connection, axis=0)
        
        # isolated blocks (i.e, connection == False) are removed from bucket
        bucket = [bucket[n] for n in range(len(bucket)) if connection[n]]
        
        # early exit if area of remaining blocks is too small
        if len(bucket)*init.blockSize < init.minArea:
            return []
    # return surviving (i.e, possibly fradulent blocks)
    return bucket