import shutil, Simulation, os


simulationRootDirectory = '%s/simulation' % os.getcwd()

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
    simulation = loadSimulation( simulationId )
    if( simulation ):
        return simulation.getProgress()
    else:
        return "CANNOT FIND SIMULATION (NO PROGRESS)"
    
def getSimulationResults( simulationId ):
    simulation = loadSimulation( simulationId )
    if( simulation ):
        return simulation.getResults()
    else:
        return "CANNOT FIND SIMULATION (NO PROGRESS)"
    

# The server should not run more than 16 simulations at once
# so we make sure that less than 16 are available.
def activeSimulationCount():
    return 5

def newSimulation( simulationId, xmlData ):
    global simulationRootDirectory
    #nextSimulationId = nextSimulationId + 1
    #simId = nextSimulationId
    if( activeSimulationCount() > 16 ):
        return 'Error: Server Busy.  Too many simulations running'
    simulationDirectory = simulationRootDirectory+ "/sim-" + str(simulationId)
    simulation = Simulation.Simulation( simulationDirectory, simulationId )
    simulation.create( xmlData )
    print 'CREATED SIMULATION ID: %s'%simulationId
    return 'SUCCESS'

    
def loadSimulation( simulationId ):
    global simulationRootDirectory
    if( activeSimulationCount() > 16 ):
        return 'Error: Server Busy.  Too many simulations running'
    simulationDirectory = simulationRootDirectory+ "/sim-" + str(simulationId)
    simulation = Simulation.Simulation( simulationDirectory, simulationId )
    if( simulation.load() ):
        return simulation
    else:
        return False
