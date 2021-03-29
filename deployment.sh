#!/bin/bash

# This deployment requires the creation of an an azure docker registry

# Create an image from the current directory using docker image
docker build -t palogiannidi.azurecr.io/gadvi-image:tag1 .

# login to the registry
docker login palogiannidi.azurecr.io

# push the image to the registry
docker push palogiannidi.azurecr.io/gadvi-image:tag1