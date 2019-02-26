#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import gc
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import StratifiedKFold
import datetime

#加载数据
print('cur time = ' + str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
train = np.load('../data/X_train.npy')
test = np.load('../data/X_test.npy')
train_labels = np.load('../data/labels.npy')
print(train.shape,test.shape)

#5-fold训练1
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf.get_n_splits(train,train_labels)
meta_train = np.zeros(shape = (len(train),8))
meta_test = np.zeros(shape = (len(test),8))
for tr_ind,te_ind in skf.split(train,train_labels):
    print ('FOLD:')
    print (len(te_ind),len(tr_ind))
    X_train,X_train_label = train[tr_ind],train_labels[tr_ind]
    X_val,X_val_label = train[te_ind],train_labels[te_ind]
    dtrain = lgb.Dataset(X_train,X_train_label) 
    dval   = lgb.Dataset(X_val,X_val_label, reference = dtrain)   
    params = {
            'task':'train', 
            'boosting_type':'gbdt',
            'num_leaves': 15,
            'objective': 'multiclass',
            'num_class':8,
            'learning_rate': 0.05,
            'feature_fraction': 0.85,
            'subsample':0.85,
            'num_threads': 32,
            'metric':'multi_logloss',
            'seed':100
        }  
    model = lgb.train(params, dtrain, num_boost_round=100000,valid_sets=[dtrain,dval],verbose_eval=100, early_stopping_rounds=100)  
    pred_val = model.predict(X_val)
    pred_test = model.predict(test)
    
    meta_train[te_ind] = pred_val
    meta_test += pred_test
meta_test /= 5.0
pd.to_pickle(meta_train,'../data/train_meta_lgb_1.pkl')
pd.to_pickle(meta_test,'../data/test_meta_lgb_1.pkl')

#5-fold训练2
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf.get_n_splits(train,train_labels)
meta_train = np.zeros(shape = (len(train),8))
meta_test = np.zeros(shape = (len(test),8))
for tr_ind,te_ind in skf.split(train,train_labels):
    print ('FOLD:')
    print (len(te_ind),len(tr_ind))
    X_train,X_train_label = train[tr_ind],train_labels[tr_ind]
    X_val,X_val_label = train[te_ind],train_labels[te_ind]
    dtrain = lgb.Dataset(X_train,X_train_label) 
    dval   = lgb.Dataset(X_val,X_val_label, reference = dtrain)   
    params = {
            'task':'train', 
            'boosting_type':'gbdt',
            'num_leaves': 31,
            'objective': 'multiclass',
            'num_class':8,
            'learning_rate': 0.05,
            'feature_fraction': 0.85,
            'subsample':0.85,
            'num_threads': 32,
            'metric':'multi_logloss',
            'seed':100
        }  
    model = lgb.train(params, dtrain, num_boost_round=100000,valid_sets=[dtrain,dval],verbose_eval=100, early_stopping_rounds=100)  
    pred_val = model.predict(X_val)
    pred_test = model.predict(test)
    
    meta_train[te_ind] = pred_val
    meta_test += pred_test
meta_test /= 5.0
pd.to_pickle(meta_train,'../data/train_meta_lgb_2.pkl')
pd.to_pickle(meta_test,'../data/test_meta_lgb_2.pkl')

#5-fold训练3
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf.get_n_splits(train,train_labels)
meta_train = np.zeros(shape = (len(train),8))
meta_test = np.zeros(shape = (len(test),8))
for tr_ind,te_ind in skf.split(train,train_labels):
    print ('FOLD:')
    print (len(te_ind),len(tr_ind))
    X_train,X_train_label = train[tr_ind],train_labels[tr_ind]
    X_val,X_val_label = train[te_ind],train_labels[te_ind]
    dtrain = lgb.Dataset(X_train,X_train_label) 
    dval   = lgb.Dataset(X_val,X_val_label, reference = dtrain)   
    params = {
            'task':'train', 
            'boosting_type':'gbdt',
            'num_leaves': 31,
            'objective': 'multiclass',
            'num_class':8,
            'learning_rate': 0.045,
            'feature_fraction': 0.8,
            'subsample':0.8,
            'num_threads': 32,
            'metric':'multi_logloss',
            'seed':100
        }  
    model = lgb.train(params, dtrain, num_boost_round=100000,valid_sets=[dtrain,dval],verbose_eval=100, early_stopping_rounds=100)  
    pred_val = model.predict(X_val)
    pred_test = model.predict(test)
    
    meta_train[te_ind] = pred_val
    meta_test += pred_test
meta_test /= 5.0
pd.to_pickle(meta_train,'../data/train_meta_lgb_3.pkl')
pd.to_pickle(meta_test,'../data/test_meta_lgb_3.pkl')

#5-fold训练4
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf.get_n_splits(train,train_labels)
meta_train = np.zeros(shape = (len(train),8))
meta_test = np.zeros(shape = (len(test),8))
for tr_ind,te_ind in skf.split(train,train_labels):
    print ('FOLD:')
    print (len(te_ind),len(tr_ind))
    X_train,X_train_label = train[tr_ind],train_labels[tr_ind]
    X_val,X_val_label = train[te_ind],train_labels[te_ind]
    dtrain = lgb.Dataset(X_train,X_train_label) 
    dval   = lgb.Dataset(X_val,X_val_label, reference = dtrain)   
    params = {
            'task':'train', 
            'boosting_type':'gbdt',
            'num_leaves': 63,
            'objective': 'multiclass',
            'num_class':8,
            'learning_rate': 0.045,
            'feature_fraction': 0.5,
            'subsample':0.7,
            'num_threads': 54,
            'metric':'multi_logloss',
            'seed':100
        }  
    model = lgb.train(params, dtrain, num_boost_round=100000,valid_sets=[dtrain,dval],verbose_eval=100, early_stopping_rounds=100)  
    pred_val = model.predict(X_val)
    pred_test = model.predict(test)
    
    meta_train[te_ind] = pred_val
    meta_test += pred_test
meta_test /= 5.0
pd.to_pickle(meta_train,'../data/train_meta_lgb_4.pkl')
pd.to_pickle(meta_test,'../data/test_meta_lgb_4.pkl')

