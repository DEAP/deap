#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import numpy
import csv
import operator
import random

class KNN(object):
    def __init__(self, k):
        self.k = k
        self.data = None
        self.labels = None
        self.ndim = 0
    
    def train(self, data, labels):
        self.data = numpy.array(data)
        self.labels = numpy.array(labels)
        self.classes = numpy.unique(self.labels)
        self.ndim = len(self.data[0])
    
    def predict(self, data, features=None):
        data = numpy.array(data)
        if features is None:
            features = numpy.ones(self.data.shape[1])
        else:
            features = numpy.array(features)
        
        if data.ndim == 1:
            dist = self.data - data
        elif data.ndim == 2:
            dist = numpy.zeros((data.shape[0],) + self.data.shape)
            for i, d in enumerate(data):
                dist[i, :, :] = self.data - d
        else:
            raise ValueError("Cannot process data with dimensionality > 2")
        dist = features * dist
        dist = dist * dist
        dist = numpy.sum(dist, -1)
        dist = numpy.sqrt(dist)
        nns = numpy.argsort(dist)
        
        if data.ndim == 1:
            classes = dict((cls, 0) for cls in self.classes)
            for n in nns[:self.k]:
                classes[self.labels[n]] += 1
            labels = sorted(classes.items(), key=operator.itemgetter(1))[-1][0]
        elif data.ndim == 2:
            labels = list()
            for i, d in enumerate(data):
                classes = dict((cls, 0) for cls in self.classes)
                for n in nns[i, :self.k]:
                    classes[self.labels[n]] += 1
                labels.append(sorted(classes.items(), key=operator.itemgetter(1))[-1][0])
        
        return labels

# Create a default internal KNN object
# Read data from file
FILE="heart_scale.csv"
N_TRAIN=175
K=1

with open(FILE, "r") as data_csv:
    data = csv.reader(data_csv)
    trainset = list()
    trainlabels = list()
    rows = [row for row in data]

random.shuffle(rows)
for row in rows:
    trainlabels.append(float(row[0]))
    trainset.append([float(e) for e in row[1:]])

_knn = KNN(K)
_knn.train(trainset[:N_TRAIN], trainlabels[:N_TRAIN])

def classification_rate(features):
    """Returns the classification rate of the default KNN."""
    labels = _knn.predict(trainset[N_TRAIN:], features)
    return sum(x == y for x, y in zip(labels, trainlabels[N_TRAIN:]))/float(len(trainlabels[N_TRAIN:]))

if __name__ == "__main__":
    trainset = [[1, 0], [1, 1], [1, 2]]
    trainlabels = [1, 2, 3]
    knn = KNN(1)
    knn.train(trainset, trainlabels)
    print("Single Data ===========")
    print(knn.predict([1, 0], [1, 1]))
    print("Multiple Data ===========")
    print(knn.predict([[1, 3], [1, 0]], [1, 1]))
