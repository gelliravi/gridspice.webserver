import os, sys, subprocess, re, shutil, server, SimulationFactory
from posixpath import  curdir, sep, pardir, join
class Simulation(object):
    """ Wrapper class for GridSpice simulations """
    def __init__( self, simulationDirectory, simulationId, xmlData ):
        self.simulationDirectory = simulationDirectory
        self.simulationId = simulationId
        self.resultsDirectory =  simulationDirectory + '/results'
        self.schematicPath = self.resultsDirectory + '/schematic'
        self.dataFilePath = self.resultsDirectory + '/dataFile'
        self.glmDirectory = simulationDirectory + '/glm'
        self.glmFile = self.glmDirectory + '/model.glm'
        self.lockFile = self.glmDirectory +'/complete'
        self.logFile = self.simulationDirectory + '/output.log'
        self.errFile = self.simulationDirectory + '/error.log'
        self.serverLocation = 'http://prodfe1.gridspice.org/gridspice.webserver'
        #Set valid to false,  we will set it http://127.0.0.1:56174/ImageViewer.html?gwt.codesvr=127.0.0.1:56171
        #to true at the end of init
        self.valid = False
        
        # If we are starting the simulation, make sure to clear our directory
        if os.path.exists( self.simulationDirectory ):
            shutil.rmtree( self.simulationDirectory )
        os.mkdir( simulationDirectory )
        os.mkdir( self.resultsDirectory )
        os.mkdir( self.glmDirectory )
        self.child_pid = os.fork()
        
        self.terminated = False
        self.parseXML(xmlData)


        ## Fork a new process to run the simulation, but store the
        ## child's pid

        print xmlData
        if self.child_pid == 0:
            #SimulationFactory.closeSockets()
            self.output = open( self.logFile, 'w+' )
            self.error = open( self.errFile, 'w+' )
            for i in range(len(self.fileIds)):
                fileURL = self.serverPath+"gsDownloadService?fileId="+self.fileIds[i]
                downloadDir = self.dataFilePath+"-"+self.fileNames[i]
                print "DOWNLOADING FILE: %s to %s" % (fileURL, downloadDir)
                curlCmd = 'curl -o %s \'%s\' --connect-timeout 60' % (downloadDir, fileURL)
                print "CURL CMD: %s" % curlCmd
                os.system(curlCmd)
            for model in self.models:
                modelURL = self.serverPath+"gsDownloadService?schematicId="+model
                print "DOWNLOADING MODEL: %s" % modelURL
                downloadDir = "%s%s.glm" % (self.schematicPath,model)
                curlCmd = 'curl -o %s \'%s\' --connect-timeout 60' % (downloadDir, modelURL)
                print "CURL CMD: %s" % curlCmd
                os.system(curlCmd)

            print "CREATING LOCK FILE: %s"%self.lockFile
            file = open("%s"%self.lockFile,'w+')
            file.close()
            firstSchematic = "%s%s.glm" % (self.schematicPath,self.models[0])


            simulationProc = subprocess.Popen( ['/usr/lib/gridlabd/gridlabd.bin', firstSchematic], \
                       cwd=self.resultsDirectory, stdout=self.output.fileno(),\
                       stderr=self.error.fileno() )
            simulationProc.wait()
            os._exit(os.EX_OK)
        self.valid = True
        

    def parseXML( self, xmlData ):
        import elementtree.ElementTree as ET
        print "PARSING XML %s"%xmlData
        doc = ET.fromstring(xmlData)
        self.serverPath = doc.attrib['serverPath']
        self.fileNames=[]
        self.fileIds=[]
        self.models=[]
        allFiles = doc.find('files')
        for file in list(allFiles):
            self.fileIds.append(file.attrib['id'])
            self.fileNames.append(file.attrib['fileName'])
        allModels = doc.find('models')
        for model in list(allModels):
            self.models.append(model.attrib['id'])


        
    def name(self):
        return str(self.simulationId)

    # Determine if the simulation actually started
    def getValid(self):
        # If the process is still running we will assume its valid
        if not self.getTerminated():
            return True

        lines = os.popen("cat "+self.errFile)
        # If there is an ERROR in the output, the simulation failed
        for line in lines:
            if 'ERROR' in line or 'FATAL' in line:
                print 'failing on line: %s'%line
                return False
            else:
                print 'FATAL or ERROR not contained in "%s"'%line
        print 'PROCESS IS VALID: %s'%lines
        return True
    # This function determines if the simulation process has terminated
    def getTerminated(self):
        # if the simulation is null, we probably already waited on the
        # zombie process
        print "CHECKONG ON CHILD PID %s"%self.child_pid
        if self.terminated:
            return True
        
        pid,status = os.waitpid(self.child_pid, os.WNOHANG)
        if status == 0 and pid==0:
            return False


        print "PROCESS STATUS: %d, %d"%(status, pid)
        self.terminated = True
        print "Process still alive %s %s"% (pid,status)
        #exitCode = self.gridsimulation.poll()
        #if exitCode is not None:
            # If the simulation has completed, wait on the pid to free
            # the zombie process
        #    self.gridsimulation.wait()
        #    self.gridsimulation = []
        #    return True
        return True

    # Returns a 2-line response.  The first line is either 'COMPLETED', 'FAILED', or 'IN PROGRESS'
    # The second line is either the timestamp, or N/A
    def getProgress(self):
        msg = ""
        if not self.glmReceived():
            msg = msg+ 'GENERATING GLM FILE,'
        elif self.getTerminated() and self.getValid():
            msg = msg+ 'COMPLETED,'
        elif self.getValid() and not self.getSimulationTime():
            msg = msg + "SIMULATION INITIALIZING"
        elif self.getValid():
            msg = msg + "SIMULATION IN PROGRESS,"
            msg += self.getSimulationTime()
        else:
            msg = msg + 'FAILED,'

        print "response: %s"%msg
        return msg

    def getSimulationTime( self ):
        lines = os.popen("tac "+self.logFile)
        for line in lines:
            match = re.search('\AProcessing \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',line)
            if match:
                print 'found match'
                time = match.group(0)[10:]
                if( time ):
                    return time
                
            else:
                print "unmatch"+line
        return ""
   
    def glmReceived(self):
        if( os.path.exists(self.lockFile)):
            print "GLM RECEIVED:%s"%self.lockFile
            return True
        return False


    def relpath(path, start=curdir):


        if not path:
            raise ValueError("no path specified")
        start_list = posixpath.abspath(start).split(sep)
        path_list = posixpath.abspath(path).split(sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(posixpath.commonprefix([start_list, path_list]))
        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
                                            
    def getResults(self):
        print 'getting results'
        dirElems = os.listdir(self.resultsDirectory)
        msg = ""
        for i in range(len(dirElems)):
            print msg
            msg = msg + '%s'% dirElems[i]
            # Add a comma if its not the last element
            if not i == len(dirElems) -1 :
                msg = msg + '\n'
        return msg
        
