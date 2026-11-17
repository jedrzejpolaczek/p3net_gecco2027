"""No-op local stub for the real `netifaces` PyPI package.

`netifaces` is a C-extension package with no prebuilt wheel for modern
Python on Windows (needs MSVC Build Tools to build from source). It is a
hard `install_requires` of hpbandster (MO-BOHB's backend), but is used
ONLY inside hpbandster.core.nameserver.nic_name_to_host and
hpbandster.utils.nic_name_to_host -- both lazy imports inside a function
body used solely for auto-detecting a network interface for hpbandster's
Pyro4-based DISTRIBUTED worker nameserver. Our usage (methods/external/
mo_bohb.py, ask/tell over a single local process) never starts that
nameserver, so this function is never called and this stub's functions
are never actually invoked -- verified by reading hpbandster 0.7.4's
source directly, not assumed.
"""

AF_INET = 2  # matches socket.AF_INET's real value; ifaddresses() below never actually runs


def ifaddresses(interface):
    raise NotImplementedError(
        "netifaces is stubbed out in this project (see this package's module "
        "docstring) -- if you see this error, something now calls "
        "hpbandster's nic_name_to_host(), which was previously assumed "
        "unreachable from methods/external/mo_bohb.py; either avoid that "
        "code path or install the real netifaces package instead of this stub."
    )
