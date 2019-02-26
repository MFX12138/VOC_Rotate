import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import gc
from sklearn.preprocessing import OneHotEncoder
import datetime
from sklearn.model_selection import StratifiedKFold

#加载数据
print('cur time = ' + str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
train = np.load('../data/X_train.npy')
test = np.load('../data/X_test.npy')
train_labels = np.load('../data/labels.npy')

#加载特征
train_cnn_1 = pd.read_pickle('../data/train_meta_cnn.pkl')
test_cnn_1= pd.read_pickle('../data/test_meta_cnn.pkl')
train_cnn_2= pd.read_pickle('../data/train_meta_dilated_cnn.pkl')
test_cnn_2 = pd.read_pickle('../data/test_meta_dilated_cnn.pkl')
train_lgb_1 = pd.read_pickle('../data/train_meta_lgb_1.pkl')
test_lgb_1 = pd.read_pickle('../data/test_meta_lgb_1.pkl')
train_lgb_2 = pd.read_pickle('../data/train_meta_lgb_2.pkl')
test_lgb_2 = pd.read_pickle('../data/test_meta_lgb_2.pkl')
train_lgb_3 = pd.read_pickle('../data/train_meta_lgb_3.pkl')
test_lgb_3 = pd.read_pickle('../data/test_meta_lgb_3.pkl')
train_lgb_4 = pd.read_pickle('../data/train_meta_lgb_4.pkl')
test_lgb_4 = pd.read_pickle('../data/test_meta_lgb_4.pkl')
extra_feat_val = pd.read_csv('../data/tr_lr_oof_prob.csv').drop(columns='file_id').values
extra_feat_test = pd.read_csv('../data/te_lr_oof_prob.csv').drop(columns='file_id').values

#连接特征
train = np.hstack([train, train_lgb_1, train_lgb_2, train_lgb_3, train_lgb_4,train_cnn_1,train_cnn_2,extra_feat_val])
test = np.hstack([test, test_lgb_1, test_lgb_2, test_lgb_3, test_lgb_4,test_cnn_1,test_cnn_2,extra_feat_test])

#训练
meta_test = np.zeros(shape = (len(test),8))
for seed in range(1):
    print ('Times: ',seed)
    print('cur time = ' + str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    skf.get_n_splits(train,train_labels)
    for tr_ind,te_ind in skf.split(train,train_labels):
        print(len(te_ind),len(tr_ind))
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
                'learning_rate': 0.01,
                'feature_fraction': 0.85,
                'subsample':0.85,
                'num_threads': 54,
                'metric':'multi_logloss',
                'seed':seed
            }  
        model = lgb.train(params, dtrain, num_boost_round=100000,valid_sets=[dtrain,dval],verbose_eval=100, early_stopping_rounds=100)  
        pred_test = model.predict(test)
        #meta_train[te_ind] = pred_val
        meta_test += pred_test
        print('cur time = ' + str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
meta_test/=5.0

#保存结果
res = pd.DataFrame(meta_test,columns=['prob0','prob1','prob2','prob3','prob4','prob5','prob6','prob7'])
res.index.name='file_id'
res.round(5).to_csv('../submit/round5_LGB+CNN+XGB.csv', index = True, header=True)
res.index = range(1,res.shape[0]+1)
res.index.name = 'file_id'
en =res.copy()
en.sum(axis=1).max()
en.to_csv('../submit/LGB+CNN+XGB.csv',index=True,header=True,float_format='%.5f')
train=en
train=train.round(5)
train['prob7']=1-train['prob0']-train['prob1']-train['prob2']-train['prob3']-train['prob4']-train['prob5']-train['prob6']
train.to_csv('../submit/submit_rlt_TEST.csv',index=None,float_format='%.5f')

