from context lib inport contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kithen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kithen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal(meal = "Meal name", cuisine = "Italian", price = 30.0, difficulty = "LOW")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Italian", 30.0, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists."):
        create_meal(meal = "Meal name", cuisine = "Italian", price = 30.0, difficulty = "LOW")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative duration
    with pytest.raises(ValueError, match="Invalid meal price: -180 \(must be a positive float\)."):
        create_meal(meal = "Meal name", cuisine = "Italian", price = -30.0, difficulty = "LOW")


    # Attempt to create a meal with a non-float duration
    with pytest.raises(ValueError, match="Invalid meal price: invalid \(must be a positive float\)."):
        create_meal(meal = "Meal name", cuisine = "Italian", price = 30, difficulty = "LOW")

def test_create_meal_min_price(mock_cursor):
    """Test creating a meal with the minimum positive price."""

    # Call the function to create a new meal with low price
    create_meal(meal="Cheap Meal", cuisine="General", price=0.01, difficulty="LOW")
    
    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty) VALUES (?, ?, ?, ?)
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."


def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., NOT 'LOW', 'MED', or 'HIGH')."""

    # Attempt to create a meal with a unique difficulty
    with pytest.raises(ValueError, match="Invalid difficulty provided: hard \(must be a string 'LOW', 'MED', or 'HIGH'\)."):
        create_meal(meal = "Meal name", cuisine = "Italian", price = 30.0, difficulty = "hard")

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has already been deleted"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing all the meals (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    """Test get meal with vaild ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Italian", 30.0, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Italian", 30.0, "LOW", False)

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    """Test gets meal with invalid ID. Should raise Error."""

    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted_meal(mock_cursor):
    """Test gets meal with ID that has been deleted. Should raise Error."""

    # Test retrieving a soft-deleted meal by ID.

    # Simulate that meal is deleted for the given ID
    mock_cursor.fetchone.return_value = (1, "Deleted Meal", "Italian", 10.0, "LOW", True)
    
    # Expect a ValueError when the meal is deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)


def test_get_meal_by_name(mock_cursor):
    """Test get meal by its name."""
    # Simulate that the meal exists (meal = "Meal Name")
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Italian", 30.0, "LOW", False)


    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Italian", 30.0, "LOW")


    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_name_deleted_meal(mock_cursor):
    """Test retrieving a soft-deleted meal by name."""

    # Simulate that the meal does not exists (meal = "Meal Name")
    mock_cursor.fetchone.return_value = (1, "Deleted Meal", "Italian", 10.0, "LOW", True)
    
    # Expect a ValueError when the meal that is called is deleted
    with pytest.raises(ValueError, match="Meal with name 'Deleted Meal' has been deleted"):
        get_meal_by_name("Deleted Meal")

def test_get_leaderboard(mock_cursor):
    """Test retrieving all meals that are not marked as deleted."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 13.0, "LOW", 10, 8, 0.8, False),
        (2, "Meal B", "Cuisine B", 10.0, "MED", 15, 10, 0.6667, False),
        (3, "Meal C", "Cuisine C", 15.0, "HIGH", 5, 2, 0.4, False)
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 10.0, "difficulty": "MED", "battles": 15, "wins": 10, "win_pct": 66.7},
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 13.0, "difficulty": "LOW", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 15.0, "difficulty": "HIGH", "battles": 5, "wins": 2, "win_pct": 40.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = FALSE AND battles > 0
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_empty(mock_cursor, caplog):
    """Test that retrieving empty leaderboard."""

    # Simulate that leaderboard is empty (no meals)
    mock_cursor.fetchall.return_value = []

    # Call the get_leaderboard function
    result = get_leaderboard()

    # Ensure the result is an empty list
    assert result == [], f"Expected empty list, but got {result}"

    # Ensure that a warning was logged
    assert "Leaderboard retrieved successfully." in caplog.text, "Expected log entry not found."

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = FALSE AND battles > 0
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_ordered_by_win_pct(mock_cursor):
    """Test retrieving all meals ordered by win_pct."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 13.0, "LOW", 10, 8, 0.8),
        (3, "Meal B", "Cuisine B", 15.0, "HIGH", 5, 2, 0.4),
        (2, "Meal C", "Cuisine C", 10.0, "MED", 15, 10, 0.6667)
    ]

    # Call the get_leaderboard function with sort_by_play_count = True
    leaderboard = get_leaderboard(sort_by="win_pct")

    # Ensure the results are sorted by play count
    expected_result = [
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 13.0, "difficulty": "LOW", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 10.0, "difficulty": "MED", "battles": 15, "wins": 10, "win_pct": 66.7},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 15.0, "difficulty": "HIGH", "battles": 5, "wins": 2, "win_pct": 40.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
        ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_update_meal_stats_win(mock_cursor):
    """Test updating the win count of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating the loss count of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    meal_id = 1
    update_meal_stats(meal_id, "loss")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

### Test for valid sort_by:
def test_get_leaderboard_invalid_sort_by():
    """Test error when sort_by is invalid"""

    # Expect a ValueError when attempting input invalid sort_by
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by="invalid_sort")

### Test for Updating a Deleted Meal:
def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update meal stats for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

    # Ensure that no SQL query for updating play count was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

### Test for Updating a None-existent Meal
def test_update_meal_stats_nonexistent_meal(mock_cursor):
    """Test error when trying to update stats for a non-existent meal."""

    # Simulate that the meal does not exist (fetchone returns None)
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to update a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        update_meal_stats(1, "win")

    # Ensure that the query checked if the meal exists
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

### Test for Updating a meal with an invalid result
def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when providing an invalid result to update_meal_stats."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Expect a ValueError when attempting to update with an invalid result
    with pytest.raises(ValueError, match="Invalid result: winner. Expected 'win' or 'loss'."):
        update_meal_stats(1, "winner")