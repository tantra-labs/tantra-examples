"""Black-Scholes analytical pricing and option Greeks (mirrors ``honba_tamashii::analytics::greeks``, gap 0006).

Decimal-canonical (ex 0006): every price, strike, volatility, rate and Greek is an
exact ``decimal.Decimal``. The normal CDF uses a portable Decimal erf approximation
(Abramowitz & Stegun 7.1.26, max abs error ~1.5e-7) instead of ``math.erf``, so the
whole pricing path stays float-free under the zero-floats policy.
"""
# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tantra_examples._kernel.option import OptionKind

__all__ = ["Greeks", "bs_greeks", "bs_price", "implied_volatility"]

_SQRT_2 = Decimal(2).sqrt()
_INV_SQRT_2PI = Decimal(1) / (Decimal(2) * _SQRT_2)

# Abramowitz & Stegun 7.1.26 coefficients: erf(x) ~= 1 - t*(a1 + t*(a2 + t*(a3 + t*(a4 + t*a5)))) * exp(-x^2),
# t = 1/(1 + p*x), p = 0.3275911.
_ERF_P = Decimal("0.3275911")
_ERF_COEFS = (
    Decimal("0.254829592"),
    Decimal("-0.284496736"),
    Decimal("1.421413741"),
    Decimal("-1.453152027"),
    Decimal("1.061405429"),
)


def _erf(x: Decimal) -> Decimal:
    """Portable Decimal error function via A&S 7.1.26 (exact Decimal arithmetic)."""
    if x < 0:
        return -_erf(-x)
    t = Decimal(1) / (Decimal(1) + _ERF_P * x)
    poly = _ERF_COEFS[0] + t * (
        _ERF_COEFS[1] + t * (_ERF_COEFS[2] + t * (_ERF_COEFS[3] + t * _ERF_COEFS[4]))
    )
    return Decimal(1) - (t * poly) * (-(x * x)).exp()


def _norm_cdf(x: Decimal) -> Decimal:
    return Decimal("0.5") * (Decimal(1) + _erf(x / _SQRT_2))


def _norm_pdf(x: Decimal) -> Decimal:
    return _INV_SQRT_2PI * (-Decimal("0.5") * x * x).exp()


def _to_dec(value: Decimal | int | str) -> Decimal:
    """Coerce a numeric operand to an exact ``Decimal`` (wheel ``to_decimal`` semantics)."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


@dataclass(frozen=True, slots=True)
class Greeks:
    """Option Greeks and theoretical price."""

    price: Decimal
    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Decimal

    def __getitem__(self, key: str) -> Decimal:
        return getattr(self, key)


def bs_price(
    kind: OptionKind,
    spot: Decimal,
    strike: Decimal,
    tau: Decimal,
    iv: Decimal,
    r: Decimal = Decimal("0.07"),
) -> Decimal:
    """Black-Scholes theoretical price for European option."""
    spot, strike, tau, iv, r = (_to_dec(v) for v in (spot, strike, tau, iv, r))
    if tau <= 0 or iv <= 0:
        if kind == OptionKind.CALL:
            return max(Decimal(0), spot - strike)
        return max(Decimal(0), strike - spot)

    sigma_sqrt_tau = iv * tau.sqrt()
    d1 = ((spot / strike).ln() + (r + Decimal("0.5") * iv * iv) * tau) / sigma_sqrt_tau
    d2 = d1 - sigma_sqrt_tau

    discount = (-r * tau).exp()
    if kind == OptionKind.CALL:
        return spot * _norm_cdf(d1) - strike * discount * _norm_cdf(d2)
    return strike * discount * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def bs_greeks(
    kind: OptionKind,
    spot: Decimal,
    strike: Decimal,
    tau: Decimal,
    iv: Decimal,
    r: Decimal = Decimal("0.07"),
) -> Greeks:
    """Compute analytical Black-Scholes Greeks."""
    spot, strike, tau, iv, r = (_to_dec(v) for v in (spot, strike, tau, iv, r))
    price = bs_price(kind, spot, strike, tau, iv, r)
    if tau <= 0 or iv <= 0:
        delta = Decimal(1) if (kind == OptionKind.CALL and spot >= strike) else Decimal(0)
        if kind == OptionKind.PUT:
            delta = Decimal(-1) if spot <= strike else Decimal(0)
        return Greeks(
            price=price,
            delta=delta,
            gamma=Decimal(0),
            theta=Decimal(0),
            vega=Decimal(0),
            rho=Decimal(0),
        )

    sigma_sqrt_tau = iv * tau.sqrt()
    d1 = ((spot / strike).ln() + (r + Decimal("0.5") * iv * iv) * tau) / sigma_sqrt_tau
    d2 = d1 - sigma_sqrt_tau

    pdf_d1 = _norm_pdf(d1)
    discount = (-r * tau).exp()

    if kind == OptionKind.CALL:
        delta = _norm_cdf(d1)
        theta = -(spot * pdf_d1 * iv) / (
            Decimal(2) * tau.sqrt()
        ) - r * strike * discount * _norm_cdf(d2)
        rho = strike * tau * discount * _norm_cdf(d2)
    else:
        delta = _norm_cdf(d1) - Decimal(1)
        theta = -(spot * pdf_d1 * iv) / (
            Decimal(2) * tau.sqrt()
        ) + r * strike * discount * _norm_cdf(-d2)
        rho = -strike * tau * discount * _norm_cdf(-d2)

    gamma = pdf_d1 / (spot * sigma_sqrt_tau)
    vega = spot * pdf_d1 * tau.sqrt()

    return Greeks(
        price=price,
        delta=delta,
        gamma=gamma,
        theta=theta / Decimal(365),  # daily theta convention
        vega=vega / Decimal(100),  # per 1% vol convention
        rho=rho / Decimal(100),
    )


def implied_volatility(
    price: Decimal,
    spot: Decimal,
    strike: Decimal,
    tau: Decimal,
    r: Decimal = Decimal("0.07"),
    kind: OptionKind = OptionKind.CALL,
    tol: Decimal = Decimal("1e-5"),
    max_iter: int = 100,
) -> Decimal | None:
    """Solve for implied volatility via Newton-Raphson with bisection fallback."""
    price, spot, strike, tau, r = (_to_dec(v) for v in (price, spot, strike, tau, r))
    tol = _to_dec(tol)
    if tau <= 0 or price <= 0:
        return None

    # Newton-Raphson
    iv = Decimal("0.2")
    for _ in range(max_iter):
        p = bs_price(kind, spot, strike, tau, iv, r)
        diff = p - price
        if abs(diff) < tol:
            return iv
        greeks = bs_greeks(kind, spot, strike, tau, iv, r)
        vega = greeks.vega * Decimal(100)
        if abs(vega) < Decimal("1e-12"):
            break
        iv -= diff / vega
        if iv <= Decimal("0.001") or iv > Decimal("5.0"):
            break

    # Bisection fallback
    low, high = Decimal("0.001"), Decimal("5.0")
    for _ in range(max_iter):
        mid = (low + high) / Decimal(2)
        p = bs_price(kind, spot, strike, tau, mid, r)
        if abs(p - price) < tol or (high - low) < tol:
            return mid
        if p > price:
            high = mid
        else:
            low = mid

    return None
