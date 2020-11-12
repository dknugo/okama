import pandas as pd
from pandas.testing import assert_series_equal
import numpy as np
from numpy.testing import assert_array_equal
import pytest
from pytest import approx
from pytest import mark
from okama.assets import Portfolio, AssetList


@mark.asset
@mark.usefixtures('_init_asset')
class TestAsset:

    @mark.smoke
    def test_get_symbol_data(self):
        assert self.spy.name == 'SPDR S&P 500 ETF Trust'
        assert self.spy.country == 'USA'
        assert self.spy.currency == 'USD'
        assert self.spy.type == 'ETF'
        assert self.spy.inflation == 'USD.INFL'
        assert self.spy.first_date == pd.to_datetime('1993-02')

    def test_price(self):
        assert type(self.spy.price) == float

    def test_dividends(self):
        assert self.spy.dividends['2019'].sum() == 5.6183

    def test_nav_ts(self):
        assert self.otkr.nav_ts[0] == 101820352.18


@mark.asset_list
def test_asset_list_init_failing():
    with pytest.raises(Exception, match=r'Symbols should be a list of string values.'):
        AssetList(symbols=('RUB.FOREX', 'MCFTR.INDX'))


@mark.asset_list
@mark.usefixtures('_init_asset_list')
class TestAssetList:

    def test_currencies(self):
        assert self.currencies.period_length == 1.
        assert self.currencies.first_date == pd.to_datetime('2019-01')
        assert self.currencies.currencies == \
               {'RUBUSD.FOREX': 'USD', 'EURUSD.FOREX': 'USD', 'CNYUSD.FOREX': 'USD', 'asset list': 'USD'}
        assert self.currencies.names == {'RUBUSD.FOREX': 'RUBUSD', 'EURUSD.FOREX': 'EURUSD', 'CNYUSD.FOREX': 'CNYUSD'}
        assert self.currencies.describe().iloc[1, -1] == approx(0.02485059471387574, rel=1e-2)

    @mark.smoke
    def test_make_asset_list(self):
        assert self.asset_list.last_date == pd.to_datetime('2020-01')
        assert list(self.asset_list.ror) == ['RUB.FOREX', 'MCFTR.INDX']

    def test_calculate_wealth_indexes(self):
        assert self.asset_list.wealth_indexes.sum(axis=1)[-1] == \
               approx(3339.677963676333, rel=1e-2)  # last month indexes sum

    def test_risk(self):
        assert self.asset_list.risk_monthly.sum() == approx(0.0521775818338418, rel=1e-2)
        assert self.asset_list.risk_annual.sum() == approx(0.20460447233157303, rel=1e-2)

    def test_semideviation(self):
        assert self.asset_list.semideviation.sum() == approx(0.01561429133038064, rel=1e-2)

    def test_get_var(self):
        assert self.asset_list.get_var_historic(level=5).sum() == approx(0.04660186150371443, rel=1e-2)

    def test_get_cvar(self):
        assert self.asset_list.get_cvar_historic(level=5).sum() == approx(0.06586521994497807, rel=1e-2)

    def test_drawdowns(self):
        assert self.asset_list.drawdowns.min().sum() == approx(-0.08293560490704811, rel=1e-2)

    testdata = [
        ('YTD', 0.0340965755805116, 0.04050306772244683),
        (1, 0.29095332822955333, 0.2975877999271892),
        (None, 0.30814669684220186, 0.16174551168647278),
    ]

    @mark.parametrize("input_data,expected1,expected2", testdata, ids=["YTD", "1 year", "full period"])
    def test_get_cagr(self, input_data, expected1, expected2):
        assert self.asset_list.get_cagr(period=input_data).sum() == approx(expected1, rel=1e-2)
        assert self.real_estate.get_cagr(period=input_data).sum() == approx(expected2, rel=1e-2)

    def test_mean_return(self):
        assert self.asset_list.mean_return.sum() == approx(0.31657677165833564, rel=1e-2)

    def test_real_return(self):
        assert self.asset_list.real_mean_return.sum() == approx(0.11205444958570421, rel=1e-2)

    def test_annual_return_ts(self):
        assert self.asset_list.annual_return_ts.iloc[-1, :].sum() == approx(0.030096575580511598, rel=1e-2)

    def test_describe(self):
        description = self.asset_list.describe(tickers=False)
        assert list(description.columns) == ['property', 'period', 'MOEX Total Return', 'RUB', 'inflation']
        assert description.loc[0, 'RUB'] == approx(0.01825680026233445, rel=1e-2)
        assert description.loc[0, 'inflation'] == approx(0.0040000000000000036, rel=1e-2)

    def test_dividend_yield(self):
        assert list(self.spy.names.values()) == ['SPDR S&P 500 ETF Trust']
        assert self.spy.dividend_yield.iloc[-1, 0] == approx(0.012541968545679447, rel=1e-2)
        assert self.asset_list.dividend_yield.iloc[:, 0].sum() == 0

    def test_dividends_annual(self):
        assert self.spy.dividends_annual.iloc[-2, 0] == approx(1.4194999999999998, rel=1e-2)
        assert self.asset_list.dividends_annual.iloc[:, 0].sum() == 0

    def test_growing_dividend_years(self):
        assert self.spy.dividend_growing_years.iloc[-1, 0] == 0

    def test_paying_dividend_years(self):
        assert self.spy.dividend_paying_years.iloc[-2, 0] == 2

