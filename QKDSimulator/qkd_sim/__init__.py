"""QKD simulation platform - BB84, B92, E91 benchmarking."""

__version__ = "2.0.0"

from .base import QKDProtocol, QKDResult
from .noise import create_backend
from .eve import EveInterceptor
from .benchmark import BenchmarkRunner, BenchmarkData
from .plotter import QKDPlotter
from .protocols.bb84 import BB84Protocol
from .protocols.b92 import B92Protocol
from .protocols.e91 import E91Protocol
