#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# analysis.py
#

import sys
import math
sys.path.append('../')
from models.history import History, ActionType
from models.rating import Rating, RatingType
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import random


# ///////////////////////////////////
#
# concat actions and positions
#
# ///////////////////////////////////

def init_action_column(df_positions):
    df_positions.loc[:, 'action'] = 0
    print('initialize action column by 0')


def add_action(df_positions, df_action, action_type):
    # add 'action' column if not exist
    if not 'action' in df_positions.columns:
        init_action_column(df_positions)

    # all user ids
    user_ids = [user_id for user_id, _ in df_positions.groupby('user_id')]
    print(f'{len(user_ids)} users found')

    # df_positions for users
    results = []

    # for each user
    for user_id in tqdm(user_ids):
        print(f'user_id {user_id}')

        # positions for this user
        df_positions_user_sorted = df_positions.groupby('user_id').get_group(user_id)

        # set action column
        # df_positions_user_sorted.loc[:, 'action'] = 0

        #
        # play record for this user
        df_action_for_user = df_action[df_action['user_id'] == user_id]
        if len(df_action_for_user) > 0: print(f'{len(df_action_for_user)} actions found')

        # set action into df_positions
        for idx, row_action in df_action_for_user.iterrows():
            print(f'search closest position to data {row_action["utc_date"]}')

            # search position having closest date
            i = df_positions_user_sorted['utc_date'].searchsorted(row_action['utc_date'])

            # set action type to "action" column
            df_positions_user_sorted['action'].iloc[i] = action_type
            print(f'row {i} is closest. set {action_type}.')

        results += [df_positions_user_sorted]

    return pd.concat(results)



# ///////////////////////////////////
#
# generate data to plot in 2d chart
#
# ///////////////////////////////////

def convert_to_metric(lat, lon, clat, clon):
    """convert (dlat, dlon) to (dx, dy)

    args:
    - clat, clon # center lat lon. (0, 0) of the local coordinate system.
    - lat, lon # the position

    returns:
        - x, y  # (x, y) in the local coordinate system with (clat, clon) as the origin (0, 0).
    """

    def dx_per_degree(clat):
        """geo degree to metric (lat)
        """
        lat = math.radians(clat)  # degree to radian
        m1 = 111132.92  # latitude calculation term 1
        m2 = -559.82  # latitude calculation term 2
        m3 = 1.175  # latitude calculation term 3
        m4 = -0.0023  # latitude calculation term 4
        dx_per_dlat = m1 + (m2 * math.cos(2 * clat)) + (m3 * math.cos(4 * clat)) + (m4 * math.cos(6 * clat))
        return dx_per_dlat

    def dy_per_degree(clat):
        """geo degree to metric (lon)
        """
        lon = math.radians(clat)  # degree to radian
        p1 = 111412.84  # longitude calcuclation term 1
        p2 = -93.5  # longitude calcuclation term 2
        p3 = 0.118  # longitude calcuclation term 3
        dy_per_dlon = (p1 * math.cos(clat)) + (p2 * math.cos(3 * clat)) + (p3 * math.cos(5 * clat))
        return dy_per_dlon

    dx_per_dlat = dx_per_degree(clat)
    dy_per_dlon = dy_per_degree(clat)
    dlat = lat - clat
    dlon = lon - clon
    y = dy_per_dlon * dlat
    x = dx_per_dlat * dlon
    return x, y


def gen_locations_by_user(df, df_all):
    locations_by_users = []
    df_by_user_id = df.groupby('user_id')
    indices_by_user = df_by_user_id.groups
    for key, indices in tqdm(indices_by_user.items()):
        print(key, indices)
        locations_by_user = []
        for index in indices:
            df_by_index = df_all.iloc[index]
            d = {
                'user_id': df_by_index['user_id'],
                'lat': df_by_index['lat'],
                'lon': df_by_index['lon'],
                'timestamp': df_by_index['created'],
                'facility_id': df_by_index['facility_id'],
                'action': df_by_index['action']
            }
            locations_by_user.append(d)
        locations_by_users.append(locations_by_user)
    return locations_by_users


