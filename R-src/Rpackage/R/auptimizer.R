# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

#' Get hyperparameter configuration
#'
#' This function loads a configuration file in JSON format. It assumes that the first argument of the running script is
#' the configuraiton file.  It will parse and inject the hyperparameter variables into the global environment and return
#' them.
#' 
#' 
#' Assuming the R script is used as follows: `./test.R config.json`, the script should look like below:
#' 
#' \preformatted{
#' #!Rscript
#' 
#' # hyperparameter definitions
#' get_config() 
#' # use hyperparamter to train model, 
#' # after training, return optimization target (e.g. validation accuracy) as score
#' print_result(score)
#' }
#' 
#' 
#' 
#' @param filename optional JSON filename containing hyperparameters as dict, default to first argument in command line.
#' @param env optional environment containing hyperparameters, default to global env.
#' @return a matrix of hyperparameters as name-value pairs
#' @export
get_config <- function(filename, env) {
    if (missing(filename)){
        args <- commandArgs(TRUE)
        if (length(args) < 1) {
            warning("R script requires an input configuration file for Auptimzier experiment.")
            return()
        } else if (length(args) > 1) {
            warning("R script takes the first input as configuration file.")
        }
        filename = args[1]
    }
    
    data <- rjson::fromJSON(file=filename)
    if (missing(env)){
        env = globalenv()
    }
    for (name in names(data)) {
        if (length(data[name]) > 1){
            warning("Auptimizer only supports hyperparameter as a single value, not a list. Only first value is used")
        }
        # set to global variables
        assign(name, data[name][[1]], envir = env)
    }
    return(data)
}


#' Report result to Auptimizer
#'
#' This function reports the results to Auptimizer.  A numerical score will be converted to string automatically.  If 
#' you want to report multiple scores, use ',' to seperate them and only the first value will be used by Auptimzier for
#' Optimization.
#' 
#' 
#' Assume the R script is used as follows `./test.R config.json`, the script should look like below:
#' 
#' \preformatted{
#' #!Rscript
#' 
#' # hyperparameter definitions
#' get_config() 
#' # use hyperparamter to train model,
#' # after training, return optimization target (e.g. validation accuracy) as score
#' print_result(score)
#' }
#'
#' @param score Score to be reported back to Auptimizer
#' @export
print_result <- function(score) {
    message(paste("\n#Auptimizer:", score))
}