from crank_nicholson import crank_nicholson
import numpy as np
from math import log, exp, sqrt
from scipy.stats import norm
import scipy

from distutils.version import LooseVersion

if LooseVersion(scipy.__version__)>=LooseVersion("0.18.0"):
    have_CubicSpline = True
    from scipy.interpolate import CubicSpline
else:
    have_CubicSpline = False
    from scipy.interpolate import spline


def priceOptionBS(term, vol, rate, spot, strike, put=False):
    fwd = spot * exp(rate*term)
    d1 = (log(fwd/strike)+0.5*vol*vol*term)/(vol*sqrt(term))
    d2 = d1-vol*sqrt(term)
    if put:
        price = norm.cdf(-d2)*strike*exp(-rate*term) - norm.cdf(-d1)*spot
        itm_prob = norm.cdf(-d2)
    else:
        price = norm.cdf(d1)*spot - norm.cdf(d2)*strike*exp(-rate*term)
        itm_prob = norm.cdf(d2)
    return price, itm_prob

def priceEuropeanWithPDE(spot,payoff,gridCentre,stdDevs,term,vol,rate,
                         do_discounting=True):
    nx=100
    nt=100
    centralLogSpot=log(gridCentre)
    sd=vol*sqrt(term)
    minGridLogSpot=centralLogSpot-sd*stdDevs
    maxGridLogSpot=centralLogSpot+sd*stdDevs
    logGrid = np.linspace(minGridLogSpot,maxGridLogSpot,nx)
    payoff_values=payoff(np.exp(logGrid))
    growth = lambda v: (-rate if do_discounting else 0)*v

    time_0_vals = crank_nicholson(payoff_values,
                                  maxGridLogSpot-minGridLogSpot,
                                  term,
                                  nt,
                                  0.5*vol*vol,
                                  rate-0.5*vol*vol,
                                  growth
                                  )
    if have_CubicSpline:
        val = CubicSpline(logGrid,time_0_vals)(log(spot)).item()
    else:
        val = spline(xk=logGrid,yk=time_0_vals,xnew=log(spot)).item()
    return val

if __name__=="__main__":
    vol=0.12
    term = 4
    rate=0.01
    spot=100
    strike=99
    put=True

    print(priceOptionBS(term,vol,rate,spot,strike,put))

    payoff = lambda x: np.maximum(0,strike-x if put else x-strike)
    #payoff = lambda x : np.ones_like(x)
    pde_val = priceEuropeanWithPDE(spot, payoff,
                                   strike,4,term,vol, rate)
    itm_payoff = lambda x:(strike>x if put else x>strike)
    itm_prob = priceEuropeanWithPDE(spot, itm_payoff,
                                    strike,4,term,vol, rate, False)

    print((pde_val, itm_prob))

                          