def gen_xys_by_user(locations_by_user, clat, clon, max_d=None, min_d=None):
    positions_list = []
    timestamps_list = []
    user_ids = []
    lats_list = []
    lons_list = []
    actions_list = []
    for locations in tqdm(locations_by_user):
        user_id = locations[0]['user_id']
        xs = []
        ys = []
        lats = []
        lons = []
        timestamps = []
        actions = []
        for location in locations:
            lat = location['lat']
            lon = location['lon']
            timestamp = location['timestamp']
            action = location['action']
            x, y = convert_to_metric(lat, lon, clat, clon)
            if max_d and min_d:
                if x < max_d and x > min_d and y < max_d and y > min_d:
                    xs.append(x)
                    ys.append(y)
                    lats.append(lat)
                    lons.append(lon)
                    timestamps.append(timestamp)
                    actions.append(action)
            else:
                    xs.append(x)
                    ys.append(y)
                    lats.append(lat)
                    lons.append(lon)
                    timestamps.append(timestamp)
                    actions.append(action)
        positions_list.append([xs, ys])
        timestamps_list.append(timestamps)
        user_ids.append(user_id)
        lats_list.append(lats)
        lons_list.append(lons)
        actions_list.append(actions)
    return positions_list, timestamps_list, user_ids, lats_list, lons_list, actions_list



# /////////////////////////////////////
#
# draw path from positions
#
# /////////////////////////////////////

def draw_path_from_positions(
        positions_list: list, timestamps_list: list, user_ids: list, lats_list: list, lons_list: list, actions_list: list,
        xlim: tuple, ylim: tuple, n_users_per_figure=20,
        cmap='gist_rainbow',  # 'cool' 'winter'
        title='user activity data', action_point_r_rate=1.0, figsize=(30, 30), font_size=23, size=6,
        xlabel='', ylabel='',
        show_timestamp=True, show_user_id=True, texts: list = None, text_interval=50, verbose=True):
    def get_cmap(n, name=cmap):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)

    def cmap_random(cmap):
        r = random.random()
        return cmap(r)

    def timeformat(timestamps):
        timestrings = pd.to_datetime(timestamps).strftime('%m-%d %H:%M')
        return timestrings

    n = len(positions_list)
    n_figure = 1  # int(n / n_users_per_figure)
    # if n % n_users_per_figure != 0:
    #    n_figure = n_figure + 1

    # create figure
    fig, axs = plt.subplots(n_figure, figsize=(30, 30 * n_figure), sharex=False, dpi=100)
    fig.set_size_inches(13, 13 * n_figure)

    # if verbose: print(f'num figures {len(axs)}')

    def set_ax(ax, xlabel, ylabel, xmin, xmax, ymin, ymax, title, label_color='gray'):
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.xaxis.label.set_color(label_color)
        ax.yaxis.label.set_color(label_color)
        ax.xaxis.label.set_fontsize(font_size)
        ax.yaxis.label.set_fontsize(font_size)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        # ax.autoscale(False)

    def if_inrange(x, y, xlim, ylim) -> bool:
        return x > xlim[0] and x < xlim[1] and y > ylim[0] and y < ylim[1]

    for i in range(n_figure):
        # set_ax(axs[i], xlabel, ylabel, xlim[0], xlim[1], ylim[0], ylim[1], title+f'  [user {i*n_users_per_figure} ~ {i+1*n_users_per_figure}]')
        set_ax(axs, xlabel, ylabel, xlim[0], xlim[1], ylim[0], ylim[1], title)

    n = len(positions_list)
    cmap = get_cmap(n)
    for i, (positions, user_id, timestamps, lats, lons, actions) in tqdm(
            enumerate(zip(positions_list, user_ids, timestamps_list, lats_list, lons_list, actions_list))):
        positions_ = np.array(positions)
        n_positions = positions_.size
        xs = positions[0]
        ys = positions[1]
        ax_index = int(i / n_users_per_figure)
        if verbose: print(f'[{i}] user_id {user_id} has {n_positions} positions, plot to figure {ax_index}')
        c = cmap_random(cmap)
        # axs[ax_index].scatter(xs, ys, color=c, label='', alpha=0.3, zorder=1, s=size)
        axs.scatter(xs, ys, color=c, label='', alpha=0.3, zorder=1, s=size)
        # plt.plot(xs,ys, color=cmap(i), zorder=2, lw=1)
        for i, action in enumerate(actions):
            if action == ActionType.PLAY_AUDIO_CONTENT.value:
                play_point = plt.Circle((xs[i], ys[i]), radius=8*action_point_r_rate, alpha=0.2, color='mediumvioletred')
                axs.add_patch(play_point)
            if action == ActionType.FINISH_GUIDE.value:
                finish_point = plt.Circle((xs[i], ys[i]), radius=4*action_point_r_rate, alpha=0.4, color='black')
                axs.add_patch(finish_point)

        # draw user_id
        if show_user_id:
            if len(xs) > 0 and len(ys) > 0:
                if if_inrange(xs[-1], ys[-1], xlim, ylim):
                    # axs[ax_index].text(xs[-1], ys[-1], f'{user_id}', fontsize=5, color='k')
                    axs.text(xs[-1], ys[-1], f'{user_id}', fontsize=5, color='gray', alpha=0.3)

        # draw timestamp
        timestrings = timeformat(timestamps)
        if show_timestamp:
            for j, (x, y, timestamp) in enumerate(zip(xs, ys, timestrings)):
                # if verbose: print(f'draw text {j} {timestamp_nagasaki_nagasaki_nagasaki}')
                if j == 0 or j == len(xs) - 1 or j % text_interval == 0:
                    if if_inrange(x, y, xlim, ylim):
                        # axs[ax_index].text(x, y, f'{timestamp}', fontsize=10, color=c, alpha=0.2)
                        axs.text(x, y, f'{timestamp}', fontsize=10, color=c, alpha=0.2)

            # draw lat lon
            if len(xs) > 0 and (i == 0 or i == n - 1) and if_inrange(xs[0], ys[0], xlim, ylim):
                offset = 10
                axs.text(xs[0] + offset, ys[0] + offset, f'({lats[0]}, {lons[0]})', fontsize=10, color='k', alpha=1.0)
            if len(xs) > 0 and (i == 0 or i == n - 1) and if_inrange(xs[-1], ys[-1], xlim, ylim):
                offset = 10
                axs.text(xs[-1] + offset, ys[-1] + offset, f'({lats[-1]}, {lons[-1]})', fontsize=10, color='k',
                         alpha=1.0)


