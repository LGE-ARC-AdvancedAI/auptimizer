ridgeRegression<-function(trainX,trainy,valX,valy,lambda){
  #######################################################
  # A Typical Ridge Regression Problem
  #######################################################
  
  # N =  No. of Training samples, D = Dimension of Problem
  N<-nrow(trainX)
  D <-ncol(trainX)
  I <- diag(D)
  
  
  # Closed form solution for Ridge regression:  min (1/2N)*sum_i (w'*x_i - y_i)^2 + (lambda/2)*||w||^2
  w <- solve((t(trainX)%*%trainX)/N + lambda*I) %*% ((t(trainX)%*%trainy)/N)
  
  
  # Predict on the validation samples and return the error.
  valErr<-MSE(valX,valy,w)
  return(valErr)
}

MSE<-function(X,y,w){
  #####################################################
  # This is the mean squared error
  #####################################################
  N <- nrow(X)
  return((0.5*N)*norm(X%*%w-y))
}