@mark.portfolio
def test_init_portfolio_failing():
    with pytest.raises(Exception, match=r'Number of tickers \(2\) should be equal to the weights number \(3\)'):
        Portfolio(symbols=['RUB.FOREX', 'MCFTR.INDX'], weights=[0.1, 0.2, 0.7]).symbols
    with pytest.raises(Exception, match='Weights sum is not equal to one.'):
        Portfolio(symbols=['RUB.FOREX', 'MCFTR.INDX'], weights=[0.1, 0.2]).symbols
    # with pytest.raises(Exception, match=r'RUB is not in allowed assets namespaces*'):
    #     Portfolio(symbols=['RUB.RUB'], weights=[1])
    # # with pytest.raises(Exception):
    # #     Portfolio(symbols=['XXXX.RE'], weights=[1])


@mark.portfolio
@mark.usefixtures('_init_portfolio')
class TestPortfolio:

    def test_weights(self):
        assert self.portfolio.weights == [0.5, 0.5]

    def test_mean_return(self):
        assert self.portfolio.mean_return_monthly == approx(0.010855399342030503, rel=1e-2)
        assert self.portfolio.mean_return_annual == approx(0.13833062987252154, rel=1e-2)

    def test_real_mean_return(self):
        assert self.portfolio.real_mean_return == approx(0.05233240453358268, rel=1e-2)

    def test_real_cagr(self):
        assert self.portfolio.real_cagr == approx(0.04515917172982675, rel=1e-2)
        with pytest.raises(Exception, match="Real Return is not defined. Set inflation=True to calculate."):
            self.portfolio_no_inflation.real_cagr

    def test_dividend_yield(self):
        assert self.portfolio.dividend_yield.iloc[-1, :].sum() == 0

    def test_risk(self):
        assert self.portfolio.risk_monthly == approx(0.03571707423375908, rel=1e-2)
        assert self.portfolio.risk_annual == approx(0.1398099289724462, rel=1e-2)

    def test_rebalanced_portfolio_return(self):
        assert self.portfolio.get_rebalanced_portfolio_return_ts().mean() == approx(0.01122171623373367, rel=1e-2)
        assert self.portfolio.get_rebalanced_portfolio_return_ts(period='N').mean() == \
               approx(0.01221789515271935, rel=1e-2)

    def test_cagr(self):
        values = pd.Series({'portfolio': 0.1303615092603554, 'RUB.INFL': 0.05548082428015655})
        assert_series_equal(self.portfolio.cagr, values, rtol=1e-4)

    def test_describe(self):
        description = self.portfolio.describe()
        assert list(description.columns) == ['property', 'rebalancing', 'period', 'portfolio', 'inflation']
        assert description.loc[0, 'portfolio'] == approx(0.015048287790255799, rel=1e-2)
        assert description.loc[0, 'inflation'] == approx(0.0040000000000000036, rel=1e-2)

    def test_forecast_from_history(self):
        assert self.portfolio.forecast_from_history().iloc[-1, :].sum() == approx(0.2844073190898566, rel=1e-2)
        with pytest.raises(Exception, match="Time series does not have enough history to forecast. "
                                            "Period length is 0.90 years. At least 2 years are required."):
            self.portfolio_short_history.forecast_from_history()

    def test_table(self):
        assert_array_equal(self.portfolio.table['ticker'].values, np.array(['RUB.FOREX', 'MCFTR.INDX']))

    def test_get_rolling_return(self):
        assert self.portfolio.get_rolling_return(years=1).iloc[-1] == approx(0.1226961060060261, rel=1e-2)

    def test_forecast_monte_carlo_norm_wealth_indexes(self):
        assert self.portfolio.forecast_monte_carlo_norm_wealth_indexes(years=1, n=1000).iloc[-1, :].mean() == approx(2121, rel=1e-1)

    def test_forecast_monte_carlo_percentile_wealth_indexes(self):
        dic = self.portfolio.forecast_monte_carlo_percentile_wealth_indexes(years=1, n=100, percentiles=[50])
        assert dic[50] == approx(2121, rel=1e-1)