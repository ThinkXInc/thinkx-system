#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# mlutils/utils.py
#
# utility functions for machine learning
#

import os
import math
import time
import numpy as np
import torch
import matplotlib.pyplot as plt


def time_elapse(start, total_iter, i):
    """Stdout time information on trainings.

    args
        - start: time.time()
        - total_iter: int
        - i: int  # current iter

    example
    ----------------------------------------------------------------------------------
    elapse 0.03H iter 3739/500000 [0.7]% estimation 4.45H left (4.49H total)
    ----------------------------------------------------------------------------------
    """
    if i == 0:
        return
    current = time.time()
    elapse = current - start
    progress = (i/total_iter)*100
    iter_time_sec = elapse/i
    total_hour_estimation = (iter_time_sec/(60*60))*total_iter
    left_hour_estimation = (100-progress)*0.01*total_hour_estimation
    print('-' * 90)
    print('elapse {0:.0}H iter {1}/{2} [{3:.3}]% estimation {4:.3}H left ({5:.3}H total)'.format(
        elapse/(60*60), i, total_iter, progress,
        left_hour_estimation, total_hour_estimation))
    print('-' * 90)


def time_since(started) :
    elapsed = time.time() - started
    m = int(elapsed // 60)
    s = int(elapsed % 60)
    if m >= 60 :
        h = int(m // 60)
        m = m % 60
        return f'{h}h {m}m {s}s'
    else :
        return f'{m}m {s}s'


def check_update(model, grad_clip=10, grad_top=150):
    r'''Check model gradient against unexpected jumps and failures'''
    skip_flag = False
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
    if np.isinf(grad_norm):
        print(" | > Gradient is INF !!")
        skip_flag = True
    elif grad_norm > grad_top:
        print(" | > Gradient is above the top limit !!")
        skip_flag = True
    return grad_norm, skip_flag


def update_lr(i, optimizer, annealing_rate=0.95, interval=10000):
    """Update learning rate for annealing.

    args
        - i: int  # iter
        - optimizer: obj  # pytorch optimizer
        - annealing_rate: float
        - annealing_interval: int
    """
    if i != 0 and i % interval == 0:
        # update learning rate by annealing_rate
        for param_group in optimizer.param_groups:
            current_lr = param_group['lr']
        lr = current_lr*annealing_rate
        print('update to new learning rate {}'.format(lr))
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr
        return lr
    return None


def calc_acc(out: torch.FloatTensor, y: np.array):
    """Calculate accuracy.

    args:
        - out: torch.Tensor  # model out (T, N, H)
        - y: np.array  # label vector
    """
    # TODO: enable several input type
    dim = len(out.shape)
    if dim == 3:
        max_indices = out.max(dim=2)[1].view(-1)
        predicted_sequence = max_indices
    if dim == 1:
        predicted_sequence = out
    else:
        print(f'[WARNING] dim of out must be 3. but {len(out.shape)}')
    return (predicted_sequence == torch.from_numpy(y)).sum().data.numpy() / predicted_sequence.shape[0]


def train_test_split_files(data_files_dir: str, test_size=0.3):
    file_paths = list_file_path(data_files_dir)
    print('{} data files found.'.format(len(file_paths)))
    split_idx = int(len(file_paths) * test_size)
    test_file_paths = file_paths[:split_idx]
    train_file_paths = file_paths[split_idx:]
    print('{} train file paths.'.format(len(train_file_paths)))
    print('{} test file paths'.format(len(test_file_paths)))
    return train_file_paths, test_file_paths


def indices_from_file(file_path: str):
    """Load index sequence files

    args
        - file_path: str

    13 139 56 9 139 144 21 2 81
    69 23 62 3 9 63 144 26 2 144 34 18 144
    66 26 17 144 66 144 13 139

    retuns
        - indices: list

    [13 139 56 9 139 144 21 2 81 69 23 62 3 9 63 144 26 2 144 34 18 144 66..]
    """
    indices = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        indices.extend(
            [int(index) for index in line.replace('\n', '').split(' ')
                if index != ''])
    # remove consecutive 144
    indices = [v for i, v in enumerate(indices)
               if i == 0 or not (v == 144 and v == indices[i-1])]
    return indices


def to_onehot(x: np.array, n_class: int):
    return np.eye(n_class)[x]


def list_file_path(data_dir):
    return ['{}{}'.format(data_dir, f) for f in os.listdir(data_dir)
            if os.path.isfile(os.path.join(data_dir, f))]


def shape(l: list, max_sequence_len: int, offset=0, batch_size=20):
    l = l[offset:]
    reminder = len(l) % (max_sequence_len*batch_size)
    # n_padding = max_sequence_len - reminder
    # l.extend([144]*n_padding)
    l = l[:len(l)-reminder]
    n_row = len(l) // max_sequence_len
    return np.array(l).reshape(
        [max_sequence_len, batch_size, int(n_row/batch_size)]
        ).transpose(2, 1, 0)


def load_sequence_data_from_files(
        file_paths: list, max_sequence_len: int, batch_size=20,
        label_offset=1, n_class=145, one_hot_x=True, one_hot_y=False):
    """Load data from index sequence files.

    args
        file_paths: list
        max_sequence_len: int
        batch_size: int
        label_offset: int
        n_class: int
        one_hot_x: bool
        one_hot_y: bool

    returns
        X: np.array  # onehot input sequence
        Y: np.array  # onehot label sequence

    """
    print('load data from files {}'.format(file_paths))
    for file_path in file_paths:
        print('load data from file {} ..'.format(file_path))
        indices = indices_from_file(file_path)
        X = shape(
            indices,
            max_sequence_len,
            batch_size=batch_size)
        Y = shape(
            indices,
            max_sequence_len,
            offset=label_offset,
            batch_size=batch_size)
        X = to_onehot(X, n_class) if one_hot_x else X
        Y = to_onehot(Y, n_class) if one_hot_y else Y
        yield X, Y


def plot(array, title='', fontsize=23):
    fig = plt.figure(figsize=(30, 5))
    ax = fig.add_subplot(111)
    ax.xaxis.label.set_color('grey')
    ax.yaxis.label.set_color('grey')
    ax.xaxis.label.set_fontsize(fontsize)
    ax.yaxis.label.set_fontsize(fontsize)
    ax.tick_params(axis='x', colors='grey', labelsize=fontsize)
    ax.tick_params(axis='y', colors='grey', labelsize=fontsize)
    plt.title(title, fontsize=fontsize)
    plt.plot(array)


def plots(arrays, labels, title='', fontsize=23):
    fig = plt.figure(figsize=(30, 5))
    ax = fig.add_subplot(111)
    ax.xaxis.label.set_color('grey')
    ax.yaxis.label.set_color('grey')
    ax.xaxis.label.set_fontsize(fontsize)
    ax.yaxis.label.set_fontsize(fontsize)
    ax.tick_params(axis='x', colors='grey', labelsize=fontsize)
    ax.tick_params(axis='y', colors='grey', labelsize=fontsize)
    colors = ['darkorange', 'k', 'pink', 'g', 'r-']
    plt.title(title, fontsize=fontsize)
    for i, (array, label) in enumerate(zip(arrays, labels)):
        if array:
            plt.plot(array, label=label, color=colors[i])
            plt.legend()

def train_results(results, limit=3):
    """Show train results.

    Show matplot graph of loss, loss average with a title as below.

    title example)
    wavernn_test_sin [21] 2019/02/28 lr:0.001 n_epoch:1 n_iter:1000 seq_len:1000 hidden_size:896 n_class:256  loss: 6.518

    args:
        results (list): list of MLModelDic obj
        limit (int): showing limit
    """
    for i in range(min(len(results), limit)):
        result = results[i]
        settings = result.settings
        name = f'{result.key_name} [{result.index}]'
        date = f'{result.created.strftime("%Y/%m/%d")}'
        setting = ''
        for key, val in settings.items():
            setting += f'{key}:{val} '
        loss = f'loss: {round(result.loss_averages[-1], 3)}'
        title = f'{name} {date} {setting} {loss}'
        plots([result.losses, result.loss_averages], labels=['loss', 'loss average'], title=title)

def sine_wave(freq, length, sample_rate=16000) : 
    return np.sin(np.arange(length) * 2 * math.pi * freq / sample_rate).astype(np.float32)

def square_wave(freq, length):
    return np.array(([-1.0]*int(freq/2) + [1.0]*int(freq/2))*int(length/freq))

def saw_wave(freq, length):
    return np.tile(np.arange(freq), (int(length/freq)+1))[:length]*(1/freq)

def bit_encode(x:np.ndarray, n:int, signed=True):
    """n bit encoding.

    args:
        - x: np.ndarray  # signal array [-1.0 ~ 1.0]
        - n: int  # ex. 8 (bit)
        - signed: bool  # True(signed) False(unsigned)

    returns:
        - ndarray  # encoded by n (signed, unsigned)
    """
    # e.g. unsigned 8 bit ranging from -128 to 127
    t = np.int8 if n <= 8 else\
        np.int16 if n <= 16 else\
        np.int32 if n <= 32 else\
        np.int64 if n <= 64 else\
        np.int128 if n <= 128 else None
    x_encoded_unsigned = np.clip(x*(2**(n-1)), -2**(n-1), (2**(n-1))-1).astype(t)
    if signed:
        x_encoded_signed = x_encoded_unsigned + 2**(n-1)
        return x_encoded_signed
    else:
        return x_encoded_unsigned

