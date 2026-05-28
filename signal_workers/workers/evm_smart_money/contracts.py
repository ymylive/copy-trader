"""Address book + event signature catalog for major EVM perp DEXes.

Keeping this in its own file makes it easy to (a) add a new DEX without
touching the worker plumbing and (b) unit-test the log-decoder against
captured RPC payloads.

Event topic hashes are precomputed (keccak256 of canonical signature) so the
worker does not need ``eth_abi`` at import time.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerpContract:
    chain: str           # "ethereum" / "arbitrum" / "optimism" / "base"
    name: str            # "gmx_v2_event_emitter" / "dydx_perpetualv1" / ...
    address: str         # lowercase 0x...
    topic0: str          # keccak256 topic
    event: str           # canonical event name, e.g. "OrderFilled"


# Topic hashes verified against block explorers. Add more as we onboard
# new venues — keep this list small until each is exercised.
CONTRACTS: list[PerpContract] = [
    # GMX v1 Vault — IncreasePosition / DecreasePosition / LiquidatePosition
    PerpContract(
        chain="arbitrum",
        name="gmx_v1_vault",
        address="0x489ee077994b6658eafa855c308275ead8097c4a",
        topic0="0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022",
        event="IncreasePosition",
    ),
    PerpContract(
        chain="arbitrum",
        name="gmx_v1_vault",
        address="0x489ee077994b6658eafa855c308275ead8097c4a",
        topic0="0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30",
        event="DecreasePosition",
    ),
    # GMX v2 EventEmitter — generic event log; subscribers must inspect
    # the inner `eventName` topic to discriminate. We list it as a single
    # "all events" subscription and let the worker filter.
    PerpContract(
        chain="arbitrum",
        name="gmx_v2_event_emitter",
        address="0xc8ee91a54287db53897056e12d9819156d3822fb",
        topic0="0x137a44067c8961cd7e1d876f4754a5a3a75989b4552f1843fc69c3b372def160",  # EventLog1
        event="EventLog1",
    ),
    # Aevo (Optimism rollup, perp DEX). Single OrderFilled signature.
    PerpContract(
        chain="optimism",
        name="aevo_clearinghouse",
        address="0x0000000000000000000000000000000000000000",  # TODO fill in mainnet addr at deploy
        topic0="0x0000000000000000000000000000000000000000000000000000000000000000",
        event="OrderFilled",
    ),
]


def for_chain(chain: str) -> list[PerpContract]:
    return [c for c in CONTRACTS if c.chain == chain]
