#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from sklearn.preprocessing import LabelBinarizer,LabelEncoder
from sklearn.model_selection import StratifiedKFold

#加载数据
path = '../input/'
train = pd.read_csv(path + 'security_train.csv')
test = pd.read_csv(path + 'security_test.csv')

#生成API序列
unique_api = train['api'].unique()
api2index = {item:(i+1) for i,item in enumerate(unique_api)}
index2api = {(i+1):item for i,item in enumerate(unique_api)}
train['api_idx'] = train['api'].map(api2index)
test['api_idx'] = test['api'].map(api2index)
train_period_idx = train.file_id.drop_duplicates(keep='first').index.values
test_period_idx = test.file_id.drop_duplicates(keep='first').index.values
def get_sequence(df,period_idx):
    seq_list = []
    for _id,begin in enumerate(period_idx[:-1]):
        seq_list.append(df.iloc[begin:period_idx[_id+1]]['api_idx'].values)
    seq_list.append(df.iloc[period_idx[-1]:]['api_idx'].values)
    return seq_list
train_df = train[['file_id','label']].drop_duplicates(keep='first')
test_df = test[['file_id']].drop_duplicates(keep='first')
train_df['seq'] = get_sequence(train,train_period_idx)
test_df['seq'] = get_sequence(test,test_period_idx)
train_df.seq.map(lambda x: len(x)).std(),train_df.seq.map(lambda x: len(x)).mean(),train_df.seq.map(lambda x: len(x)).max()
test_df.seq.map(lambda x: len(x)).std(),test_df.seq.map(lambda x: len(x)).mean(),test_df.seq.map(lambda x: len(x)).max()


from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, LSTM, Lambda, Embedding, Dropout, Activation,GRU,Bidirectional
from keras.layers import Conv1D,Conv2D,MaxPooling2D,GlobalAveragePooling1D,GlobalMaxPooling1D, MaxPooling1D, Flatten
from keras.layers import CuDNNGRU, CuDNNLSTM, SpatialDropout1D
from keras.layers.merge import concatenate, Concatenate, Average, Dot, Maximum, Multiply, Subtract, average
from keras.models import Model
from keras.optimizers import RMSprop,Adam
from keras.layers.normalization import BatchNormalization
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.optimizers import SGD
from keras import backend as K
from sklearn.decomposition import TruncatedSVD, NMF, LatentDirichletAllocation
from keras.layers import SpatialDropout1D
from keras.layers.wrappers import Bidirectional

#模型
def TextCNN(max_len,max_cnt,embed_size,
            num_filters,kernel_size,
            conv_action,
            mask_zero):
    _input = Input(shape=(max_len,), dtype='int32')
    _embed = Embedding(max_cnt, embed_size, input_length=max_len, mask_zero=mask_zero)(_input)
    _embed = SpatialDropout1D(0.15)(_embed)
    warppers = []
    for _kernel_size in kernel_size:
        conv1d = Conv1D(filters=num_filters, kernel_size=_kernel_size, activation=conv_action)(_embed)
        warppers.append(GlobalMaxPooling1D()(conv1d))          
    fc = concatenate(warppers)
    fc = Dropout(0.5)(fc)
    #fc = BatchNormalization()(fc)
    fc = Dense(256, activation='relu')(fc)
    fc = Dropout(0.25)(fc)
    #fc = BatchNormalization()(fc) 
    preds = Dense(8, activation = 'softmax')(fc)
    
    model = Model(inputs=_input, outputs=preds)
    
    model.compile(loss='categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy'])
    return model

#训练集&测试集
y=train_df.label.values
train_labels = pd.get_dummies(train_df.label).values
train_seq = pad_sequences(train_df.seq.values, maxlen = 6000)
test_seq = pad_sequences(test_df.seq.values, maxlen = 6000)
np.save('../data/train_labels.npy',train_labels)
np.save('../data/train_seq.npy',train_seq)
np.save('../data/test_seq.npy',test_seq)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf.get_n_splits(train_seq,train_labels)

#参数
max_len = 6000
max_cnt = 295
embed_size = 256
num_filters = 64
kernel_size = [2,4,6,8,10,12,14]
conv_action = 'relu'
mask_zero = False
TRAIN = True

#使用GPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
meta_train = np.zeros(shape = (len(train_seq),8))
meta_test = np.zeros(shape = (len(test_seq),8))
FLAG = False

#训练
for i, (tr_ind, te_ind) in enumerate(skf.split(train_seq,y)):
    print('FOLD: '.format(i))
    print(len(te_ind),len(tr_ind))
    model = TextCNN(max_len,max_cnt,embed_size,num_filters,kernel_size,conv_action,mask_zero)
    model_name = 'benchmark_textcnn_fold_'+str(i)
    X_train,X_train_label = train_seq[tr_ind],train_labels[tr_ind]
    X_val,X_val_label = train_seq[te_ind],train_labels[te_ind]
    
    model = TextCNN(max_len,max_cnt,embed_size,
            num_filters,kernel_size,
            conv_action,
            mask_zero)
    
    model_save_path = '../data/%s_%s.hdf5'%(model_name,embed_size)
    early_stopping =EarlyStopping(monitor='val_loss', patience=3)
    model_checkpoint = ModelCheckpoint(model_save_path, save_best_only=True, save_weights_only=True)
    model.fit(X_train,X_train_label,
              validation_data=(X_val,X_val_label),
              epochs=100,batch_size=64,
              shuffle=True,
              callbacks=[early_stopping,model_checkpoint]
             )
    model.load_weights(model_save_path)
    pred_val = model.predict(X_val,batch_size=128,verbose=1)
    pred_test = model.predict(test_seq,batch_size=128,verbose=1)
    
    meta_train[te_ind] = pred_val
    meta_test += pred_test
    K.clear_session()
meta_test /= 5.0

#保存训练结果
pd.to_pickle(meta_train,'../data/train_meta_cnn.pkl')
pd.to_pickle(meta_test,'../data/test_meta_cnn.pkl')
