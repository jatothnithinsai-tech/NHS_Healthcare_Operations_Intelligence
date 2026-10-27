"""Clearly synthetic fixtures test controlled edge cases, not business findings."""
import numpy as np
import pandas as pd
import pytest
from src.cleaning.numeric import numeric, strict_sum
from src.statistics.analysis import block_indices, chronological_baselines
from src.validation.checks import validate_frame
from src.ingestion.acquire import infer_month


@pytest.mark.parametrize('token',['',':','-','..','*','x','NA'])
def test_suppression_is_missing(token):
    assert pd.isna(numeric(pd.DataFrame({'n':[token]})).iloc[0,0])


def test_numeric_zero_is_zero():
    assert numeric(pd.DataFrame({'n':['0']})).iloc[0,0]==0


@pytest.mark.parametrize('token',['-1','patient123','1.5'])
def test_invalid_counts_fail(token):
    with pytest.raises((ValueError,TypeError)):
        numeric(pd.DataFrame({'n':[token]}))


def test_suppressed_component_prevents_partial_sum():
    assert pd.isna(strict_sum(pd.DataFrame({'a':pd.Series([1],dtype='Int64'),'b':pd.Series([None],dtype='Int64')}),['a','b']).iloc[0])


@pytest.mark.parametrize('text,domain,expected',[
    ('Full CSV data file Aug26','rtt','2026-08-01'),
    ('Monthly A&E September 2026 revised 14.05.27','ae','2026-09-01'),
    ('DM01-MARCH-2025-full-extract.zip','diagnostics','2025-03-01')])
def test_reporting_month_is_not_revision_month(text,domain,expected):
    assert infer_month(text,domain)==expected


def test_unknown_month_rejected():
    with pytest.raises(ValueError):
        infer_month('latest','ae')


def test_duplicate_grain_rejected():
    f=pd.DataFrame({'month':['2026-01-01']*2,'provider_code':['R1H']*2})
    with pytest.raises(ValueError,match='Duplicate'):
        validate_frame(f,'ae')


def test_invalid_provider_rejected():
    with pytest.raises(ValueError,match='provider'):
        validate_frame(pd.DataFrame({'month':['2026-01-01'],'provider_code':['not a code']}),'ae')


def test_block_sampling_reproducible_and_bounded():
    a=block_indices(23,3,np.random.default_rng(7))
    b=block_indices(23,3,np.random.default_rng(7))
    assert np.array_equal(a,b) and len(a)==23 and a.min()>=0 and a.max()<23


def test_chronological_baselines_have_no_future_leakage():
    result=chronological_baselines(np.arange(24,dtype=float))
    assert result['origins']==12
    assert result['persistence_mae']==1
    assert result['seasonal_naive_mae']==12
    assert result['predictions'][0]=={'index':12,'actual':12.,'persistence':11.,'seasonal_naive':0.}


def test_short_history_rejected():
    with pytest.raises(ValueError):
        chronological_baselines(np.arange(12))
