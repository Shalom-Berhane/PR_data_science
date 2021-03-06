import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import *
from src.model.cfw import load_train_test_split
from src.preprocessing.indexer import Indexer


class DataManager:
    def __init__(self, tts_seed=SPLIT_SEED):
        self.tts_seed = tts_seed
        pass

    @staticmethod
    def load_tts_data(duration_ds=False, cnn_ds=True, color_ds=False, face_ds=False, cnn_agg=True,
                      ohe_cnn=False, ohe_color=False, n_labels=None) -> Tuple[
        pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if cnn_ds and ohe_cnn:
            return load_train_test_split(feature_frame=True, one_hot_inputs=True, n_labels=n_labels)

        # Set indizes for joins
        X_train, X_test, y_train, y_test = Indexer.load_split(INDEXED_TTS_PATH)
        X_train.set_index('v_id', inplace=True)
        X_test.set_index('v_id', inplace=True)
        y_train.set_index(X_train.index, inplace=True)
        y_test.set_index(X_test.index, inplace=True)

        X_train.drop('n_samples', 1, inplace=True)
        X_test.drop('n_samples', 1, inplace=True)
        if not duration_ds:
            X_train.drop('v_duration', 1, inplace=True)
            X_test.drop('v_duration', 1, inplace=True)

        if color_ds:
            if ohe_color:
                X_train, X_test = DataManager.get_ohe_color(X_train, X_test)
            else:
                X_train, X_test = DataManager.__load_and_merge(X_train, X_test,
                                                               os.path.join(STORED_COLOR_PATH, 'train_colors.pkl'),
                                                               os.path.join(STORED_COLOR_PATH, 'test_colors.pkl'))

        if face_ds:
            X_train, X_test = DataManager.__load_and_merge(X_train, X_test,
                                                           os.path.join(STORED_FACE_PATH, 'train_faces.pkl'),
                                                           os.path.join(STORED_FACE_PATH, 'test_faces.pkl'))
        if cnn_ds:
            if cnn_agg:
                X_train, X_test = DataManager.__load_and_merge(X_train, X_test,
                                                               os.path.join(STORED_PRED_PATH,
                                                                            f'train_cnn_agg_{cnn_agg}.pkl'),
                                                               os.path.join(STORED_PRED_PATH,
                                                                            f'test_cnn_agg_{cnn_agg}.pkl'))
            else:
                CNN_train, CNN_test, _, _ = load_train_test_split(feature_frame=True, one_hot_inputs=False,
                                                                  nlabels=n_labels)
                X_train = DataManager.merge_df(X_train, CNN_train)
                X_test = DataManager.merge_df(X_test, CNN_test)

        return X_train, X_test, y_train, y_test

    @staticmethod
    def __load_and_merge(X_train, X_test, path_train, path_test) -> Tuple[pd.DataFrame, pd.DataFrame]:
        addon_train = DataManager.load_from_file(path_train)
        addon_test = DataManager.load_from_file(path_test)
        if 'v_id' in addon_train.columns:
            addon_train.set_index('v_id', inplace=True)
            addon_test.set_index('v_id', inplace=True)
        return DataManager.merge_df(X_train, addon_train), DataManager.merge_df(X_test, addon_test)

    @staticmethod
    def log_tf(*varargs):
        res = [df.apply(np.log, axis=1) if isinstance(df, pd.DataFrame) else np.log(df) for df in varargs]
        if len(res) == 1:
            return res[0]
        else:
            return res

    @staticmethod
    def inv_tf(*varargs):
        res = [np.exp(df) for df in varargs]
        if len(res) == 1:
            return res[0]
        else:
            return res

    @staticmethod
    def merge_df(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df1.merge(right=df2, left_index=True, right_index=True)

    @staticmethod
    def write_to_file(filepath: str, df: pd.DataFrame):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_pickle(filepath)

    @staticmethod
    def load_from_file(filepath: str) -> pd.DataFrame:
        return pd.read_pickle(filepath)

    @staticmethod
    def sample_path_from_id(v_id: str):
        return os.path.join(DL_PATH, v_id)

    @staticmethod
    def sample_path_from_dict(vid_dict: Dict):
        return os.path.join(DL_PATH, vid_dict['v_id'])

    @staticmethod
    def extract_v_ids(X: pd.DataFrame) -> List[str]:
        return X.v_id.tolist()

    @staticmethod
    def get_ohe_color(X_train: pd.DataFrame, X_test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        C_train = DataManager.load_from_file(os.path.join(STORED_COLOR_PATH, 'train_colors.pkl')).set_index('v_id')
        C_test = DataManager.load_from_file(os.path.join(STORED_COLOR_PATH, 'test_colors.pkl')).set_index('v_id')
        C_train = pd.concat([pd.get_dummies(C_train[col]) for col in C_train.columns], axis=1)
        C_test = pd.concat([pd.get_dummies(C_test[col]) for col in C_test.columns], axis=1)
        return DataManager.merge_df(X_train, C_train), DataManager.merge_df(X_test, C_test)

    @staticmethod
    def preprocess_data(X_train, X_test, y_train, y_test, pp_dict: dict = PP_DICT):
        if pp_dict['std_scale']:
            std = StandardScaler(with_mean=pp_dict.get('with_mean', True)).fit(X=X_train)
            X_train = std.transform(X_train)
            X_test = std.transform(X_test)

        if pp_dict['n_components'] >= 0:
            pca = PCA(n_components=pp_dict['n_components']).fit(X_train)
            X_train = pca.transform(X_train)
            X_test = pca.transform(X_test)

        if pp_dict['log_tf']:
            y_train, y_test = DataManager.log_tf(y_train, y_test)

        return X_train, X_test, y_train, y_test


if __name__ == '__main__':
    X_train, X_test, y_train, y_test = DataManager.load_tts_data(True, True, True, True, True, False, True)
