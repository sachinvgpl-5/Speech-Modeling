import sys
import os
#nopep8
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())

from yaml import safe_load
import pandas as pd
from collections import Counter
import librosa
from librosa.display import specshow
import numpy as np
import webrtcvad
import soundfile
from scipy.ndimage import binary_dilation
import pathlib
from colorama import Fore
from tqdm import tqdm
import warnings
import h5py
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

with open('src/config.yaml', 'r') as f:
    config = safe_load(f.read())

RAW_DATA_DIR = config['RAW_DATA_DIR']
PROC_DATA_DIR = config['PROC_DATA_DIR']
INTERIM_DATA_DIR = config['INTERIM_DATA_DIR']
MODEL_SAVE_DIR = config['MODEL_SAVE_DIR']
GMU_DATA_PACKED = config['GMU_DATA_PACKED']
GMU_DATA_INFO = config['GMU_DATA_INFO']
GMU_DATA = config['GMU_DATA']
GMU_ACCENT_COUNT = config['GMU_ACCENT_COUNT']
AUDIO_WRITE_FORMAT = config['AUDIO_WRITE_FORMAT']
AUDIO_READ_FORMAT = config['AUDIO_READ_FORMAT']
SAMPLING_RATE = config['SAMPLING_RATE']
WINDOW_SIZE = config['WINDOW_SIZE']
WINDOW_STEP = config['WINDOW_STEP']
MEL_CHANNELS = config['MEL_CHANNELS']
SMOOTHING_LENGTH = config['SMOOTHING_LENGTH']
SMOOTHING_WSIZE = config['SMOOTHING_WSIZE']
DBFS = config['DBFS']
SMOOTHING_WSIZE = int(SMOOTHING_WSIZE * SAMPLING_RATE / 1000)

dirs_ = set([globals()[d] for d in globals() if d.__contains__('DIR')] +
            [config[d] for d in config if d.__contains__('DIR')])

VAD = webrtcvad.Vad(mode=3)


def structure(dirs=[]):
    """
    Summary:
    
    Args:
    
    Returns:
    
    """
    dirs_reqd = set(list(dirs_) + list(dirs))
    for data_dir in dirs_reqd:
        if not pathlib.Path.exists(pathlib.Path(data_dir)):
            os.makedirs(data_dir)


def normalization(aud, norm_type='peak'):
    """
    Summary:
    
    Args:
    
    Returns:
    
    """
    try:
        assert len(aud) > 0
        if norm_type is 'peak':
            aud = aud / np.max(aud)

        elif norm_type is 'rms':
            dbfs_diff = DBFS - (20 *
                                np.log10(np.sqrt(np.mean(np.square(aud)))))
            if DBFS > 0:
                aud = aud * np.power(10, dbfs_diff / 20)

        return aud
    except AssertionError as e:
        raise AssertionError("Empty audio sig")


def preprocess(fname):
    """
    Summary:
    
    Args:
    
    Returns:
    
    """
    aud, sr = librosa.load(fname, sr=None)
    aud = librosa.resample(aud, sr, SAMPLING_RATE)
    trim_len = len(aud) % SMOOTHING_WSIZE
    aud = np.append(aud, np.zeros(SMOOTHING_WSIZE - trim_len))

    assert len(aud) % SMOOTHING_WSIZE == 0, print(len(aud) % trim_len, aud)

    pcm_16 = np.round(
        (np.iinfo(np.int16).max * aud)).astype(np.int16).tobytes()
    voices = [
        VAD.is_speech(pcm_16[2 * ix:2 * (ix + SMOOTHING_WSIZE)],
                      sample_rate=SAMPLING_RATE)
        for ix in range(0, len(aud), SMOOTHING_WSIZE)
    ]
    smoothing_mask = np.repeat(
        binary_dilation(voices, np.ones(SMOOTHING_LENGTH)), SMOOTHING_WSIZE)
    aud = aud[smoothing_mask]
    try:
        aud = normalization(aud, norm_type='peak')
        return aud

    except AssertionError as e:
        raise AssertionError("Empty audio sig")
        # exit()


def mel_spectogram(aud):
    """
    Summary:
    
    Args:
    
    Returns:
    
    """
    mel = librosa.feature.melspectrogram(aud,
                                         sr=SAMPLING_RATE,
                                         n_fft=WINDOW_SIZE,
                                         hop_length=WINDOW_STEP,
                                         n_mels=MEL_CHANNELS)
    return mel


if __name__ == "__main__":
    strcuture()