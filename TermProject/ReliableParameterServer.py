from copy import deepcopy
from enum import Enum
import networkx as nx
import threading

from numpy import loadtxt
from keras.models import Sequential
from keras.layers import Dense

from Ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload
from MinimumSpanningTree import MSTMessageTypes, LMSTUpdate


GLOBAL_LOCK = threading.Lock()

DATASET_PATH = "DL/credit.csv"
AGGREGATED_OUTPUT_FILE_PATH = "Output/aggregated_accuracies.txt"
OUTPUT_FILE_PATH = "Output/without_aggregated_accuracies.txt"
EPOCH = 5
LAST_TRAINING_ROUND = 40
WEIGHT_AVERAGING = True

class RPSEventTypes(Enum):
    MST_CONSTRUCTED = "minimumspanningtreeconstructed"
    START = "start"
    TRAIN = "train"
    SHARE = "share"

class RPSMessageTypes(Enum):
    START = "start"
    TRAIN = "train"
    SHARE = "share"

class RPSStartMessagePayload(GenericMessagePayload):
    def __init__(self, mst: nx.Graph):
        super().__init__(mst)

class RPSStartMessageHeader(GenericMessageHeader):
    def __init__(self, messagefrom, messageto):
        super().__init__(RPSMessageTypes.START, messagefrom, messageto, nexthop=messageto)

class RPSTrainMessagePayload(GenericMessagePayload):
    def __init__(self, messagepayload=None):
        super().__init__(messagepayload)

class RPSTrainMessageHeader(GenericMessageHeader):
    def __init__(self, messagefrom, messageto):
        super().__init__(RPSMessageTypes.TRAIN, messagefrom, messageto, nexthop=messageto)

class RPSShareMessagePayload(GenericMessagePayload):
    def __init__(self, weights, source):
        super().__init__(weights)
        self.source = source

class RPSShareMessageHeader(GenericMessageHeader):
    def __init__(self, messagefrom, messageto):
        super().__init__(RPSMessageTypes.SHARE, messagefrom, messageto, nexthop=messageto)

class RPSMessage(GenericMessage):
    def __init__(self, messagefrom, messageto, messagetype: RPSMessageTypes, messagepayload=None, source=-1):
        if messagetype == RPSMessageTypes.START:
            super().__init__(header=RPSStartMessageHeader(messagefrom, messageto),
                             payload=RPSStartMessagePayload(messagepayload))
        elif messagetype == RPSMessageTypes.TRAIN:
            super().__init__(header=RPSTrainMessageHeader(messagefrom, messageto),
                             payload=RPSTrainMessagePayload(messagepayload))
        elif messagetype == RPSMessageTypes.SHARE:
            super().__init__(header=RPSShareMessageHeader(messagefrom, messageto),
                             payload=RPSShareMessagePayload(messagepayload, source))

