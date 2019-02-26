## 阿里云安全恶意程序检测比赛链接:
https://tianchi.aliyun.com/competition/information.htm?spm=5176.100067.5678.2.63ff703ecG8fkG&raceId=231694

## PPT:
阿里云安全恶意程序检测.pptx

## 代码按照以下运行顺序:
* main_train.py:生成train数据集TF-IDF,2-Gram特征,并去掉不重要的特征
* main_test.py:生成test数据集TF-IDF,2-Gram特征,保持和train特征一致,并保存成npy文件
* lgb_meta_features.py:生成LGB元特征
* CNN_metafeature.py:生成CNN元特征
* CNN_metafeature_dilated.py:生成CNN_dilated元特征
* tfid_feature.py:生成XGB元特征
* submit.py:stacking生成最终结果