# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

#' Get hyperparameter configuration
#'
#' This function loads a file as a JSON. It assumes that the first argument of the running script is the configuraiton 
#' file.  It will parse and inject the hyperparameter variables into the global environment and return them.
#'
#' @param filename optional JSON filename contains hyperparameters as dict, default to first argument in command line.
#' @param env optional environment contains hyperparameters, de fault to global env.
#' @return A matrix of the infile
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
            warning("Auptimizer does not support hyperparameter with size > 1.")
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
#' @param score Score to be reported back to Auptimizer
#' @export
print_result <- function(score) {
    message(paste("\n#Auptimizer:", score))
}