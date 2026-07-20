#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# migrate/migrate.py
#
# Mongo Supermarket全般のデータ更新スクリプト
#

import sys
sys.path.append('..')
from models.recommend import Recommend
from models.history import History
from csv_import.store_nutrient_effect import StoreNutrientEffect
from csv_import.store_standard_in_mongo import StandardImporter
import argparse


def create_index_all():
    """全てのMongoモデルのcreateIndexes()を実行
    """
    Recommend.createIndexes()
    History.createIndexes()

def update_animal_effects():
    store_nutrient_effect = StoreNutrientEffect()
    store_nutrient_effect.update_animal_effects()

def update_appropriate_nutrient_zone():
    StandardImporter.store_appropriate_zone_in_mongo()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create_index",
        help="update index for thesystem database",
        action="store_true")
    parser.add_argument(
        "--animal_effects",
        help="update all animal.effects",
        action="store_true")
    parser.add_argument(
        "--appropriate_zone",
        help="store appropriate zone to each nutrient standards",
        action="store_true"
    )

    args = parser.parse_args()

    if args.create_index:
        create_index_all()

    if args.animal_effects:
        update_animal_effects()

    if args.appropriate_zone:
        update_appropriate_nutrient_zone()
