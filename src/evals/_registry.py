from evals.oranbench.oranbench import oranbench
from evals.sixg_bench.sixg_bench import sixg_bench
from evals.srsranbench.srsranbench import srsranbench
from evals.telco_challenge.track_a.task import ttac_wireless
from evals.telelogs.telelogs import telelogs
from evals.telemath.telemath import telemath
from evals.teleqna.teleqna import teleqna
from evals.teletables.teletables import teletables
from evals.three_gpp.three_gpp import three_gpp
from evals.ttac_ipnet.task import ttac_ipnet

__all__ = [
    "oranbench",
    "sixg_bench",
    "srsranbench",
    "telelogs",
    "telemath",
    "teleqna",
    "teletables",
    "three_gpp",
    "ttac_ipnet",
    "ttac_wireless",
]
