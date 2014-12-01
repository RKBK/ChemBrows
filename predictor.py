#!/usr/bin/python
# -*-coding:Utf-8 -*

import sys
import os
from PyQt4 import QtSql

#Pour les modules persos
sys.path.append('/home/djipey/informatique/python/batbelt')
import batbelt


import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB

from sklearn.feature_extraction import text 


class Predictor():

    """Object to predict the percentage match of an article,
    based on its abstract"""


    def __init__(self, bdd=None):

        self.x_train = []
        self.y_train = []
        self.classifier = None

        self.bdd = bdd

        self.initializePipeline()


    def getStopWords(self):

        """Method to get english stop words
        + a list of personnal stop words"""

        my_additional_stop_words = []

        with open('config/stop_words.txt', 'r') as config:
            for word in config.readlines():
                my_additional_stop_words.append(word.replace("\n", ""))

        self.stop_words = text.ENGLISH_STOP_WORDS.union(my_additional_stop_words)


    def initializePipeline(self):

        """Initialize the pipeline for text analysis"""

        if self.bdd is None:
            self.bdd = QtSql.QSqlDatabase.addDatabase("QSQLITE");
            self.bdd.setDatabaseName("fichiers.sqlite");
            self.bdd.open()

        query = QtSql.QSqlQuery("fichiers.sqlite")

        query.exec_("SELECT * FROM papers WHERE new=0")

        while query.next():
            record = query.record()

            if type(record.value('abstract')) is str:
                abstract = record.value('abstract')
            else:
                continue

            if type(record.value('liked')) is not int:
                category = 0
            else:
                category = 1

            self.x_train.append(abstract)
            self.y_train.append(category)

        self.x_train = np.array(self.x_train)
        self.y_train = np.array(self.y_train)

        self.getStopWords()

        self.classifier = Pipeline([
            ('vectorizer', CountVectorizer(
                            stop_words=self.stop_words)),
            ('tfidf', TfidfTransformer()),
            ('clf', MultinomialNB())])

        self.classifier.fit(self.x_train, self.y_train)


    def calculatePercentageMatch(self, test=False):

        """Calculate the match percentage for each article,
        based on the abstract text and the liked articles"""

        print("Starting calculations of match percentages")

        query = QtSql.QSqlQuery("fichiers.sqlite")

        query.exec_("SELECT id, abstract FROM papers")

        list_id = []
        x_test = []

        while query.next():

            record = query.record()

            if type(record.value('abstract')) is str:
                abstract = record.value('abstract')

                list_id.append(record.value('id'))
                x_test.append(abstract)

        x_test = np.array(x_test)

        #list_percentages = [ round(float(100 * proba[1]), 2) for proba in self.classifier.predict_proba(x_test) ]
        list_percentages = [ float(100 * proba[1]) for proba in self.classifier.predict_proba(x_test) ]

        if test:
            print(list_percentages)
        else:
            for id_bdd, percentage in zip(list_id, list_percentages):
                request = "UPDATE papers SET percentage_match = ? WHERE id = ?"
                params = (percentage, id_bdd)

                query = QtSql.QSqlQuery("fichiers.sqlite")

                query.prepare(request)

                for value in params:
                    query.addBindValue(value)

                query.exec_()

            print("Done calculating match percentages")




if __name__ == "__main__":
    predictor = Predictor()
    predictor.calculatePercentageMatch(True)
    predictor.getStopWords()
    pass

