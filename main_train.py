#-*- coding:utf-8 -*-
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import gc
#数据读取
path = '../input/'
train = pd.read_csv(path + 'security_train.csv')
#特征工程(1-Gram)
train_data = train[['file_id','label']].drop_duplicates()
#全局特征
#File_id (Api): count,nunique
api_opt = ['count','nunique']
for opt in api_opt:
    tmp = train.groupby(['file_id'])['api'].agg({'fileid_api_' + opt: opt}).reset_index() 
    train_data = pd.merge(train_data,tmp,how='left', on='file_id')

#File_id (Tid): count,nunique,max,min,median,std
tid_opt = ['count','nunique','max','min','median','std']
for opt in tid_opt:
    tmp = train.groupby(['file_id'])['tid'].agg({'fileid_tid_' + opt: opt}).reset_index() 
    train_data = pd.merge(train_data,tmp,how='left', on='file_id')

#File_id (Tid): quantile(20,40,50,60,80)
secs = [0.2,0.4,0.6,0.8]
for sec in secs:
    train_data['fileid_tid_quantile_' + str(sec * 100)] = train.groupby(['file_id'])['tid'].quantile(sec).values
train_data['fileid_tid_range'] = train.groupby(['file_id'])['tid'].quantile(0.975).values - train.groupby(['file_id'])['tid'].quantile(0.0125).values

#File_id (Index): count,nunique,max,min,median,std
index_opt = ['count','nunique','max','min','median','std']
for opt in index_opt:
    tmp = train.groupby(['file_id'])['index'].agg({'fileid_index_' + opt: opt}).reset_index() 
    train_data = pd.merge(train_data,tmp,how='left', on='file_id')

#File_id (Index): quantile(20,40,50,60,80)
secs = [0.2,0.4,0.6,0.8]
for sec in secs:
    train_data['fileid_index_quantile_' + str(sec * 100)] = train.groupby(['file_id'])['index'].quantile(sec).values
train_data['fileid_index_range'] = train.groupby(['file_id'])['index'].quantile(0.975).values - train.groupby(['file_id'])['index'].quantile(0.0125).values

#局部组合特征(展开形式)
def groupby_pivot_features(data_merge, data_orig , groupby_features,col1 = None, col2 = None, opts = None):
    for opt in opts:
        print(opt)
        train_split = data_orig.groupby(['file_id',col1])[col2].agg({'fileid_' + col1 + '_'+col2+'_'+ str(opt):opt}).reset_index() 
        
        train_split_ =  pd.pivot_table(train_split, values = 'fileid_' + col1 + '_'+col2+'_'+ str(opt), index=['file_id'],columns=[col1])
        new_cols = [ 'fileid_' + col1 + '_'+col2+  '_' + opt + '_' + str(col) for col in train_split_.columns]
        
        groupby_features.append(new_cols)
        train_split_.columns = new_cols 

        train_split_.reset_index(inplace = True)
        
        data_merge = pd.merge(data_merge,train_split_,how='left', on='file_id') 
    return data_merge,groupby_features 

#File_id + Api (tid): count,nunique
groupby_features = []
api_opts = ['count', 'nunique']
train_data_,groupby_features = groupby_pivot_features(train_data, train, groupby_features, col1 = 'api', col2 = 'tid', opts = api_opts)

#File_id + Api(index): nunique, max, min, median, std
api_opts = ['nunique','max','min','median','std']
train_data_,groupby_features = groupby_pivot_features(train_data_, train, groupby_features, col1 = 'api', col2 = 'index', opts = api_opts) 

#特征补充（加入index的差值特征）
#File_id + Api (index_diff): 'nunique','max','min','median','std'
train_diff = train.groupby(['file_id','tid'])['index'].diff().fillna(-999).values
train['index_diff'] = train_diff
train_diff = train.loc[train.index_diff!=-999]
api_opts = ['nunique','max','min','median','std']
train_data_,groupby_features = groupby_pivot_features(train_data_, train_diff, groupby_features, col1 = 'api', col2 = 'index_diff', opts = api_opts) 

