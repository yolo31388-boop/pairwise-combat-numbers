import pytest

from game.combat import (apply_hp_damage, block_damage, combine_modifiers,
                         combo_multiplier, crit_damage, dodge_chance, dot_ticks,
                         effective_armor, glancing_factor, heal_amount,
                         is_executable, mitigate, resist_damage,
                         variance_damage)


def test_mitigation_uses_armor_curve():
    assert mitigate(1000, 100) == pytest.approx(500.0)
    assert mitigate(1000, 0) == pytest.approx(1000.0)


def test_crit_only_when_roll_is_under_chance():
    assert crit_damage(100, 0.5, 2.0, 0.3) == pytest.approx(200.0)
    assert crit_damage(100, 0.5, 2.0, 0.9) == pytest.approx(100.0)


def test_crit_multiplier_varies():
    assert crit_damage(100, 0.5, 3.0, 0.1) == pytest.approx(300.0)
    assert crit_damage(100, 0.5, 3.0, 0.9) == pytest.approx(100.0)


def test_resist_is_clamped_at_ninety_percent():
    assert resist_damage(1000, 0.5) == pytest.approx(500.0)
    assert resist_damage(1000, 1.5) == pytest.approx(100.0)


def test_glancing_blow_scales_with_level_difference():
    assert glancing_factor(0) == pytest.approx(1.0)
    assert glancing_factor(5) == pytest.approx(0.7)


def test_dodge_chance_diminishes_with_level():
    assert dodge_chance(500, 60) == pytest.approx(500 / 6500, rel=0.01)


def test_block_reduces_damage_only_when_blocked():
    assert block_damage(100, 30, True) == pytest.approx(70.0)
    assert block_damage(100, 30, False) == pytest.approx(100.0)


def test_dot_is_split_into_ticks():
    ticks, per_tick = dot_ticks(120, 12, 3)
    assert ticks == 4
    assert per_tick == pytest.approx(30.0)


def test_variance_uses_roll():
    assert variance_damage(100, 0.5) == pytest.approx(100.0)
    assert variance_damage(100, 1.0) == pytest.approx(110.0)


def test_flat_modifier_applies_before_multiplier():
    assert combine_modifiers(100, flat=10, pct=0.2) == pytest.approx(72.0)


def test_hp_never_goes_negative():
    assert apply_hp_damage(10, 50) == 0


def test_healing_reduction_is_applied():
    assert heal_amount(200, reduction=0.5) == pytest.approx(100.0)


def test_combo_bonus_is_capped():
    assert combo_multiplier(5, 0.1, cap=0.3) == pytest.approx(1.3)
    assert combo_multiplier(10, 0.1, cap=0.3) == pytest.approx(1.3)


def test_armor_penetration_applies_flat_then_percent():
    assert effective_armor(200, pen_pct=0.5, pen_flat=20) == pytest.approx(90.0)


def test_execute_threshold_is_inclusive():
    assert is_executable(0.2, 0.25) is True
    assert is_executable(0.3, 0.25) is False
