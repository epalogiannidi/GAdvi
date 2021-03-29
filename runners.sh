#!/bin/bash

export PYTHONPATH==$PYTHONPATH:/scripts/

resources='scripts/resources/'
data=$resources"data/"
train_data=$data"subset_5000users_train.tsv"
test_data=$data"subset_5000users_test.tsv"

models=$resources"models/"
model=$models"model_light_fm_simple_256_warp.pickle"
model_data=$models"model_light_fm_simple_256_warp_data.pickle"
model_dataset=$models"model_light_fm_simple_256_warp_dataset.pickle"
playerid="Player_13893025"


if [ "$1" == "train" ]; then
  python scripts/main.py train -config $resources"config.yml" -train_path $train_data -test_path $test_data
fi

if [ "$1" == "predict" ]; then
  python scripts/main.py predict -playerid $playerid -model_path $model -dataset_path $model_dataset -data_path $model_data
fi
