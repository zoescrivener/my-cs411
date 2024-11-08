
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
def sample_meal_3():
    return Meal("Sushi", "Japanese", 20.0, "HIGH")

@pytest.fixture
def sample_conbatants(sample_meal_1, sample_meal_2):
    return [sample_meal_1, sample_meal_2]


##################################################
# Add Combatants Management Test Cases
##################################################

def test_prep_combatants(battle_model, sample_combatants):
    """Test adding combatants to the battle model."""
    battle_model.prep_combatants(sample_meal_1)
    battle_model.prep_combatants(sample_meal_2)

    assert len(battle_model.combatants) == 2
    assert battle_model.combatants == sample_combatants

def test_add_extra_combatants(battle_model, sample_combatants):
    """ Test adding extra combatants to combatants."""
    battle_model.combatants = sample_combatants
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatants(sample_meal_3)


def test_clear_combatants(battle_model, sample_combatants):
    """Test clearing combatants from the battle model."""
    battle_model.combatants = sample_combatants
    battle_model.clear_combatants()

    assert len(battle_model.combatants) == 0
    assert battle_model.combatants == []

def test_get_combatants(battle_model, sample_combatants):
    """Test returning combatants from the battle model."""
    battle_model.combatants = sample_combatants

    assert battle_model.get_combatants() == sample_combatants

def test_get_battle_score(battle_model, sample_meal_1):
    """Test calculating battle score of a meal."""
    score = battle_model.get_battle_score(sample_meal_1)

    assert score == 67.0

def test_battle(battle_model, sample_combatants):
    """Test battling two combatants."""
    battle_model.combatants = sample_combatants
    battle_result = battle_model.battle()

    assert battle_result == sample_combatants[1]

    """need to test for , removing the loser,
    updating the stats for each combatant, all the intermediate calculations"""