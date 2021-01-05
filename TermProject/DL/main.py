from numpy import loadtxt
from keras.models import Sequential, clone_model
from keras.layers import Dense
from copy import deepcopy

E = 5
TOTAL_EPOCH = 200


def mainMultipleModels(aggregate = False):
    N = {
        0: {'model': None, 'bestModel': None, 'bestAccuracy': -1, 'epoch': -1},
        1: {'model': None, 'bestModel': None, 'bestAccuracy': -1, 'epoch': -1},
        2: {'model': None, 'bestModel': None, 'bestAccuracy': -1, 'epoch': -1},
        3: {'model': None, 'bestModel': None, 'bestAccuracy': -1, 'epoch': -1},
        4: {'model': None, 'bestModel': None, 'bestAccuracy': -1, 'epoch': -1}
    }

    # load the dataset
    dataset = loadtxt("credit.csv", delimiter=',')
    # split into features (input) and labels (output) variables
    features = dataset[:, 1:]
    labels = dataset[:, 0]

    for n in N:
        # define the keras model
        model = Sequential()
        model.add(Dense(12, input_dim=features[0].size, activation='relu'))
        model.add(Dense(8, activation='relu'))
        model.add(Dense(1, activation='sigmoid'))

        # compile the keras model
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        N[n]['model'] = model

    totalEpoch = 0
    while totalEpoch <= TOTAL_EPOCH:
        aggregatedWeights = []
        for n in N:
            model = N[n]['model']
            # fit the keras model on the dataset
            model.fit(features, labels, epochs=E, batch_size=10, verbose=0)

            # evaluate the keras model
            _, accuracy = model.evaluate(features, labels, verbose=0)
            if accuracy > N[n]['bestAccuracy']:
                N[n]['bestAccuracy'] = accuracy
                N[n]['bestModel'] = deepcopy(model)
                N[n]['epoch'] = totalEpoch + E
            if len(aggregatedWeights) > 0:
                weight = model.get_weights()
                if len(weight) == len(aggregatedWeights):
                    for i in range(len(aggregatedWeights)):
                        aggregatedWeights[i] = aggregatedWeights[i] + weight[i]
                else:
                    print("SHAPE MISMATCH!")
            else:
                aggregatedWeights = model.get_weights()

        for i in range(len(aggregatedWeights)):
            aggregatedWeights[i] = aggregatedWeights[i] / len(N)
        if aggregate:
            for n in N:
                N[n]['model'].set_weights(aggregatedWeights)
        totalEpoch += E

    if aggregate:
        s = "With Aggregation: "
    else:
        s = "Without Aggregation: "
    totalAcc = 0
    for n in N:
        model = N[n]['bestModel']
        epoch = N[n]['epoch']
        _, accuracy = model.evaluate(features, labels, verbose=0)
        # print(f'The Best Accuracy of Model {n}: %.2f from epoch[{epoch}]' % (accuracy * 100))
        s = s + f" %.2f({epoch})" % accuracy
        totalAcc += accuracy
    s = s + " => %.2f" % (totalAcc/len(N))
    print(s)
    return float(totalAcc/len(N))

def mainOnlyOneModel():
    # load the dataset
    dataset = loadtxt("credit.csv", delimiter=',')
    # split into features (input) and labels (output) variables
    features = dataset[:, 1:]
    labels = dataset[:, 0]

    # define the keras model
    model = Sequential()
    model.add(Dense(16, input_dim=features[0].size, activation='relu'))
    model.add(Dense(12, activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    # compile the keras model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    # fit the keras model on the dataset
    model.fit(features, labels, epochs=150, batch_size=10, verbose=0)

    # evaluate the keras model
    # _, accuracy = model.evaluate(features, labels, verbose=0)
    # print(f'The Best Accuracy of Model {n}: %.2f from epoch[{epoch}]' % (accuracy * 100))
    # pass

def mainMultipleBestModels(aggregate = False):
    N = {
        0: {'model': None, 'bestModelWeights': None, 'bestAccuracy': 0.0, 'epoch': -1},
        1: {'model': None, 'bestModelWeights': None, 'bestAccuracy': 0.0, 'epoch': -1},
        2: {'model': None, 'bestModelWeights': None, 'bestAccuracy': 0.0, 'epoch': -1},
        3: {'model': None, 'bestModelWeights': None, 'bestAccuracy': 0.0, 'epoch': -1},
        4: {'model': None, 'bestModelWeights': None, 'bestAccuracy': 0.0, 'epoch': -1}
    }

    # load the dataset
    dataset = loadtxt("credit.csv", delimiter=',')
    # split into features (input) and labels (output) variables
    features = dataset[:, 1:]
    labels = dataset[:, 0]

    for n in N:
        # define the keras model
        model = Sequential()
        model.add(Dense(12, input_dim=features[0].size, activation='relu'))
        model.add(Dense(8, activation='relu'))
        model.add(Dense(1, activation='sigmoid'))

        # compile the keras model
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        N[n]['model'] = model

    totalEpoch = 0
    while totalEpoch <= TOTAL_EPOCH:
        aggregatedWeights = []
        for n in N:
            model = N[n]['model']
            # fit the keras model on the dataset
            model.fit(features, labels, epochs=E, batch_size=10, verbose=0)

            # evaluate the keras model
            _, accuracy = model.evaluate(features, labels, verbose=0)
            print(f'Accuracy of Model {n}: %.2f from epoch[{totalEpoch + E}]' % (accuracy * 100))
            if accuracy > N[n]['bestAccuracy']:
                N[n]['bestAccuracy'] = accuracy
                N[n]['bestModelWeights'] = model.get_weights()
                N[n]['epoch'] = totalEpoch + E
            if len(aggregatedWeights) > 0:
                weight = model.get_weights()
                if len(weight) == len(aggregatedWeights):
                    for i in range(len(aggregatedWeights)):
                        aggregatedWeights[i] = aggregatedWeights[i] + weight[i]
                else:
                    print("SHAPE MISMATCH!")
            else:
                aggregatedWeights = model.get_weights()

        for i in range(len(aggregatedWeights)):
            aggregatedWeights[i] = aggregatedWeights[i] / len(N)
        if aggregate:
            for n in N:
                N[n]['model'].set_weights(aggregatedWeights)
        totalEpoch += E

    if aggregate:
        s = "With Aggregation: "
    else:
        s = "Without Aggregation: "
    totalAcc = 0
    for n in N:
        accuracy = N[n]['bestAccuracy']
        epoch = N[n]['epoch']
        print(f'The Best Accuracy of Model {n}: %.2f from epoch[{epoch}]' % (accuracy * 100))
        s = s + f" %.2f({epoch})" % accuracy
        totalAcc += accuracy
    s = s + " => %.2f" % (totalAcc/len(N))
    print(s)

if __name__ == "__main__":
    # mainOnlyOneModel()
    ########
    # withAgg = []
    # withoutAgg = []
    # for i in range(5):
    #     withoutAgg.append(mainMultipleModels(aggregate=False))
    #     withAgg.append(mainMultipleModels(aggregate=True))
    #
    # withoutAggTotal = 0
    # for i in withoutAgg:
    #     withoutAggTotal += i
    # withoutAggAvr = withoutAggTotal / len(withoutAgg)
    #
    # withAggTotal = 0
    # for i in withAgg:
    #     withAggTotal += i
    # withAggAvr = withAggTotal / len(withAgg)
    #
    # print(f"Without Agg. %.2f vs With Agg. %.2f" % (withoutAggAvr, withAggAvr))
    ########
    mainMultipleBestModels(True)
