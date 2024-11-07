
import pytest 

from meal_max.models.kitchen_model import BattleModel
from meal_max.models.kitchen_model import Meal

@pytest.fixture()

def battle_model():
    """Fixture to provide a new instance of battle_model for each test."""
    return BattleModel()

@pytest.fixture

def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function."""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")

"""fixtures providing sample meals for the tests"""
@pytest.fixture
def sample_meal_1():
    return Meal("Spaghetti", "Italian", 10.0, "LOW")
def sample_meal_2():
    return Meal("Pizza", "Italian", 15.0, "MEDIUM")

@pytest.fixture
def sample_conbatants(sample_meal_1, sample_meal_2):
    return [sample_meal_1, sample_meal_2]


##################################################
# Add Combatants Management Test Cases
##################################################

def test_prep_combatants(battle_model, sample_combatants):
    """Test adding combatants to the battle model."""
    battle_model.prep_combatants(sample_combatants[0])
    battle_model.prep_combatants(sample_combatants[1])

    assert len(battle_model.combatants) == 2
    assert battle_model.combatants == sample_combatants

def test_add_duplicate_combatants(battle_model, sample_combatants):
    """test adding t"""
