"""Unit tests for symbol mapping."""
from __future__ import annotations

import pytest

from engine.symbols import is_supported, parse_unified, to_native, to_unified


def test_parse_unified():
    assert parse_unified("BTC-USDT-SWAP") == ("BTC", "USDT")
    assert parse_unified("eth-usdc-swap".upper()) == ("ETH", "USDC")


def test_parse_unified_rejects_bad():
    with pytest.raises(ValueError):
        parse_unified("BTC/USDT")
    with pytest.raises(ValueError):
        parse_unified("BTCUSDT")


@pytest.mark.parametrize(
    "exch, unified, expected",
    [
        ("binance", "BTC-USDT-SWAP", "BTCUSDT"),
        ("okx", "BTC-USDT-SWAP", "BTC-USDT-SWAP"),
        ("gate", "BTC-USDT-SWAP", "BTC_USDT"),
        ("bitget", "BTC-USDT-SWAP", "BTCUSDT_UMCBL"),
        ("hyperliquid", "BTC-USDT-SWAP", "BTC"),
    ],
)
def test_to_native(exch, unified, expected):
    assert to_native(exch, unified) == expected


@pytest.mark.parametrize(
    "exch, native, expected",
    [
        ("binance", "BTCUSDT", "BTC-USDT-SWAP"),
        ("binance", "ETHUSDC", "ETH-USDC-SWAP"),
        ("okx", "BTC-USDT-SWAP", "BTC-USDT-SWAP"),
        ("gate", "BTC_USDT", "BTC-USDT-SWAP"),
        ("bitget", "BTCUSDT_UMCBL", "BTC-USDT-SWAP"),
        ("hyperliquid", "BTC", "BTC-USD-SWAP"),
    ],
)
def test_to_unified(exch, native, expected):
    assert to_unified(exch, native) == expected


def test_to_native_unsupported():
    with pytest.raises(ValueError):
        to_native("ftx", "BTC-USDT-SWAP")


def test_is_supported():
    for x in ("binance", "okx", "gate", "bitget", "hyperliquid"):
        assert is_supported(x)
    assert not is_supported("ftx")
