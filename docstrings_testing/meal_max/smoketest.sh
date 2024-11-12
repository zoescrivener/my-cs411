#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meals cleared successfully."
  else
    echo "Failed to clear all meals."
    exit 1
  fi
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal - $cuisine, $price, $difficulty) to the kitchen..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal=$1

  echo "Getting meal by name (Meal: '$meal')..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name?meal=$(echo $meal | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}

get_leaderboard() {
  sort_by=$1

  echo "Getting leaderboard sorted by $sort_by..."
  response=$(curl -s -X GET "$BASE_URL/get-leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meals JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to Leaderboard."
    exit 1
  fi
}

# Function to update meal stats with a win or loss
update_meal_stats() {
  meal_id=$1
  result=$2

  echo "Updating meal stats for meal ID $meal_id with result: $result..."
  response=$(curl -s -X POST "$BASE_URL/update-meal-stats" -H "Content-Type: application/json" \
    -d "{\"meal_id\": $meal_id, \"result\": \"$result\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal stats updated successfully for result: $result"
    [ "$ECHO_JSON" = true ] && echo "$response" | jq .
  else
    echo "Failed to update meal stats for result: $result"
    echo "$response"
    exit 1
  fi
}

###############################################
#
# Battle Management
#
###############################################

# Conduct a battle between two meals
battle() {
  echo "Starting battle..."
  response=$(curl -s -X POST "$BASE_URL/battle")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle conducted successfully."
    [ "$ECHO_JSON" = true ] && echo "$response" | jq .
  else
    echo "Failed to conduct battle."
    exit 1
  fi
}

# Clear all combatants
clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}


# Function to calculate the battle score of a meal (combatant)
get_battle_score() {
  meal_id=$1
  echo "Calculating battle score for meal with ID $meal_id..."
  response=$(curl -s -X GET "$BASE_URL/get-battle-score/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle score calculated successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Score JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to calculate battle score."
    exit 1
  fi
}

# Function to retrieve the list of combatants
get_combatants() {
  echo "Retrieving current list of combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}


# Add a combatant for a battle
prep_combatant() {
  meal_id=$1
  echo "Adding combatant with meal ID $meal_id..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant added successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatant JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add combatant."
    exit 1
  fi
}

###############################################
#
# Run Tests
#
###############################################

# Health checks
check_health
check_db

# Clear all meals
clear_meals

# Create meals
create_meal "Pizza" "Italian" 13.0 "MED"
create_meal "Taco" "Mexican" 10.0 "LOW"
create_meal "Sushi" "Japanese" 15.0 "HIGH"

# Retrieve and delete a meal
get_meal_by_id 1
delete_meal 1
get_meal_by_id 1  # Should fail since it is deleted

# Leaderboard tests
get_leaderboard "wins"
get_leaderboard "win_pct"


###############################################
#
# Run Combatant Tests
#
###############################################

# Clear combatants list and prepare for tests
echo "Clearing combatants list..."
curl -s -X POST "$BASE_URL/clear-combatants" | grep -q '"status": "success"'
if [ $? -eq 0 ]; then
  echo "Combatants list cleared successfully."
else
  echo "Failed to clear combatants list."
  exit 1
fi

# Add combatants
prep_combatant 2
prep_combatant 3

# Retrieve and verify combatants list
get_combatants

# Calculate battle scores for each combatant
get_battle_score 2
get_battle_score 3

echo "All tests passed successfully!"


