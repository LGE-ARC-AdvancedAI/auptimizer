#!/usr/bin/env Rscript
# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Example code to use Auptimzier.
library("auptimizer")
source("ridgeRegression.R")


# Synthetic Data
Nt = 90
D = 100
w<-rnorm(D)
trainX<-matrix(rnorm(Nt*D,0,1),nrow=Nt,ncol=D)
trainy<-trainX%*%w + rnorm(Nt,0,1) # Add Gaussian noise

Nv = 40
valX<-matrix(rnorm(Nv*D,0,1),nrow=Nv,ncol=D)
valy<-valX%*%w + rnorm(Nv,0,1) # Add Gaussian noise


# Hyperparameters
lambda = 1.0

hp <- get_config()
score <- ridgeRegression(trainX,trainy,valX,valy,lambda)
print_result(score)
