from sklearn.ensemble import RandomForestRegressor

from src.config import N_JOBS
from src.model.utils import train_model

# TODO GS PARAMS
params = {'n_jobs': N_JOBS}
pp_dict = {'n_components': -1}
data_dict = {'duration_ds': True,
             'cnn_ds': False,
             'color_ds': True,
             'face_ds': True,
             'cnn_agg': False,
             'ohe_cnn': False,
             'ohe_color': False,
             'n_labels': None
             }

pipeline, m_err = train_model(RandomForestRegressor(), params, data_dict, pp_dict, save_model=True)
