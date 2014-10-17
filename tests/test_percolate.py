#!/usr/bin/env python
# encoding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import (ascii, bytes, chr, dict, filter, hex, input,
                             int, map, next, oct, open, pow, range, round,
                             str, super, zip)

import pytest
import inspect
import percolate
import numpy as np


def _test_existence(module, function):
    return hasattr(module, function)


def _test_signature(function, params):
    try:  # python 3
        args = inspect.signature(function).parameters
    except:  # python 2
        args = inspect.getargspec(function).args

    for param in params:
        assert param in args


def test_sample_state_existence():
    assert _test_existence(percolate, 'sample_states')


def test_sample_state_signature():
    _test_signature(
        percolate.sample_states,
        ['graph', 'spanning_cluster', 'model']
    )


@pytest.fixture
def empty_graph():
    import networkx

    return networkx.Graph()


@pytest.fixture(params=[True, False])
def grid_3x3_graph(request):
    import networkx

    ret = networkx.Graph()
    ret.add_nodes_from(range(9))
    ret.add_edges_from([
        (i, i + j) for i in [1, 4, 7] for j in [-1, 1]
    ])
    ret.add_edges_from([
        (i, i + j) for i in [3, 4, 5] for j in [-3, 3]
    ])

    if request.param:
        ret.add_nodes_from(range(9, 12), span=0)
        ret.add_nodes_from(range(12, 15), span=1)
        ret.add_edges_from(
            [(0, 9), (3, 10), (6, 11)], span=0
        )
        ret.add_edges_from(
            [(2, 12), (5, 13), (8, 14)], span=1
        )

    ret.graph['span'] = request.param
    return ret

def test_sample_state_not_implemented_model(empty_graph):
    with pytest.raises(ValueError):
        next(percolate.sample_states(empty_graph, model='site'))


def test_sample_state_no_auxiliary_nodes(empty_graph):
    with pytest.raises(ValueError):
        next(percolate.sample_states(empty_graph, spanning_cluster=True))


def test_sample_state_one_sided_auxiliary_nodes(empty_graph):
    empty_graph.add_node(1, span=0)
    with pytest.raises(ValueError):
        next(percolate.sample_states(empty_graph, spanning_cluster=True))


def test_initial_iteration(grid_3x3_graph):

    spanning_cluster = grid_3x3_graph.graph['span']

    ret = next(percolate.sample_states(
        grid_3x3_graph, spanning_cluster=spanning_cluster
    ))

    assert ret['n'] == 0
    assert ret['max_cluster_size'] == 1
    assert np.array_equal(
        ret['moments'], np.ones(5, dtype=int) * 8
    )

    assert ('has_spanning_cluster' in ret) == spanning_cluster

    if spanning_cluster:
        assert not ret['has_spanning_cluster']


@pytest.fixture
def state_it(grid_3x3_graph):
    spanning_cluster = grid_3x3_graph.graph['span']
    ret = percolate.sample_states(
        grid_3x3_graph, spanning_cluster=spanning_cluster
    )
    return ret, spanning_cluster


def test_number_of_iterations(state_it):

    n = 0

    for state in state_it[0]:
        assert state['n'] == n
        n += 1

    assert state['n'] == 12


# TEST CASE:
# 3 x 3 grid with edge indices
#
#  . 10  . 11  .
#  6     8     9
#  .  5  .  7  .
#  1     3     4
#  .  0  .  2  .
#
# The edge permutation is
# [10, 9, 0, 8, 5, 2, 1, 11, 4, 7, 3, 6]

def test_max_cluster_size(state_it):

    np.random.seed(42)

    max_cluster_sizes = [
        1, 2, 2, 2, 3, 4, 4, 7, 9, 9, 9, 9, 9
    ]

    for state in state_it[0]:
        assert state['max_cluster_size'] == max_cluster_sizes[state['n']]


def test_moments(state_it):

    np.random.seed(42)

    moments = np.array([
        [8, 8, 8, 8, 8],     # n == 0
        [7, 7, 7, 7, 7],     # n == 1
        [6, 7, 9, 13, 21],
        [5, 7, 11, 19, 35],
        [4, 6, 10, 18, 34],
        [3, 5, 9, 17, 33],
        [2, 5, 13, 35, 97],
        [1, 2, 4, 8, 16],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])

    for state in state_it[0]:
        assert np.array_equal(moments[state['n']], state['moments'])


def test_spanning(state_it):

    if not state_it[1]:
        return

    np.random.seed(42)

    has_spanning_cluster = 6 * [False, ] + 7 * [True, ]

    for state in state_it[0]:
        assert (
            state['has_spanning_cluster'] == has_spanning_cluster[state['n']]
        )