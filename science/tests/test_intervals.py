import pytest
from luna_ready.intervals import sampled_intervals
T=[f'2026-11-15T0{i}:00:00Z' for i in range(5)]

def test_censoring_and_transition_brackets():
    r=sampled_intervals(T,[True,True,False,True,True])
    assert len(r)==2
    assert r[0]['left_censored'] and not r[0]['right_censored']
    assert r[0]['end_transition_bracket_utc']==[T[1],T[2]]
    assert r[1]['right_censored'] and not r[1]['left_censored']

def test_unknown_splits_runs_without_inventing_transition():
    r=sampled_intervals(T,[False,True,None,True,False])
    assert len(r)==2 and r[0]['right_censored'] and r[1]['left_censored']
    assert r[0]['end_transition_bracket_utc'] is None

def test_all_visible_and_no_outage():
    assert sampled_intervals(T,[True]*5,False)==[]
    r=sampled_intervals(T,[True]*5)
    assert r[0]['sample_span_hours']==4
    assert r[0]['left_censored'] and r[0]['right_censored']
