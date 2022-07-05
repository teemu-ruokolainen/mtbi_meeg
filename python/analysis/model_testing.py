#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 15:01:16 2022

@author: aino

Tests the performance of different models (mainly logistic regression, linear discriminant analysis 
and support vector machine) using stratified k fold cross validation. Plots ROC curve for chosen model
"""

from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn import svm
from sklearn.neighbors import NeighborhoodComponentsAnalysis, KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_curve, roc_auc_score, RocCurveDisplay, auc, plot_confusion_matrix, confusion_matrix, ConfusionMatrixDisplay
from sklearn.covariance import OAS
import numpy as np
from readdata import data_frame
from freq_waves import all_dataframe as bands_dataframe
from freq_waves import ctp_dataframe, gtp_dataframe

import pandas as pd
import matplotlib.pyplot as plt
import math



def main():
    # Get data (ctp_dataframe, bands_dataframe, data_frame, gtp_dataframe)
    data = ctp_dataframe
    X, y = data.iloc[:,1:data.shape[1]], data.loc[:, 'Group']
    
    # Choose parameters
    test = 'roc' # How to test the models ('split', 'roc', 'cv')
    clfs = ['lda'] # List of models to test ('lr', 'lda', 'svm', 'nca', 'qda', 'rf') !!!IN THIS ORDER!!!
    pca = False
    confusion_m = True # To plot a confusion matrix len(clfs) > 1
    folds = 10
    
    
    if test == 'split':
        one_split(clfs, X, y, confusion_m, pca)
    # Stratified k fold cross validation
    elif test == 'cv':
        scores = stratified_k_fold_cv(clfs, X, y, folds, confusion_m, pca)
        print(scores)
        for i in scores:
            print(np.mean(i))
        
    # Plots a ROC curve and uses stratified k fold cross validation (len(clfs)=1)
    elif test == 'roc':
        print(plot_roc_curve(clfs, X, y, folds))


def one_split(clfs, X, y, confusion_m, pca):
    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.25, random_state=20)
    classifiers = []
    # Dimensionality reduction with PCA
    if pca: 
        pca = PCA(n_components=4)
        X_train = pca.fit_transform(X_train)
        X_test = pca.fit_transform(X_test)
       
    # Logistic regression
    if 'lr' in clfs:
        clf = LogisticRegression(random_state=0).fit(X_train, y_train)  
        print(clf.score(X_test, y_test))
        classifiers.append(clf)
    
    # Linear discriminant analysis
    if 'lda' in clfs:
        clf_2 = LinearDiscriminantAnalysis().fit(X_train, y_train)
        print(clf_2.score(X_test, y_test))
        classifiers.append(clf_2)
    
    # Support vector machine
    if 'svm' in clfs:
        clf_3 = svm.SVC()
        clf_3.fit(X_train, y_train)
        print(clf_3.score(X_test, y_test))
        classifiers.append(clf_3)
    
    # Neighborhood component analysis
    if 'nca' in clfs:
        nca = NeighborhoodComponentsAnalysis()
        knn = KNeighborsClassifier()
        nca_pipe = Pipeline([('nca', nca), ('knn', knn)])
        nca_pipe.fit(X_train, y_train)
        print(nca_pipe.score(X_test, y_test))
        # Random forest
    if 'rf' in clfs:
        clf_rf = RandomForestClassifier().fit(X_train, y_train)
        classifiers.append(clf_rf)
        print(clf_rf.feature_importances_)
    # if confusion_m:
    #     plot_confusion_matrices(len(clfs), classifiers, X_test, y_test, clfs)
        
    

def plot_confusion_matrices(dim, clfs, X_test, y_test, titles):
    figure, axis = plt.subplots(1, dim)
    for clf, ax, title in zip(clfs, axis.flatten(), titles):
        ConfusionMatrixDisplay.from_estimator(clf, X_test, y_test, ax=ax)
        ax.title.set_text(title)
    plt.tight_layout()
    plt.show()


    

def plot_roc_curve(clfs, X, y, folds):
    """
    Plots ROC curves for a model
    
    Parameters
    ----------
    clf : LIST
        ('lr', 'lda', 'svm')
    folds : INT
    Returns -
    """
    # Define classifier
    classifier = ''
    if 'lr' in clfs:
        classifier = LogisticRegression(random_state=0)
    elif 'svm' in clfs:
        classifier = svm.SVC()
    elif 'lda' in clfs:
        classifier = LinearDiscriminantAnalysis(solver='lsqr')
    else:
        print("Wrong classifier")
        
    # Stratified k fold cross validation
    skf = StratifiedKFold(n_splits=folds)
    split = skf.split(X, y)   
    tprs = []
    aucs = []
    mean_fpr = np.linspace(0, 1, 100)
    
    for train_index, test_index in split:
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        classifier.fit(X_train, y_train)
        #?pred = clf.predict(X_test).astype(int) 
        # Plot ROC curves for individual folds
        viz = RocCurveDisplay.from_estimator(classifier, X_test, y_test)
        interp_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
        aucs.append(viz.roc_auc)
    fig, ax = plt.subplots()
    ax.plot([0,1],[1,0], lw=2, color='r', label='Chance', alpha=0.8)
    mean_tpr = np.mean(tprs, axis = 0)
    mean_tpr[-1]=1.0
    mean_auc = auc(mean_fpr, mean_tpr) 
    std_auc = np.std(aucs)
    # Plot mean ROC curve
    ax.plot(mean_fpr, mean_tpr, color='b', 
            label=r"Mean ROC (AUC =%0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
            lw=2, alpha = 0.8)  
    std_tpr = np.std(tprs, axis = 0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    ax.fill_between(mean_fpr, tprs_lower, tprs_upper, color='grey', alpha=0.2,
                    label = r'$\pm$ 1 std. dev.')
    ax.set(xlim=[-0.05, 1.05], ylim=[-0.05, 1.05], title="10-fold CV ROC curve")



    #TODO: fix confusion matrix problem 
def stratified_k_fold_cv(clfs, X, y, folds, confusion_m, pca):
    # Stratified K fold cross validation, testing different models
    
    skf = StratifiedKFold(n_splits=folds, shuffle=True)
    split = skf.split(X, y)
    
    # Lists for scores
    stratified_accuracy_lr =[]
    stratified_accuracy_lda =[]
    stratified_accuracy_svm = []
    stratified_accuracy_nca = []
    stratified_accuracy_qda= []
    stratified_accuracy_rf = []
    
    
    
    for train_index, test_index in split:
        # # Get training and testing sets
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        classifiers = []
        # Dimensionality reduction using PCA
        if pca:
            pca = PCA(n_components=15)
            X_train = pca.fit_transform(X_train)
            X_test = pca.fit_transform(X_test)
    
        # Logistic regression
        if 'lr' in clfs:
            clf = LogisticRegression(penalty='l1',solver='liblinear',random_state=0).fit(X_train, y_train)
            stratified_accuracy_lr.append(clf.score(X_test, y_test))
            classifiers.append(clf)
            
        # Linear discriminant analysis
        if 'lda' in clfs:
            clf_2 = LinearDiscriminantAnalysis(solver='svd').fit(X_train, y_train)
            stratified_accuracy_lda.append(clf_2.score(X_test, y_test))
            classifiers.append(clf_2)
             
        # Support vector machine
        if 'svm' in clfs:
            clf_3 = svm.SVC(probability=True)
            clf_3.fit(X_train, y_train)
            stratified_accuracy_svm.append(clf_3.score(X_test, y_test))
            classifiers.append(clf_3)
        
        # Neighborhood component analysis 
        if 'nca' in clfs:
            nca = NeighborhoodComponentsAnalysis()
            knn = KNeighborsClassifier()
            nca_pipe = Pipeline([('nca', nca), ('knn', knn)])
            nca_pipe.fit(X_train, y_train)
            stratified_accuracy_nca.append(nca_pipe.score(X_test, y_test))
            classifiers.append(nca_pipe)
            
        # Quadratic discriminant analysis
        if 'qda' in clfs:
            clf_qda = QuadraticDiscriminantAnalysis()
            clf_qda.fit(X_train, y_train)
            stratified_accuracy_qda.append(clf_qda.score(X_test, y_test))
            classifiers.append(clf_qda)
            
            ### Warning: variables are collinear (also with PCA)
        # Random forest
        if 'rf' in clfs:
            clf_rf = RandomForestClassifier().fit(X_train, y_train)
            stratified_accuracy_rf.append(clf_rf.score(X_test, y_test))
            classifiers.append(clf_rf)
            
        # Plot confusion matrices
        if confusion_m:
            if len(clfs) >1:
                plot_confusion_matrices(len(clfs), classifiers, X_test, y_test, clfs)
            else:
                plot_confusion_matrices(2, classifiers, X_test, y_test, clfs)
    # Return scores
    scores = []
    for i in [stratified_accuracy_lr, stratified_accuracy_lda, stratified_accuracy_svm, 
              stratified_accuracy_nca, stratified_accuracy_qda, stratified_accuracy_rf]:
        if len(i) != 0:
            scores.append(i)
    return scores


        

main()
