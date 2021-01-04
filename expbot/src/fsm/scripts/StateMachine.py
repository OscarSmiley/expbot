#!bin/bash/python

##################### Overview ######################
#   Contains a Preprocessor and current state and Postprocessor instances
#   Compairs the current state and the imput language input using a transition algorithm (Contained in the state object)
#   Decides to remain in the current state or transition to a new one
#   the post-transition state object then issues control arguments to the Postprocessor that publishes messages


#Ros
import rospy
from std_msgs.msg import String
#System
import sys
import time
#State Scripts
#Add ./stateScripts to the python path as an absolute filepath
#   sys.path[0] current directory at runtime
#   appends /stateScripts so sys.path[1] = ./stateScripts
sys.path.insert(1, sys.path[0] + '/stateScripts')
print(sys.path[1])
from startState import startState               #import the various python statescripts
#Machine Objects
from Preprocessor import Preprocessor
from History import History                     #About half-done as of the moment
#from Postprocessor import Postprocessor        #haven't made this thing yet
Noisy = True                                   #kinda like ifdef DEBUG

class StateMachine:
    def __init__(self, extPreProcessor = None, extPostProcessor = None):
        STACKSIZE = 10                          #could be much larger for actual use
        self.Continue = "Good"

        ## create machine objects ##
        #outProcessor = Postprocessor()         #default recieve/publish objects
        self.inProcessor = Preprocessor()
        self.currentState = startState()        #default state
        self.inputVector = {}                   #fsm input language
        self.outputVector = {}                  #fsm output language
        self.pushDownHistory = History(STACKSIZE)

        ## check in processor ##
        if(extPreProcessor != None):           #replace the pre-processor object with a test pre-processor if it is provided
            self.inProcessor = extPreProcessor
        if(extPostProcessor != None):           #replace the pre-processor object with a test pre-processor if it is provided
            self.outProcessor = extPostProcessor

        ## start ros node ##
        self.fsm_debugpub = rospy.Publisher('fsm_debugpub', String, queue_size=10)

    def startup(self):
        #gives preprocessor time to load as full a dictionary as possible before runstates
        #could be as simple as this and tune it in
        rospy.sleep(1)
        print("startup complete")
        return(True)
        #otherwise do some sort of slow polling with __is_full or something similar


    def runStates(self):
        cycleCount = 0
        rate = rospy.Rate(10)
        while(self.Continue == "Good" and not rospy.is_shutdown()):
            time_str = "runstates at %s" % rospy.get_time()
            rospy.loginfo(time_str)
            self.fsm_debugpub.publish(time_str)
            #run loop while the system is good
            #while the system is good, get input from the preprocessor, update the current state, and generate output
            self.inputVector = self.inProcessor.getInputVector()
            self.currentState = self.currentState.getNext(self.inputVector, self.pushDownHistory)
            self.outputVector = self.currentState.generateRequest()
            #outProcessor.generateMessages(outputVector)        #not done yet
            self.Continue = self.outputVector["systemStatus"]   #check to see if the system is still good in the output vector
            if(Noisy):      #useful debuging printouts
                print(">> Cycle: ", cycleCount)
                print("StateMachine input:", self.inputVector)
                print("StateMachine output:", self.outputVector)
            cycleCount += 1
            rate.sleep()
        #Return the reason why the system is not good
        if(self.outputVector == "End"):
            return "Mission_Complete"
        if(self.outputVector == "Non_fatal"):
            return "Restart"
        else:
            return "Fatal"
