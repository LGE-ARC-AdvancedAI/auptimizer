import scipy
import logging
import numpy as np
import time

from scipy import optimize

logger = logging.getLogger(__name__)


def vap(x, a, b, c):
    return np.exp(a+b/x+c*np.log(x))

def pow3(x, c, a, alpha):
    return c - a * x**(-alpha)

def linear(x, a, b):
    return a*x + b

def logx_linear(x, a, b):
    x = np.log(x)
    return a*x + b

def dr_hill_zero_background(x, theta, eta, kappa):
    return (theta * x**eta) / (kappa**eta + x**eta)

def log_power(x, a, b, c):
    return a/(1.+(x/np.exp(b))**c)

def pow4(x, alpha, a, b, c):
    return c - (a*x+b)**-alpha

def mmf(x, alpha, beta, kappa, delta):
    return alpha - (alpha - beta) / (1. + (kappa * x)**delta)

def exp4(x, c, a, b, alpha):
    return c - np.exp(-a*(x**alpha)+b)

def ilog2(x, c, a):
    return c - a / np.log(x)

def weibull(x, alpha, beta, kappa, delta):
    return alpha - (alpha - beta) * np.exp(-(kappa * x)**delta)

def janoschek(x, a, beta, k, delta):
    return a - (a - beta) * np.exp(-k*x**delta)

CURVE_FIT_FUNCS = {
    "vap": vap,
    "pow3": pow3,
    "linear": linear,
    "logx_linear": logx_linear,
    "dr_hill_zero_background": dr_hill_zero_background,
    "log_power": log_power,
    "pow4": pow4,
    "mmf": mmf,
    "exp4": exp4,
    "ilog2": ilog2,
    "weibull": weibull,
    "janoschek": janoschek,
}


class CurveModel:
    LEAST_FITTED_FUNCTION = 4
    NUM_INSTANCE = 10
    STEP_SIZE = 0.0005

    def __init__(self, iterations):
        self.iterations = iterations

    def fit_theta(self):
        x = range(1, self.step + 1)
        y = self.interm_res
        func_params = {}
        for func_name, func in CURVE_FIT_FUNCS.items():
            try:
                params = scipy.optimize.curve_fit(func, x, y)[0]
                func_params[func_name] = params
            except RuntimeError:
                pass
            except (FloatingPointError, OverflowError, ZeroDivisionError) as exception:
                logger.warning("Mathematical error encountered in fit_theta: {}".format(exception))
            except Exception as exception:
                logger.critical("Exceptions in fit_theta: {}".format(exception))
                raise exception
        return func_params

    def filter_curve(self, func_params):
        standard = self.step * np.mean(self.interm_res) ** 2
        predict_data = []
        funcs = {}
        for func_name, func in CURVE_FIT_FUNCS.items():
            if func_name not in func_params:
                continue
            var = 0
            for idx in range(1, self.step+1):
                y = func(idx, *func_params[func_name])
                var += (y - self.interm_res[idx-1]) ** 2
            if var < standard:
                predict_data += [y]
                funcs[func_name] = func
        final_funcs = {}
        median = np.median(predict_data)
        stddev = np.std(predict_data)
        for func_name, func in funcs.items():
            y = func(self.iterations, *func_params[func_name])
            epsilon = self.step / 10 * stddev
            if y < median + epsilon and y > median - epsilon:
                final_funcs[func_name] = func
        return final_funcs

    def normalize_weights(self, samples, num_funcs):
        for i in range(CurveModel.NUM_INSTANCE):
            total = 0
            for j in range(num_funcs):
                total += samples[i][j]
            for j in range(num_funcs):
                samples[i][j] /= total
        return samples
    
    def f_comb(self, pos, sample, funcs, func_params):
        ret = 0
        for idx, (func_name, func) in enumerate(funcs.items()):
            y = func(pos, *func_params[func_name])
            ret += sample[idx] * y
        return ret
    
    def sigma_sq(self, sample, funcs, func_params):
        ret = 0
        for i in range(1, self.step + 1):
            temp = self.interm_res[i - 1] - self.f_comb(i, sample, funcs, func_params)
            ret += temp * temp
        return 1.0 * ret / self.step

    def normal_distribution(self, pos, sample, funcs, func_params):
        curr_sigma_sq = self.sigma_sq(sample, funcs, func_params)
        delta = self.interm_res[pos-1] - self.f_comb(pos, sample, funcs, func_params)
        return np.exp(np.square(delta) / (-2.0 * curr_sigma_sq)) / np.sqrt(2 * np.pi * np.sqrt(curr_sigma_sq))

    def likelihood(self, samples, funcs, func_params):
        ret = np.ones(CurveModel.NUM_INSTANCE)
        for i in range(CurveModel.NUM_INSTANCE):
            for j in range(1, self.step + 1):
                ret[i] *= self.normal_distribution(j, samples[i], funcs, func_params)
        return ret
    
    def prior(self, samples, funcs, func_params):
        ret = np.ones(CurveModel.NUM_INSTANCE)
        for i in range(CurveModel.NUM_INSTANCE):
            for j in range(len(funcs)):
                if not samples[i][j] > 0:
                    ret[i] = 0
            if self.f_comb(1, samples[i], funcs, func_params) >= self.f_comb(self.iterations, samples[i], funcs, func_params):
                ret[i] = 0
        return ret

    def target_distribution(self, samples, funcs, func_params):
        curr_likelihood = self.likelihood(samples, funcs, func_params)
        curr_prior = self.prior(samples, funcs, func_params)
        ret = np.ones(CurveModel.NUM_INSTANCE)
        for i in range(CurveModel.NUM_INSTANCE):
            ret[i] = curr_likelihood[i] * curr_prior[i]
        return ret

    def mcmc_sampling(self, filtered_funcs, func_params, timeout):
        t0 = time.time()
        init_weight = np.ones((len(filtered_funcs),), dtype=np.float32) / len(filtered_funcs)
        weights_samples = np.broadcast_to(init_weight, (CurveModel.NUM_INSTANCE, len(filtered_funcs)))
        while True:
            new_values = np.random.randn(CurveModel.NUM_INSTANCE, len(filtered_funcs)) * CurveModel.STEP_SIZE + weights_samples
            new_values = self.normalize_weights(new_values, len(filtered_funcs))
            alpha = np.minimum(1, self.target_distribution(new_values, filtered_funcs, func_params) / self.target_distribution(weights_samples, filtered_funcs, func_params))
            u = np.random.rand(CurveModel.NUM_INSTANCE)
            change_value_flag = (u < alpha).astype(np.int)
            for idx in range(CurveModel.NUM_INSTANCE):
                new_values[idx] = weights_samples[idx] * (1 - change_value_flag[idx]) + new_values[idx] * change_value_flag[idx]
            weights_samples = new_values
            if time.time() - t0 > timeout:
                break
        return weights_samples

    def predict(self, interm_res, timeout):
        self.interm_res = interm_res
        self.step = len(interm_res)
        func_params = self.fit_theta()
        filtered_funcs = self.filter_curve(func_params)
        final_keys = set(func_params.keys()) & set(filtered_funcs.keys())
        filtered_funcs = {func_name: filtered_funcs[func_name] for func_name in final_keys}
        func_params = {func_name: func_params[func_name] for func_name in final_keys}
        if len(filtered_funcs) < CurveModel.LEAST_FITTED_FUNCTION:
            return None
        weights_samples = self.mcmc_sampling(filtered_funcs, func_params, timeout)
        f_res = [self.f_comb(self.iterations, weight_sample, filtered_funcs, func_params) for weight_sample in weights_samples]
        return np.mean(f_res) 