class RPSComponent(ComponentModel):
    dataset = loadtxt(DATASET_PATH, delimiter=',')
    trainingFeatures = dataset[:, 1:]
    trainingLabels = dataset[:, 0]

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        messageType = message.header.messagetype

        if messageType is MSTMessageTypes.LOCAL_MST:
            mstEvent = Event(eventobj.eventsource, RPSEventTypes.MST_CONSTRUCTED, eventobj.eventcontent, eventobj.fromchannel)
            self.send_self(mstEvent)
        elif messageType is RPSMessageTypes.START:
            startEvent = Event(eventobj.eventsource, RPSEventTypes.START, eventobj.eventcontent, eventobj.fromchannel)
            self.send_self(startEvent)
        elif messageType is RPSMessageTypes.SHARE:
            shareEvent = Event(eventobj.eventsource, RPSEventTypes.SHARE, eventobj.eventcontent, eventobj.fromchannel)
            self.send_self(shareEvent)

    def __init__(self, componentid):
        componentname = "RPSComponent"
        super().__init__(componentname, componentid)
        self.eventhandlers[RPSEventTypes.MST_CONSTRUCTED] = self.on_minimum_spanning_tree_constructed
        self.eventhandlers[RPSEventTypes.START] = self.on_start
        self.eventhandlers[RPSEventTypes.TRAIN] = self.on_train
        self.eventhandlers[RPSEventTypes.SHARE] = self.on_share

        self.mst: nx.Graph = None
        self.rpsStarted = False

        self.model: Sequential = None
        self.bestModelInfo = {'bestModelAccuracy': 0.0, 'bestModelTrainingRound': -1, 'bestModelWeights': None}
        self.trainingRound = 0
        self.receivedWeights = {}

    def on_minimum_spanning_tree_constructed(self, eventobj: Event):
        lmstUpdate: LMSTUpdate = eventobj.eventcontent.payload.messagepayload
        mst = lmstUpdate.localMST

        selfStartEventContent = RPSMessage(self.componentinstancenumber, self.componentinstancenumber,
                                           RPSMessageTypes.START, messagepayload=mst)
        selfStartEvent = Event(self, RPSEventTypes.START, selfStartEventContent)
        self.send_self(selfStartEvent)

    def on_start(self, eventobj: Event):
        if not self.rpsStarted:
            self.rpsStarted = True
            # print(f"RPS started from Node {self.componentinstancenumber}!")
            header = eventobj.eventcontent.header
            messagefrom = header.messagefrom
            mst = eventobj.eventcontent.payload.messagepayload
            self.mst = deepcopy(mst)

            for node in self.mst.neighbors(self.componentinstancenumber):
                if node != messagefrom:
                    startEventContent = RPSMessage(self.componentinstancenumber, node, RPSMessageTypes.START,
                                                   messagepayload=self.mst)
                    startEvent = Event(self, EventTypes.MFRT, startEventContent)
                    self.send_down(startEvent)

            trainEventContent = RPSMessage(self.componentinstancenumber, self.componentinstancenumber,
                                           RPSMessageTypes.TRAIN)
            trainEvent = Event(self, RPSEventTypes.TRAIN, trainEventContent)
            self.send_self(trainEvent)

    def on_train(self, eventobj: Event):
        if self.model is None:
            self.model = Sequential()
            self.model.add(Dense(16, input_dim=self.trainingFeatures.shape[1], activation='relu'))
            self.model.add(Dense(12, activation='relu'))
            self.model.add(Dense(8, activation='relu'))
            self.model.add(Dense(1, activation='sigmoid'))
            self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

        if WEIGHT_AVERAGING:
            receivedWeights = self.receivedWeights
            self.receivedWeights.clear()
            weights = self.model.get_weights()
            for i in range(len(weights)):
                for weight in receivedWeights:
                    weights[i] += weight[i]
                weights[i] /= (len(receivedWeights) + 1)
            self.model.set_weights(weights)

        self.model.fit(self.trainingFeatures, self.trainingLabels, epochs=EPOCH, batch_size=10, verbose=0)
        _, accuracy = self.model.evaluate(self.trainingFeatures, self.trainingLabels, verbose=0)
        # print(f"Node {self.componentinstancenumber} - Accuracy = %.2f, Training Round = {self.trainingRound}" % accuracy)
        if accuracy > self.bestModelInfo['bestModelAccuracy']:
            self.bestModelInfo['bestModelWeights'] = self.model.get_weights()
            self.bestModelInfo['bestModelAccuracy'] = accuracy
            self.bestModelInfo['bestModelTrainingRound'] = self.trainingRound

        self.sendWeights(self.model.get_weights(), self.componentinstancenumber)
        self.trainingRound += 1

        if self.trainingRound < LAST_TRAINING_ROUND:
            self.send_self(eventobj)
        else:
            print(f"Node {self.componentinstancenumber} - Finished Model Training with Accuracy = %.2f, "
                  f"Best Accuracy = %.2f ({self.bestModelInfo['bestModelTrainingRound']})"
                  % (accuracy, self.bestModelInfo['bestModelAccuracy']))

            while GLOBAL_LOCK.locked():
                continue
            GLOBAL_LOCK.acquire()
            if WEIGHT_AVERAGING:
                filePath = AGGREGATED_OUTPUT_FILE_PATH
            else:
                filePath = OUTPUT_FILE_PATH
            with open(filePath, 'a+') as f:
                f.write(f"{self.bestModelInfo['bestModelAccuracy']}\n")
                f.close()
            GLOBAL_LOCK.release()

    def on_share(self, eventobj: Event):
        messagefrom = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload
        source = payload.source
        weights = payload.messagepayload

        if source != -1:
            # print(f"Node {self.componentinstancenumber} - Received Weights from {messagefrom} with Source: {source}")
            self.receivedWeights[source] = weights
            self.sendWeights(weights, source, messagefrom)

    def sendWeights(self, weights, source, messagefrom=-1):
        for n in self.mst.neighbors(self.componentinstancenumber):
            if n != messagefrom:
                shareEventContent = RPSMessage(self.componentinstancenumber, n, RPSMessageTypes.SHARE, weights, source)
                shareEvent = Event(self, EventTypes.MFRT, shareEventContent)
                self.send_down(shareEvent)
