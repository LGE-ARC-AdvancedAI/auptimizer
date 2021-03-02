# Auptimizer Dashboard

## Launching the dashboard together with an experiment

The dashboard can be launched with ``aup`` using `--launch-dashboard`

`python -m aup Examples/2dfunc_diff_res/exp_cpu.json --launch_dashboard`

You can specify the port for the dashboard with `--dashboard-port`, otherwise,
the first available port will be used and printed to the console when running
the experiment.

## Seeing HTTP requests from the frontend

The HTTP requests are all saved in `./src/aup/dashboard/frontend/febuild/auptimizer-dashboard/dashboard_logs`
