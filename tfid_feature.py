# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from xgb_model import tfidfModelTrain, nblrTrain
DATA_TYPE = {
    'label':np.uint8,
    'file_id':np.uint32,
    'tid':np.uint16,
    'index':np.uint16
}

#全局特征
def makeFeature(data, is_train=True):
    #训练集|测试集
    if is_train:
        return_data = data[['file_id', 'label']].drop_duplicates()
    else:
        return_data = data[['file_id']].drop_duplicates()
    #File_id (tid): count
    feat = data.groupby(['file_id']).tid.count().reset_index(name='file_cnt')
    return_data = return_data.merge(feat, on='file_id', how='left')
    # File_id (tid,api): nunique
    feat = data.groupby(['file_id']).agg({'tid':pd.Series.nunique, 'api':pd.Series.nunique}).reset_index()
    feat.columns = ['file_id', 'tid_distinct_cnt', 'api_distinct_cnt']
    return_data = return_data.merge(feat, on='file_id', how='left')
    # File_id (index,api): nunique
    feat_tmp = data.groupby(['file_id', 'tid']).agg({'index':pd.Series.count,'api':pd.Series.nunique}).reset_index()
    # File_id (index): max, min, mean
    feat = feat_tmp.groupby(['file_id'])['index'].agg(['max', 'min', 'mean']).reset_index()
    feat.columns = ['file_id', 'tid_api_cnt_max', 'tid_api_cnt_min', 'tid_api_cnt_mean']
    return_data = return_data.merge(feat, on='file_id', how='left')
    # File_id (api): max, min, mean
    feat = feat_tmp.groupby(['file_id'])['api'].agg(['max', 'min', 'mean']).reset_index()
    feat.columns = ['file_id', 'tid_api_distinct_cnt_max','tid_api_distinct_cnt_min', 'tid_api_distinct_cnt_mean']
    return_data = return_data.merge(feat, on='file_id', how='left')
    return return_data

#读取数据
train= pd.read_csv('../input/security_train.csv', dtype=DATA_TYPE)
test= pd.read_csv('../input/security_test.csv', dtype=DATA_TYPE)
#训练
tr_api_vec, val_api_vec = tfidfModelTrain(train, test)
train_feature= makeFeature(train, True)
tr_prob, te_prob = nblrTrain(tr_api_vec, val_api_vec, train_feature)
#保存结果
tr_prob.to_csv('../data/tr_lr_oof_prob.csv',index=False)
te_prob.to_csv('../data/te_lr_oof_prob.csv',index=False)



















