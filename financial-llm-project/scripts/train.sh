#!/bin/bash

# CUDA 관련 환경변수 설정
export CUDA_VISIBLE_DEVICES=0,1  # 사용할 GPU 지정
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Python 가상환경 활성화 (필요한 경우)
# source /path/to/your/venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt

# 학습 실행
python src/training/run_training.py 