#特征工程& 验证结果 2-Gram
#全局特征,File_id（Api_2）:count,nunique
train['api_shift'] = train['api'].shift(-1)
train['api_2'] = train['api'] +'_' + train['api_shift']
train.drop(['api_shift'],axis=1,inplace=True)
api_count = train['api_2'].value_counts()
api_opt = ['count','nunique'] 
for opt in api_opt:
    print(opt)
    tmp = train.groupby(['file_id'])['api_2'].agg({'fileid_api_2_' + opt: opt}).reset_index() 
    train_data_ = pd.merge(train_data_,tmp,how='left', on='file_id')  

#局部特征,File_id + tid (Api_2): count特征
api_value_counts = pd.DataFrame(api_count).reset_index()
api_value_counts.columns = ['api_2','api_2_count']
train = pd.merge(train, api_value_counts, on ='api_2' , how='left')
api_opts = ['count']
groupby_features =  []
train_data_,groupby_features = groupby_pivot_features(train_data_, train.loc[train.api_2_count>=20], groupby_features, col1 = 'api_2', col2 = 'tid', opts = api_opts)

#训练特征 & 标签
train_features = [col for col in train_data_.columns if col!='label' and col!='file_id']
train_label = 'label'
print(len(train_features))
#训练集&验证集
train_X, test_X, train_Y, test_Y = train_test_split( train_data_[train_features],train_data_[train_label].values, test_size = 0.33)
dtrain = lgb.Dataset(train_X,train_Y)
dval   = lgb.Dataset(test_X,test_Y, reference = dtrain)

# 损失函数
def lgb_logloss(preds, data):
    labels_ = data.get_label()
    classes_ = np.unique(labels_)
    preds_prob = []
    for i in range(len(classes_)):
        preds_prob.append(preds[i * len(labels_):(i + 1) * len(labels_)])
    preds_prob_ = np.vstack(preds_prob)

    loss = []
    for i in range(preds_prob_.shape[1]):
        sum_ = 0
        for j in range(preds_prob_.shape[0]):
            pred = preds_prob_[j, i]
            if j == labels_[i]:
                sum_ += np.log(pred)
            else:
                sum_ += np.log(1 - pred)

        loss.append(sum_)

    return 'loss is: ', -1 * (np.sum(loss) / preds_prob_.shape[1]), False

#模型参数
params = {
        'task':'train',
        'num_leaves': 255,
        'objective': 'multiclass',
        'num_class':8,
        'min_data_in_leaf': 10,
        'learning_rate': 0.05,
        'feature_fraction': 0.85,
        'bagging_fraction': 0.9,
        'bagging_freq': 5,
        'max_bin':128,
        'num_threads': 64,
        'random_state':100
    }
lgb_model= lgb.train(params, dtrain, num_boost_round=500,valid_sets=[dtrain,dval], early_stopping_rounds=50, feval=lgb_logloss)

#保留重要特征
fea_imp = pd.DataFrame({'feature':train_features, 'imp':lgb_model.feature_importance()}).sort_values('imp')
important_features = fea_imp.loc[fea_imp.imp >=1, 'feature'].values
important_features = list(important_features)
important_features.append('file_id')
important_features.append('label')
train_ind = train_X.index
test_ind = test_X.index

#局部特征,File_id + index (Api_2): max,min特征
api_opts = ['max','min']
train_data_,groupby_features = groupby_pivot_features(train_data_[important_features], train.loc[train.api_2_count>=20], groupby_features, col1 = 'api_2', col2 = 'index', opts = api_opts)

#训练特征 & 标签
train_features = [col for col in train_data_.columns if col!='label' and col!='file_id' and 'std' not in col and 'quantile' not in col]
train_label = 'label'

#训练集&验证集
dtrain = lgb.Dataset(train_data_.loc[train_ind,train_features],train_data_.loc[train_ind,train_label].values) 
dval   = lgb.Dataset(train_data_.loc[test_ind,train_features],train_data_.loc[test_ind,train_label].values, reference = dtrain)
lgb_model= lgb.train(params, dtrain, num_boost_round=500,valid_sets=[dtrain,dval], early_stopping_rounds=50, feval=lgb_logloss)


#保存训练集
fea_imp = pd.DataFrame({'feature':train_features, 'imp':lgb_model.feature_importance()}).sort_values('imp')
important_features = fea_imp.loc[fea_imp.imp >=1, 'feature'].values
important_features = list(important_features)

important_features.append('file_id')
important_features.append('label')

train_data_[important_features].to_csv('../data/train_data_2gram.csv',index = None)
