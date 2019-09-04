'''
Created on 18 Oct 2018

@author: thomasgumbricht
'''

import urllib.request
from html.parser import HTMLParser
import os
from sys import exit
from shutil import move
import geoimagine.support.karttur_dt as mj_dt
from geoimagine.kartturmain import Composition, LayerCommon, VectorLayer, RasterLayer, TimeSteps
from geoimagine.ancillary import ProcessAncillary
import geoimagine.zipper.explode as zipper


class AncilLayer(LayerCommon):
    '''Class for sentinel tiles'''
    def __init__(self, composition, locusD, datumD, filepath, FN): 
        """The constructor expects an instance of the composition class."""
        LayerCommon.__init__(self)

        self.comp = composition
        
        self.locus = locusD['locus']
        self.locuspath = locusD['path']

        self.path = filepath
        self.FN = FN

        self.datum = lambda: None
        for key, value in datumD.items():
            setattr(self.datum, key, value)
        if self.datum.acqdate:
            self._SetDOY()
            self._SetAcqdateDOY()
        self._SetPath()
        
    def _SetPath(self):
        """Sets the complete path to sentinel tiles"""
        
        self.FP = os.path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locuspath, self.datum.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING FPN contains space %s' %(self.FPN)
            exit(exitstr)
            
class GraceComposition:
    '''
    class for sentinel compositions
    '''
    def __init__(self, compD):  
        for key in compD:
            if '_' in compD[key]:
                exitstr = 'the "%s" parameter can not contain underscore (_): %s ' %(key, compD[key])
                exit(exitstr) 
            setattr(self, key, compD[key])
        if not hasattr(self, 'folder'):
            exitstr = 'All Grace compositions must contain a folder'
            exit(exitstr)
            
class GraceTile(LayerCommon):
    '''Class for sentinel tiles'''
    def __init__(self, composition, locusD, datumD, filepath, FN): 
        """The constructor expects an instance of the composition class."""
        LayerCommon.__init__(self)

        self.comp = composition
        
        self.locus = locusD['locus']
        self.locuspath = locusD['path']

        self.path = filepath
        self.FN = FN

        self.datum = lambda: None
        for key, value in datumD.items():
            setattr(self.datum, key, value)
        if self.datum.acqdate:
            self._SetDOY()
            self._SetAcqdateDOY()
        self._SetPath()
        
    def _SetPath(self):
        """Sets the complete path to sentinel tiles"""
        
        self.FP = os.path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locuspath, self.datum.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING smap FPN contains space %s' %(self.FPN)
            exit(exitstr)

class ProcessGrace:
    'class for grace specific processing'   
    def __init__(self, process, session, verbose):
        self.verbose = verbose
        self.process = process   
        self.session = session         
        #direct to subprocess

        if self.process.proc.processid.lower() == 'organizegrace':
            self._OrganizeGrace()
        elif self.process.proc.processid.lower() == 'fillgracetimegaps':
            self._FillGraceTimeGaps()
        elif self.process.proc.processid.lower() == 'averagegracesolutions':
            self._AverageGraceSolutions()
        
        else:
            exitstr = 'Exiting, processid %(p)s missing in ProcessSmap' %{'p':self.process.proc.processid}
            exit(exitstr)
 
    def _OrganizeGrace(self):
        '''Identifies grace files in given folder and converts to single ancillary layer that is imported
        '''
        for comp in self.process.proc.srcraw.paramsD:
            solutionStr = '.%(s)s.' %{'s':self.process.params.solutionset}
            datadir = self.process.proc.srcraw.paramsD[comp]['datadir']
            self.FP = os.path.join('/Volumes',self.process.srcpath.volume, datadir)
            for FN in os.listdir(self.FP):
                if FN.endswith(self.process.srcpath.hdrfiletype) and solutionStr in FN:
                    if FN.endswith('.gz'):
                        zipFPN = os.path.join(self.FP,FN)
                        dstFPN = os.path.splitext(zipFPN)[0]
                        dstFPNbasic,dstext = os.path.splitext(dstFPN)
                        #This is a gunzip file that must be exploded
                        if not os.path.isfile(dstFPN):
                            print ('    unzipping', zipFPN)
                            print ('    to',dstFPN)

                            zipper.ExplodeGunZip(zipFPN)

                        yyyymmdd =  dstFPN.split('.')[2]
                        #Force the date to represent the first day of the month
                        yyyymmdd = '%(yyyymm)s01' %{'yyyymm':yyyymmdd[0:6]}
                        acqdate = mj_dt.yyyymmddDate(yyyymmdd)

                        #Recreate the compositon
                        key = list(self.process.dstCompD.keys())[0]

                        comp = self.process.dstCompD[key]
                        #Here I reset the filetype, this is dangerous 
                        self.process.proc.srcpathD['hdrfiletype'] = dstext
                        
                        #Set the source file (without extension)
                        self.process.proc.srcraw.paramsD[key]['datafile'] = os.path.split(dstFPNbasic)[1]
                          
                        datumD = {'acqdatestr': yyyymmdd, 'acqdate':acqdate}
                    
                        filepath = lambda: None
                        filepath.volume = self.process.dstpath.volume; filepath.hdrfiletype = 'tif'
                    
                        locusD = {'locus':'global', 'path':'global'}
                        #Create a standard reaster layer
                        bandR = RasterLayer(comp, locusD, datumD, filepath)

                        self.process.dstLayerD['global'] = {}
                        self.process.dstLayerD['global'][yyyymmdd] = {key:bandR}
                        
                        srcrawD = self.process.proc.srcraw.paramsD[key]
                        if self.process.proc.srcpathD['hdrfiletype'][0] == '.':
                            ext = self.process.proc.srcpathD['hdrfiletype']
                        else:
                            ext = '.%s' %(self.process.proc.srcpathD['hdrfiletype'])
                        self.srcFN = '%(fn)s%(e)s' %{'fn':srcrawD['datafile'],'e':ext}            
                        self.srcFP = os.path.join('/Volumes',self.process.proc.srcpathD['volume'], srcrawD['datadir'])
                        self.srcFPN = os.path.join(self.srcFP,self.srcFN)
                        ProcessAncillary(self.process,self.session,True)

    def _FillGraceTimeGaps(self):
        pass