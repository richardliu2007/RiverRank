"""
Fourier coefficients on [0, 1] for an arbitrary real-valued function f(x).

We use the standard real Fourier series on [0,1] with basis {1, cos(2πnx), sin(2πnx)}:

f(x) ~ a0/2 + Σ_{n=1..∞} [ a_n cos(2π n x) + b_n sin(2π n x) ]

Coefficients:
a0 = 2 ∫_0^1 f(x) dx
a_n = 2 ∫_0^1 f(x) cos(2π n x) dx
b_n = 2 ∫_0^1 f(x) sin(2π n x) dx

This script supports:
- numeric integration (default) for any callable f(x)
- optional symbolic integration if you provide f_expr (a sympy expression)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union, List, Tuple
import math
import matplotlib.pyplot as plt
import numpy as np

# ---------- Numeric integration (Simpson's rule) ----------

def simpson_integrate(g: Callable[[float], float], a: float, b: float, n: int = 10_000) -> float:
    """
    Composite Simpson's rule on [a,b] with n subintervals (n must be even).
    Works well for smooth-ish functions; increase n for tougher functions.
    """
    if n % 2 == 1:
        n += 1
    h = (b - a) / n
    s = g(a) + g(b)
    for k in range(1, n):
        x = a + k * h
        s += (4 if k % 2 == 1 else 2) * g(x)
    return s * (h / 3.0)


# ---------- Fourier coefficients on [0,1] ----------

@dataclass(frozen=True)
class FourierCoefficients:
    a0: float
    a: List[float]  # a[n-1] corresponds to a_n for n>=1
    b: List[float]  # b[n-1] corresponds to b_n for n>=1

def fourier_coeffs_numeric(
    f: Callable[[float], float],
    N: int,
    *,
    n_int: int = 20_000,
) -> FourierCoefficients:
    """
    Compute a0, {a_n}, {b_n} for n=1..N numerically on [0,1].
    """
    twopi = 2.0 * math.pi

    # a0 = 2 ∫_0^1 f(x) dx
    a0 = 2.0 * simpson_integrate(f, 0.0, 1.0, n=n_int)

    a_list: List[float] = []
    b_list: List[float] = []

    for n in range(1, N + 1):
        def g_cos(x: float, nn=n) -> float:
            return f(x) * math.cos(twopi * nn * x)

        def g_sin(x: float, nn=n) -> float:
            return f(x) * math.sin(twopi * nn * x)

        an = 2.0 * simpson_integrate(g_cos, 0.0, 1.0, n=n_int)
        bn = 2.0 * simpson_integrate(g_sin, 0.0, 1.0, n=n_int)

        a_list.append(an)
        b_list.append(bn)

    return FourierCoefficients(a0=a0, a=a_list, b=b_list)


# ---------- Optional: symbolic coefficients with SymPy ----------

def fourier_coeffs_symbolic(
    f_expr,
    x_symbol=None,
    N: int = 10,
):
    """
    Symbolic coefficients using sympy (when integrals are tractable).
    Returns sympy expressions (can be evaluated numerically later).
    """
    import sympy as sp

    x = x_symbol if x_symbol is not None else sp.Symbol("x", real=True)
    n = sp.Symbol("n", integer=True, positive=True)

    a0 = 2 * sp.integrate(f_expr, (x, 0, 1))
    a = [2 * sp.integrate(f_expr * sp.cos(2 * sp.pi * k * x), (x, 0, 1)) for k in range(1, N + 1)]
    b = [2 * sp.integrate(f_expr * sp.sin(2 * sp.pi * k * x), (x, 0, 1)) for k in range(1, N + 1)]

    return a0, a, b


# ---------- Example usage ----------

def reconstruct_value(coeffs: FourierCoefficients, x: float, M: Optional[int] = None) -> float:
    """
    Reconstruct partial Fourier series at point x using up to M modes (default: all available).
    """
    M = M if M is not None else len(coeffs.a)
    twopi = 2.0 * math.pi
    s = 0.5 * coeffs.a0
    for n in range(1, M + 1):
        s += coeffs.a[n - 1] * math.cos(twopi * n * x) + coeffs.b[n - 1] * math.sin(twopi * n * x)
    return s


if __name__ == "__main__":
    # Define ANY function on [0,1]
    # Example: f(x) = x*(1-x) + 0.2*sin(6πx)
    def f(x: float) -> float:
        return np.sign(x-0.5)

    N = 100  # number of harmonics
    coeffs = fourier_coeffs_numeric(f, N, n_int=50_000)

    # print("a0 =", coeffs.a0)
    # for n in range(1, N + 1):
    #     print(f"a_{n} = {coeffs.a[n-1]: .12f}    b_{n} = {coeffs.b[n-1]: .12f}")

    # Quick reconstruction sanity check
    x0 = 0.37
    approx = reconstruct_value(coeffs, x0, M=N)
    print(f"\nAt x={x0:.2f}: f(x)={f(x0):.12f}, Fourier partial sum={approx:.12f}")
    Npoints = 100
    x = np.linspace(0, 1, Npoints)
    #print(x)
    f_x = np.zeros_like(x)
    for xi in range(Npoints):
        f_x[xi] = f(x[xi])

    f_approx = np.zeros_like(x)
    for xi in range(Npoints):
        f_approx[xi] = reconstruct_value(coeffs, x[xi], M=N)

    plt.plot(x, f_x, label="exact")
    plt.plot(x, f_approx, label="approximation")
    plt.legend()
    plt.show()
