import shutil, Simulation, os


simulationRootDirectory = '%s/simulation' % os.getcwd()
allSimulations = {}
print "init Simulation Factory"
#nextSimulationId = 0
# Remove old simulations
#try:
    #print "flushing directory: %s" % simulationRootDirectory
    #shutil.rmtree( simulationRootDirectory )
    #os.mkdir( simulationRootDirectory )
#except Exception, e:
#    print "Could not flush simulation directory %s" % e
#    pass

savedSockets = []
def setSocket(s):
    savedSockets.append(s)

def closeSockets():
    for socket in savedSockets:
        socket.socket.close()
# Iterate through the simulation directory and find an unused id
def getUnusedSimulationId():
    maxSimulationId = 0
    dirElems = os.listdir( simulationRootDirectory )
    print dirElems
    for elem in dirElems:
        try:
            currentSimulationId = int(elem.split("-")[1])
            if (currentSimulationId > maxSimulationId):
                maxSimulationId = currentSimulationId
        except:
            print 'corrupted simulation directory'
            return maxSimulationId + 1
        
def getSimulationProgress( simulationId ):
    if( not simulationId in allSimulations ):
        print allSimulations
        return 'unknown simulation id: %s'%simulationId
    return allSimulations[simulationId].getProgress()

def getSimulationResults( simulationId ):
    if( not simulationId in allSimulations ):
        print allSimulations
        return 'unknown simulation id: %s'%simulationId
    return allSimulations[simulationId].getResults()

# The server should not run more than 16 simulations at once
# so we make sure that less than 16 are available.
def activeSimulationCount():
    activeSimulations = 0;
    for simulationId in allSimulations.keys():
        if( not allSimulations[simulationId].getTerminated() ):
            activeSimulations = activeSimulations + 1
    return activeSimulations

def newSimulation( simulationId, xmlData ):
    global simulationRootDirectory
    #nextSimulationId = nextSimulationId + 1
    #simId = nextSimulationId
    if( activeSimulationCount() > 16 ):
        return 'Error: Server Busy.  Too many simulations running'
    if( simulationId in allSimulations and not allSimulations[simulationId].getTerminated() ):
        return 'Error: Simulation already started'
    simulationDirectory = simulationRootDirectory+ "/sim-" + str(simulationId)
    simulation = Simulation.Simulation( simulationDirectory, simulationId, xmlData )
    allSimulations[simulationId] = simulation
    print 'CREATED SIMULATION ID: %s'%simulationId
    return 'SUCCESS'

def beginSimulation( simulationId ):
    allSimulations[simulationId].startSimulationProess()
    return 'SUCCESS'

def addModelData( simulationId, file, fileName ):
    if simulationId in allSimulations:
        allSimulations[simulationId].addFile( fileName, file )
        return "SUCCESS"
    else:
        return "CANNOT ADD %s, NO SIMULATION FOR SIMULATION ID %s"%(fileName, simulationId)
    
