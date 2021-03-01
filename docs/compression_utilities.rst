Utility Functions
=================
The utility functions of the NNI compression module are also integrated into Auptimizer. They are useful for analyzing  
the network topology, making informed decisions on the target sparsity levels, and measuring model parameters and FLOPS. 
The basic usages are presented below. Please refer to `NNI compression utilities <https://nni.readthedocs.io/en/stable/Compression/CompressionUtils.html>`__ 
for more advanced applications.

Sensitivity analysis
--------------------
Sensitivity analysis prunes the layers one-by-one to measure the sentivity of each layer to different levels of target sparsity::
 
  # Example of Sensitivity Analysis usage
  # Define a test function to measure the model performance after pruning each layer
  def test(model, device, test_loader):
      ...
      return accuracy # return a metric for evaluation

  s_analyzer = aup.compression.sensitivity_analysis.SensitivityAnalysis(model=model, val_func=lambda model: test(model, device, test_loader))
  sensitivity = s_analyzer.analysis(val_args=[model])
  s_analyzer.export(os.path.join(OUT_DIR, "sensitivity_analysis.log")) 

The sensitivity analysis result will be saved to "sensitivity_analysis.log".

Channel dependency
------------------
We recommend that users run a channel dependency analysis if they want to manually assign target sparsity levels to selected layers, as the 
layers with dependency on each other need to be assigned the same sparsity. Channel dependency can be 
done as follows::

  # Assume input has dimension (1, 1, 28, 28)
  data = torch.ones(1, 1, 28, 28).to(device)
  channel_depen = aup.compression.shape_dependency.ChannelDependency(model, data)
  channel_depen.export(os.path.join(OUT_DIR, "channel_dependency.csv"))

The channel dependency result will be saved to "channel_dependency.csv".

Parameters / FLOPs counter
--------------------------

The FLOPs, number of parameters, and detailed information per layer ("flops", "params", 
"weight_size", "input_size", "output_size", etc) can be measured using::

    flops, params, results = compressor.count_flops_params(input_shape_tuple)
    print(results)
    
The per layer information is saved in "results". 