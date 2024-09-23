# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import jax.numpy as jnp

# import numpy as np
from sklearn.linear_model import QuantileRegressor as SklearnQuantileRegressor
from sklearn.metrics import mean_squared_error

import spu.spu_pb2 as spu_pb2  # type: ignore
import spu.utils.simulation as spsim
from sml.linear_model.quantile import QuantileRegressor as SmlQuantileRegressor


class UnitTests(unittest.TestCase):
    def test_forest(self):
        def proc_wrapper(
            quantile,
            alpha,
            fit_intercept,
            lr,
            max_iter,
        ):
            quantile_custom = SmlQuantileRegressor(
                quantile=quantile,
                alpha=alpha,
                fit_intercept=fit_intercept,
                lr=lr,
                max_iter=max_iter,
            )

            def proc(X, y):
                quantile_custom_fit = quantile_custom.fit(X, y)
                result = quantile_custom_fit.predict(X)
                return result, quantile_custom_fit.coef_, quantile_custom_fit.intercept_

            return proc

        n_samples, n_features = 100, 2

        def generate_data():
            from jax import random

            # 设置随机种子
            key = random.PRNGKey(42)
            # 生成 X 数据
            key, subkey = random.split(key)
            X = random.normal(subkey, (100, 2))
            # 生成 y 数据
            y = (
                5 * X[:, 0] + 2 * X[:, 1] + random.normal(key, (100,)) * 0.1
            )  # 高相关性，带有小噪声
            return X, y

        # bandwidth and latency only work for docker mode
        sim = spsim.Simulator.simple(
            3, spu_pb2.ProtocolKind.ABY3, spu_pb2.FieldType.FM64
        )

        # X, y, coef, sample_weight = generate_data()
        X, y = generate_data()

        # compare with sklearn
        quantile_sklearn = SklearnQuantileRegressor(
            quantile=0.5, alpha=0.1, fit_intercept=True, solver='revised simplex'
        )
        quantile_sklearn_fit = quantile_sklearn.fit(X, y)
        # acc_sklearn = jnp.mean(jnp.square(y - quantile_sklearn_fit.predict(X)))
        acc_sklearn = mean_squared_error(
            y, quantile_sklearn_fit.predict(X), squared=False
        )
        print(f"Accuracy in SKlearn: {acc_sklearn:.2f}")
        print(quantile_sklearn_fit.coef_)
        print(quantile_sklearn_fit.intercept_)

        # run
        proc = proc_wrapper(
            quantile=0.5, alpha=0.1, fit_intercept=True, lr=0.01, max_iter=2
        )

        spu_f = spsim.sim_jax(sim, proc)
        result, coef, intercept = spu_f(X, y)
        # print(spu_f.pphlo)
        # result, coef, intercept = proc(X, y)
        acc_custom = mean_squared_error(y, result, squared=False)

        # print acc

        print(f"Accuracy in SPU: {acc_custom:.2f}")
        print(coef)
        print(intercept)


if __name__ == "__main__":
    unittest.main()
