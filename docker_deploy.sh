#!/bin/bash

# docker login
docker build . -t stefan2904/mqtt4telegram
docker push stefan2904/mqtt4telegram:latest
