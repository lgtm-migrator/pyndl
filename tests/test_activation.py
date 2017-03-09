import time
import gc

import numpy as np
import xarray as xr

import pytest

from pyndl.activation import activation

slow = pytest.mark.skipif(not pytest.config.getoption("--runslow"),
                          reason="need --runslow option to run")


def test_activation_matrix():
    weights = xr.DataArray(np.array([[0, 1], [1, 0], [0, 0]]),
                           coords={
                               'cues': ['c1', 'c2', 'c3']
                           },
                           dims=('cues', 'outcomes'))
    events = [(['c1', 'c2', 'c3'], []),
              (['c1', 'c3'], []),
              (['c2'], []),
              (['c1', 'c1'], [])]
    reference_activations = np.array([[1, 1], [0, 1], [1, 0], [0, 1]])

    with pytest.raises(ValueError):
        activations = activation(events, weights, number_of_threads=1)

    activations = activation(events, weights, number_of_threads=1, remove_duplicates=True)
    activations_mp = activation(events, weights, number_of_threads=3, remove_duplicates=True)

    assert np.allclose(reference_activations, activations)
    assert np.allclose(reference_activations, activations_mp)


@slow
def test_activation_matrix_large():
    """Test with a lot of data. Better run only with at least 12GB free RAM.
    """
    print("Start setup...")

    def time_test(func, of=""):
        def dec_func(*args, **kwargs):
            print("Start {}".format(of))
            st = time.clock()
            res = func(*args, **kwargs)
            et = time.clock()
            print("Finished {}".format(of))
            print("Timediff: {}s".format(et-st))
            return res
        return dec_func

    n_cues = 50000
    n_outcomes = 5000
    n_events = 50000
    huge_weights = np.random.rand(n_cues, n_outcomes)
    huge_cues = ['c'+str(i) for i in range(n_cues)]
    huge_event_cues = ['c'+str(i) for i in range(n_cues-30, n_cues)]
    huge_events_cues = [huge_event_cues for i in range(n_events)]

    print("Estimated best case memory consumption: {} bytes".format(n_cues * n_outcomes * 8 +
                                                                    n_events * n_outcomes * 8 * 2))

    print("Start test...")
    gc.collect()
    asp, ncsp = time_test(activation_matrix,
                          of="single threaded")(huge_events_cues, huge_weights, huge_cues, numThreads=1)
    gc.collect()
    amp, ncmp = time_test(activation_matrix,
                          of="multi threaded (8 threads)")(huge_events_cues, huge_weights, huge_cues, numThreads=8)
    del huge_weights
    del huge_events_cues
    gc.collect()
    print("Compare results...")
    assert np.allclose(asp, amp), "single and multi threaded had different results"
