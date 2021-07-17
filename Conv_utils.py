import pandas as pd
import pickle
import h2o
import xgboost
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
import warnings

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

h2o.init(nthreads=-1, max_mem_size=12)


def load_all_models_rise():
    model_GLM = h2o.load_model('GLM_model_python_1623496078426_10')
    tuned_GBM = h2o.load_model('GBM_model_python_1623496078426_47')
    model_GBM = h2o.load_model('GBM_model_python_1623496078426_24')
    rf_model = pickle.load(open('rf_convr.pkl', 'rb'))
    return model_GLM, model_GBM, tuned_GBM, rf_model


def load_all_models_dip():
    model_GLM = h2o.load_model('GLM_model_python_1623496078426_15')
    tuned_GBM = h2o.load_model('GBM_model_python_1623496078426_53')
    model_GBM = h2o.load_model('GBM_model_python_1623496078426_25')
    xgb_model = pickle.load(open('xgb_convd.pkl', 'rb'))
    return model_GLM, model_GBM, tuned_GBM, xgb_model


def get_sages(sage_num):
    if sage_num == 1 or sage_num == 2:
        sages = 1
    else:
        sages = -1
    return sages


def get_block(sages, block):
    if sages == 1 and block == 'A':
        rblock = -1
    elif sages == 1 and block == 'B':
        rblock = 1
    else:
        rblock = -1
    return rblock


def get_set_load():
    dip_load = int(input('Enter the Load at the Dip side while setup: '))
    rise_load = int(input('Enter the Load at the Rise side while setup: '))
    return dip_load, rise_load


def getInput():
    print('Enter the input values to predict the Convergence, mm in the deployed SAGES\n')
    n_sages = int(input('Enter the SAGES number (1/2/3/4): '))
    sages = get_sages(n_sages)
    block = input('Enter the Block location (A/B): ')
    rblock = get_block(sages, block)
    set_date = input('Enter the date when the SAGES are setup: ')
    withdraw_date = input('Enter the date when the et SAGES were withdrawed: ')
    level = input('Enter the Level: ')[:2]
    slice = int(input('Enter the Slice value: '))
    dip = int(input('Enter the Dip value: '))
    dip_load, rise_load = get_set_load()
    face_value = int(input('Enter the Face value, mm: '))
    ext_days = int(input('Enter the total slice extraction days: '))
    withdrawal_min = int(input('Enter the time taken for withdrawal: '))
    roof = int(input('Enter the Roof Exposure value: '))
    holes = int(input('Enter the number of holes: '))

    if n_sages == 1 or n_sages == 3:
        featureDict_gbm = {'Level': level, 'Dip': dip, 'Slice': slice, 'Face m': face_value, 'Dip load': dip_load,
                           'Rise load': rise_load,
                           'Withdrawal load dip': 139, 'Withdrawal load rise': 129, 'Conv rise mm': 3,
                           'Slice extraction days': ext_days,
                           'withdrawal time min': withdrawal_min, 'Roof exposure': roof, 'Blasting holes': holes,
                           'Block': rblock, 'SAGES': sages}
        print('Details are mentioned as follows: \n')
        feat = pd.DataFrame(featureDict_gbm, [0])
        print(feat)
    else:
        featureDict_gbm = {'Level': level, 'Dip': dip, 'Slice': slice, 'Face m': face_value, 'Dip load': dip_load,
                           'Rise load': rise_load,
                           'Withdrawal load dip': 139, 'Withdrawal load rise': 129, 'Conv dip mm': 7,
                           'Slice extraction days': ext_days,
                           'withdrawal time min': withdrawal_min, 'Roof exposure': roof, 'Blasting holes': holes,
                           'Block': rblock, 'SAGES': sages}
        print('Details are mentioned as follows: \n')
        feat = pd.DataFrame(featureDict_gbm, [0])
        print(feat)
    return n_sages, featureDict_gbm


def stack_toframe(glm_pred, gbm_pred, tuned_pred):
    glm_ = h2o.as_list(glm_pred)
    glm_val = glm_["predict"].tolist()
    gbm_ = h2o.as_list(gbm_pred)
    gbm_val = gbm_["predict"].tolist()
    tgbm_ = h2o.as_list(tuned_pred)
    tuned_val = tgbm_["predict"].tolist()
    predDict = {'glm': glm_val, 'gbm': gbm_val, 'tuned_gbm': tuned_val}
    pred_df = pd.DataFrame(predDict, index=[0])
    return pred_df


def get_prediction(n_sages, featureDict_gbm):
    if n_sages == 2 or n_sages == 4:
        model_GLM, model_GBM, tuned_GBM, rf_model = load_all_models_rise()
        rise_df = pd.DataFrame(featureDict_gbm, index=[0])
        rise_df = h2o.H2OFrame(rise_df)
        for col in ['Level', 'Dip', 'Slice', 'Block', 'SAGES']:
            rise_df[col] = rise_df[col].asfactor()
        glm_pred = model_GLM.predict(rise_df)
        gbm_pred = model_GBM.predict(rise_df)
        tgbm_pred = tuned_GBM.predict(rise_df)
        pred_df = stack_toframe(glm_pred, gbm_pred, tgbm_pred)
        prediction = rf_model.predict(pred_df)
    else:
        model_GLM, model_GBM, tuned_GBM, xgb_model = load_all_models_dip()
        dip_df = pd.DataFrame(featureDict_gbm, index=[0])
        dip_df = h2o.H2OFrame(dip_df)
        for col in ['Level', 'Dip', 'Slice', 'Block', 'SAGES']:
            dip_df[col] = dip_df[col].asfactor()
        glm_pred = model_GLM.predict(dip_df)
        gbm_pred = model_GBM.predict(dip_df)
        tgbm_pred = tuned_GBM.predict(dip_df)
        pred_df = stack_toframe(glm_pred, gbm_pred, tgbm_pred)
        prediction = xgb_model.predict(pred_df)
    return prediction

