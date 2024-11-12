
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
"""sample_meal_1 has battle score of 67"""
@pytest.fixture
def sample_meal_2():
    return Meal("Pizza", "Italian", 15.0, "MEDIUM")
"""sample_meal_2 has battle score of 103"""
@pytest.fixture
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

    

    """need to test for , removing the loser,
    updating the stats for each combatant, all the intermediate calculations"""

def test_battle(battle_model, sample_meal_1, sample_meal_2, mock_update_meal_stats, mocker):
    """Test battling two combatants."""
    battle_model.prep_combatant(sample_meal_1)
    battle_model.prep_combatant(sample_meal_2)

    # Mock get_random to control randomness
    mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.5)

    winner_meal = battle_model.battle()
    
    # Check the winner based on scores
    score_1 = battle_model.get_battle_score(sample_meal_1)
    score_2 = battle_model.get_battle_score(sample_meal_2)

    if abs(score_1 - score_2) / 100 > 0.5:
        expected_winner = sample_meal_1 if score_1 > score_2 else sample_meal_2
    else:
        expected_winner = sample_meal_2 if score_2 > score_1 else sample_meal_1

    assert winner_meal == expected_winner.meal

    # Check that the losing combatant was removed
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0] == expected_winner

    # Check if update_meal_stats was called with correct values
    mock_update_meal_stats.assert_any_call(expected_winner.id, 'win')
    mock_update_meal_stats.assert_any_call(battle_model.combatants[0].id, 'loss')
    
def test_battle_score_intermediate_calculations(battle_model, sample_meal_1, sample_meal_2, mocker):
    """Test intermediate calculations like delta and score logging."""
    battle_model.prep_combatant(sample_meal_1)
    battle_model.prep_combatant(sample_meal_2)
    mock_logger = mocker.patch("meal_max.models.battle_model.logger")

    battle_model.battle()

    # Check for specific logs
    mock_logger.info.assert_any_call("Score for %s: %.3f", sample_meal_1.meal, 67.0)
    mock_logger.info.assert_any_call("Score for %s: %.3f", sample_meal_2.meal, 103.0)

    delta = abs(67.0 - 103.0) / 100
    mock_logger.info.assert_any_call("Delta between scores: %.3f", delta)