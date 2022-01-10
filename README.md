# Docker Image Pull Size

This tool helps you estimate how much data will be used when pulling a sequence of images and caching layers.

_This is a super early prototype and mostly for my own use!_

## Usage

```sh
# python3 image_pull_size.py image1 image2 ...
python3 image_pull_size.py python:3.8 python:3.7 my/app
```

_The arch (amd64, arm64) can be provided using the `--arch` flag._

The output will contain a trace of the total size and number of layers accumulated by the provided sequence of pulls.

* `name`. Name of image pulled at this step.
* `size_total`. Total _accumulated_ size.
* `size_total_pct`. Total _accumulated_ size as percentage of final accumulated size.
* `size_delta`. Size of _new_ layers in this pull.
* `size_delta_pct`. Size of _new_ layers in this pull as percentage of final accumulated size.
* `layers_total`. Total _accumulated_ number of layers.
* `layers_delta`. _New_ layers in this pull.
