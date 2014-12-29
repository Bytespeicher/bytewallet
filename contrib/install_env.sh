#!/bin/sh

mkdir env
virtualenv env
source env/bin/activate
pip install -r contrib/requirements.txt

