# Docker Image Pull Size

This tool helps you estimate how much data will be used when pulling a sequence of images and caching layers.

_This is a super early prototype and mostly for my own use!_

## Usage

```sh
# python3 image_pull_size.py image1 image2 ...
python3 image_pull_size.py python:3.8 python:3.7 my/app
```

Sizes are shown in MBs.