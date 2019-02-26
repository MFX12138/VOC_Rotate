#-*- coding:utf-8 -*-
import pandas as pd
import numpy as np
import gc

#数据读取
path = '../input/'
test = pd.read_csv(path + 'security_test.csv')

#特征工程(1-Gram)
test_data = test['file_id'].drop_duplicates()
test_data=pd.DataFrame(test_data)

#全局特征
#File_id (Api): count,nunique
api_opt = ['count','nunique']
for opt in api_opt:
    tmp = test.groupby(['file_id'])['api'].agg({'fileid_api_' + opt: opt}).reset_index() 
    test_data = pd.merge(test_data,tmp,how='left', on='file_id')

#File_id (Tid): count,nunique,max,min,median,std
tid_opt = ['count','nunique','max','min','median','std']
for opt in tid_opt:
    tmp = test.groupby(['file_id'])['tid'].agg({'fileid_tid_' + opt: opt}).reset_index() 
    test_data = pd.merge(test_data,tmp,how='left', on='file_id')

#File_id (Tid): quantile(20,40,50,60,80)
secs = [0.2,0.4,0.6,0.8]
for sec in secs:
    test_data['fileid_tid_quantile_' + str(sec * 100)] = test.groupby(['file_id'])['tid'].quantile(sec).values
test_data['fileid_tid_range'] = test.groupby(['file_id'])['tid'].quantile(0.975).values - test.groupby(['file_id'])['tid'].quantile(0.0125).values

#File_id (Index): count,nunique,max,min,median,std
index_opt = ['count','nunique','max','min','median','std']
for opt in index_opt:
    tmp = test.groupby(['file_id'])['index'].agg({'fileid_index_' + opt: opt}).reset_index() 
    test_data = pd.merge(test_data,tmp,how='left', on='file_id')

#File_id (Index): quantile(20,40,50,60,80)
secs = [0.2,0.4,0.6,0.8]
for sec in secs:
    test_data['fileid_index_quantile_' + str(sec * 100)] = test.groupby(['file_id'])['index'].quantile(sec).values
test_data['fileid_index_range'] = test.groupby(['file_id'])['index'].quantile(0.975).values - test.groupby(['file_id'])['index'].quantile(0.0125).values

#局部组合特征(展开形式)
def groupby_pivot_features(data_merge, data_orig , groupby_features,col1 = None, col2 = None, opts = None):
    for opt in opts:
        print(opt)
        test_split = data_orig.groupby(['file_id',col1])[col2].agg({'fileid_' + col1 + '_'+col2+'_'+ str(opt):opt}).reset_index() 
        
        test_split_ =  pd.pivot_table(test_split, values = 'fileid_' + col1 + '_'+col2+'_'+ str(opt), index=['file_id'],columns=[col1])
        new_cols = [ 'fileid_' + col1 + '_'+col2+  '_' + opt + '_' + str(col) for col in test_split_.columns]
        
        groupby_features.append(new_cols)
        test_split_.columns = new_cols 

        test_split_.reset_index(inplace = True)
        
        data_merge = pd.merge(data_merge,test_split_,how='left', on='file_id') 
    return data_merge,groupby_features 

#File_id + Api (tid): count,nunique
groupby_features = []
api_opts = ['count', 'nunique']
test_data_,groupby_features = groupby_pivot_features(test_data, test, groupby_features, col1 = 'api', col2 = 'tid', opts = api_opts)

#File_id + Api(index): nunique, max, min, median, std
api_opts = ['nunique','max','min','median','std']
test_data_,groupby_features = groupby_pivot_features(test_data_, test, groupby_features, col1 = 'api', col2 = 'index', opts = api_opts) 

#特征补充（加入index的差值特征）
#File_id + Api (index_diff): 'nunique','max','min','median','std'
test_diff = test.groupby(['file_id','tid'])['index'].diff().fillna(-999).values
test['index_diff'] = test_diff
test_diff = test.loc[test.index_diff!=-999]
api_opts = ['nunique','max','min','median','std']
test_data_,groupby_features = groupby_pivot_features(test_data_, test_diff, groupby_features, col1 = 'api', col2 = 'index_diff', opts = api_opts) 

#特征工程& 验证结果 2-Gram
#全局特征,File_id（Api_2）:count,nunique
test['api_shift'] = test['api'].shift(-1)
test['api_2'] = test['api'] +'_' + test['api_shift']
test.drop(['api_shift'],axis=1,inplace=True)
api_count = test['api_2'].value_counts()
api_opt = ['count','nunique'] 
for opt in api_opt:
    print(opt)
    tmp = test.groupby(['file_id'])['api_2'].agg({'fileid_api_2_' + opt: opt}).reset_index() 
    test_data_ = pd.merge(test_data_,tmp,how='left', on='file_id')  

#局部特征,File_id + tid (Api_2): count特征
api_value_counts = pd.DataFrame(api_count).reset_index()
api_value_counts.columns = ['api_2','api_2_count']
test = pd.merge(test, api_value_counts, on ='api_2' , how='left')
api_opts = ['count']
groupby_features =  []
test_data_,groupby_features = groupby_pivot_features(test_data_, test, groupby_features, col1 = 'api_2', col2 = 'tid', opts = api_opts)

#局部特征,File_id + index (Api_2): max,min特征
api_opts = ['max','min']
test_data_,groupby_features = groupby_pivot_features(test_data_, test, groupby_features, col1 = 'api_2', col2 = 'index', opts = api_opts)

#保存测试集
test_data_.to_csv('../data/test_data_2gram.csv',index = None)
train_data_= pd.read_csv('../data/train_data_2gram.csv')
cols = [item for item in train_data_.columns if item not in ['label']]
np.save('../data/X_test.npy',test_data_[cols].values)
np.save('../data/X_train.npy',train_data_[cols].values)
np.save('../data/labels.npy',train_data_['label'].values)

