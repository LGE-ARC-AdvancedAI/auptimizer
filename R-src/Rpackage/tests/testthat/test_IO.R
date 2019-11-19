library(auptimizer)

test_that("auptimizer output format", {
  expect_message(print_result(1), '\n#Auptimizer: 1')
})





test_that("auptimizer input format", {
  a <- 2
  b <- TRUE
  expect_equal(a, 2)
  get_config("test_io.json", environment())
  expect_equal(b, FALSE)
  expect_equal(a, 1)
})