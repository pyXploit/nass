"""Tests for nass.plot. Skipped when matplotlib is not installed."""

from __future__ import annotations

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from matplotlib.text import Text  # noqa: E402

import nass  # noqa: E402
from nass import plot as nass_plot  # noqa: E402


@pytest.fixture(autouse=True)
def _clean() -> None:
    nass_plot.disable()
    yield
    nass_plot.disable()


def test_shapes_natively_reports_the_installed_version() -> None:
    expected = nass_plot._version() >= (3, 11)
    assert nass_plot.shapes_natively() is expected


def test_enable_is_a_noop_when_matplotlib_shapes_natively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 11))
    assert nass_plot.enable() is False
    assert Text(0, 0, "مرحبا").get_text() == "مرحبا"


def test_enable_patches_old_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 10))
    assert nass_plot.enable() is True
    assert Text(0, 0, "مرحبا").get_text() == nass.display("مرحبا")


def test_patch_leaves_latin_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 10))
    nass_plot.enable()
    assert Text(0, 0, "hello").get_text() == "hello"


def test_disable_restores_original_behaviour(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 10))
    nass_plot.enable()
    nass_plot.disable()
    assert Text(0, 0, "مرحبا").get_text() == "مرحبا"


def test_enable_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 10))
    nass_plot.enable()
    nass_plot.enable()
    assert Text(0, 0, "مرحبا").get_text() == nass.display("مرحبا")


def test_already_shaped_text_is_not_reprocessed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(nass_plot, "_version", lambda: (3, 10))
    nass_plot.enable()
    shaped = nass.display("مرحبا")
    assert Text(0, 0, shaped).get_text() == shaped


def test_disable_without_enable_is_safe() -> None:
    nass_plot.disable()
    nass_plot.disable()


def test_plot_is_lazy() -> None:
    assert nass.plot.__name__ == "nass.plot"
