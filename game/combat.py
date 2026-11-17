"""Combat damage resolution helpers.

All helpers are pure functions and return clamped, non-negative results.
Percentages are expressed as fractions in ``[0, 1]``.
"""

from collections.abc import Iterable

RESIST_CAP = 0.9
GLANCING_FLOOR = 0.7
GLANCING_PER_LEVEL = 0.06
DODGE_LEVEL_FACTOR = 100.0


def _clamp(value, low, high):
    """Clamp *value* to the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


def _non_negative(value):
    return max(0.0, value)


def mitigate(damage, armor, k=100.0):
    """Apply the armor mitigation curve ``damage * k / (k + armor)``.

    ``k`` is the armor value at which incoming damage is halved.  Zero armor
    therefore leaves the damage untouched instead of switching to a different
    (flat subtraction) formula.
    """
    damage = _non_negative(damage)
    armor = _non_negative(armor)
    denominator = k + armor
    if denominator <= 0:
        return 0.0
    return damage * k / denominator


def crit_damage(damage, crit_chance, crit_mult, roll):
    """Return damage after a single critical-strike roll.

    ``roll`` is a uniform value in ``[0, 1)``; a critical hit occurs only when
    it is strictly below ``crit_chance``.  The multiplier is never assumed.
    """
    damage = _non_negative(damage)
    chance = _clamp(crit_chance, 0.0, 1.0)
    if roll < chance:
        return damage * crit_mult
    return damage


def resist_damage(damage, resist):
    """Apply resistance multiplicatively and cap it at 90%.

    ``resist`` may be a single fraction or an iterable of resistance sources.
    Each source is clamped to ``[0, RESIST_CAP]`` and sources combine by
    multiplying their remaining-damage factors, so stacked resistances can
    never flip damage into healing.
    """
    damage = _non_negative(damage)
    if isinstance(resist, Iterable) and not isinstance(resist, (str, bytes)):
        sources = resist
    else:
        sources = (resist,)

    remaining = 1.0
    for source in sources:
        remaining *= 1.0 - _clamp(source, 0.0, RESIST_CAP)
    # Cap the *combined* reduction too: stacking several capped sources must
    # not push the total past 90% (and can therefore never heal the target).
    remaining = max(1.0 - RESIST_CAP, remaining)
    return _non_negative(damage * remaining)


def glancing_factor(level_diff):
    """Damage factor for a glancing blow based on the attacker/target level gap.

    Each level of disadvantage costs 6% damage, floored at 70%.  Attacking a
    lower-level target never grants more than normal damage through this path.
    """
    return _clamp(1.0 - GLANCING_PER_LEVEL * level_diff,
                  GLANCING_FLOOR, 1.0)


def dodge_chance(dodge_rating, level):
    """Diminishing-returns dodge chance: ``rating / (rating + level * 100)``."""
    dodge_rating = _non_negative(dodge_rating)
    level = _non_negative(level)
    denominator = dodge_rating + level * DODGE_LEVEL_FACTOR
    if denominator <= 0:
        return 0.0
    return _clamp(dodge_rating / denominator, 0.0, 1.0)


def block_damage(damage, block_value, blocked):
    """Subtract the shield value only when the block actually succeeded."""
    damage = _non_negative(damage)
    if not blocked:
        return damage
    return _non_negative(damage - _non_negative(block_value))


def dot_ticks(total_damage, duration, tick_interval):
    """Split a DoT into whole ticks and return ``(tick_count, per_tick)``.

    The total damage is divided evenly across the *ticks*, not across seconds.
    """
    total_damage = _non_negative(total_damage)
    if duration <= 0 or tick_interval <= 0:
        return 0, 0.0
    ticks = max(1, int(duration / tick_interval))
    return ticks, total_damage / ticks


def variance_damage(base, roll, variance=0.1):
    """Apply symmetric damage variance around the base value.

    ``roll == 0`` deals ``base * (1 - variance)``, ``roll == 0.5`` deals
    exactly the base, and ``roll == 1`` deals ``base * (1 + variance)``.
    """
    base = _non_negative(base)
    roll = _clamp(roll, 0.0, 1.0)
    variance = _non_negative(variance)
    return base * (1.0 + variance * (2.0 * roll - 1.0))


def combine_modifiers(damage, flat=0.0, pct=0.0):
    """Apply flat reduction first, then the percentage reduction.

    ``(damage - flat) * (1 - pct)`` keeps the two modifier buckets in a fixed,
    order-independent order and never returns negative damage.
    """
    damage = _non_negative(damage)
    flat = _non_negative(flat)
    pct = _clamp(pct, 0.0, 1.0)
    return _non_negative((damage - flat) * (1.0 - pct))


def apply_hp_damage(hp, damage):
    """Subtract damage from HP, flooring the result at zero."""
    hp = _non_negative(hp)
    damage = _non_negative(damage)
    return max(0.0, hp - damage)


def heal_amount(heal, reduction=0.0):
    """Apply healing reduction (e.g. mortal strike) without going negative."""
    heal = _non_negative(heal)
    reduction = _clamp(reduction, 0.0, 1.0)
    return heal * (1.0 - reduction)


def combo_multiplier(stacks, per_stack, cap=0.3):
    """Stacking combo bonus, capped so it cannot become unbounded."""
    bonus = _non_negative(stacks) * _non_negative(per_stack)
    return 1.0 + min(bonus, _non_negative(cap))


def effective_armor(armor, pen_pct=0.0, pen_flat=0.0):
    """Armor after flat penetration, then percentage penetration.

    ``max(0, armor - pen_flat) * (1 - pen_pct)`` matches the fixed resolution
    order used everywhere else in the combat pipeline.
    """
    armor = _non_negative(armor)
    pen_flat = _non_negative(pen_flat)
    pen_pct = _clamp(pen_pct, 0.0, 1.0)
    return _non_negative((armor - pen_flat) * (1.0 - pen_pct))


def is_executable(hp_pct, threshold):
    """Whether a target is within execute range (threshold is inclusive)."""
    return hp_pct <= threshold
