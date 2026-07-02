from __future__ import annotations

import pytest

from core.har_field_rules import (
    HarSkipReason,
    get_skip_reason,
    should_block_import,
)


@pytest.mark.parametrize(
    ("def_type", "field", "expected"),
    [
        (
            "AlienRace.ThingDef_AlienRace",
            "alienRace.generalSettings.alienPartGenerator.colorChannels.0.name",
            HarSkipReason.COLOR_CHANNEL_NAME,
        ),
        (
            "AlienRace.ThingDef_AlienRace",
            "alienRace.generalSettings.alienPartGenerator.bodyAddons.5.name",
            HarSkipReason.BODY_ADDON_NAME,
        ),
        (
            "AlienRace.ThingDef_AlienRace",
            "alienRace.generalSettings.alienPartGenerator.bodyAddons.0.conditions.0.bodyPartLabel",
            HarSkipReason.BODY_PART_LABEL_CONDITION,
        ),
        ("AlienRace.ThingDef_AlienRace", "label", HarSkipReason.NONE),
        ("ThingDef", "label", HarSkipReason.NONE),
    ],
)
def test_get_skip_reason_matches_har_technical_keys(def_type, field, expected):
    assert get_skip_reason(def_type, field) == expected


def test_should_block_import_when_translation_differs_from_source():
    field = "alienRace.generalSettings.alienPartGenerator.colorChannels.0.name"
    assert should_block_import("AlienRace.ThingDef_AlienRace", field, "hair", "髮色")
    assert not should_block_import("AlienRace.ThingDef_AlienRace", field, "hair", "hair")
    assert not should_block_import("ThingDef", "label", "Sword", "劍")