def draw(
        positions_list, timestamps_list, user_ids, last_list,
        lons_list, actions_list, xlim, ylim, show_text, text_interval, n_users,
        n_users_per_figure, limit, verbose, draw_all, desc, action_point_r_rate=1.0):

    if draw_all:
        title = f'user activity data ({desc}) [user {0}~{limit}]'
        draw_path_from_positions(
            positions_list[0:limit], timestamps_list[0:limit], user_ids[0:limit],
            last_list[0:limit], lons_list[0:limit], actions_list[0:limit], xlim=xlim, ylim=ylim,
            show_user_id=True, show_timestamp=False, text_interval=text_interval,
            n_users_per_figure=n_users_per_figure, title=title, action_point_r_rate=action_point_r_rate, verbose=verbose)

    step = int(n_users / n_users_per_figure) \
        if n_users % n_users_per_figure == 0 else int(n_users / n_users_per_figure) + 1

    for i in range(step):
        s = i * n_users_per_figure
        e = s + n_users_per_figure if s + n_users_per_figure < limit else limit
        title = f'user activity data ({desc}) [user {s}~{e}]'

        draw_path_from_positions(
            positions_list[s:e], timestamps_list[s:e], user_ids[s:e], last_list[s:e],
            lons_list[s:e], actions_list[s:e], xlim=xlim, ylim=ylim, show_user_id=show_text,
            show_timestamp=show_text, text_interval=text_interval,
            n_users_per_figure=n_users_per_figure, title=title, action_point_r_rate=action_point_r_rate, verbose=verbose)

        if s + n_users_per_figure > limit:
            break