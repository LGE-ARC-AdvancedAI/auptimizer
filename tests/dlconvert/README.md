## Tests
### Prerequisits
The tests require `Docker` environment to run. 

### Full Unittest
Use `./unittest_tf1.sh` or `./unittest_tf2.sh` to run test in Tensorflow 1.15 or Tensorflow 2.3 environments respectively. In each environment, two sets of tests are run, each with or without eager execution mode. Note that some conversions only work under eager execution mode while some only work under non-eager execution mode. 

After running the unit tests, the results will be summarized in the files `test_summary_tf1.out` and `test_summary_tf2.out`.

