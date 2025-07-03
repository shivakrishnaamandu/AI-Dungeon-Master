import ollama
import json # for JSON handling
import os # for path checking

# --- Configuration ---
LOCAL_MODEL_NAME = "llama3" # Make sure this matches the model you pulled (e.g., "llama3", "mistral", "phi3")
SAVE_FILE = "game_save.json" # game state save file

# Initial Game State (dictionary)
initial_game_state = {
    "current_location":"Abandone Room",
    "player_health":100,
    "player_inventory":[],
    "game_time":0, # could be turns or on-gmae hours
    "visited_locations":["Abandoned Room"],
    "messages": [] # Will store conversation history for your re-loads
}

# --- DM Persona and Initial Scenario ---
# This is the "system prompt" that sets the AI's role and initial instructions.
SYSTEM_PROMPT = """
You are an impartial Dungeon Master for a text-based adventure game.
Your role is to describe the environment, react to player actions, and narrate the outcome.
You will primarily interact with the player, taking their input and describing the world.
Keep your descriptions concise, vivid, and engaging, typically 2-4 sentences.
Start by describing a simple, small, abandoned room.
"""

# Function to save game state
def save_game(state, filename=SAVE_FILE):
    try:
        with open(filename, 'w') as f:
            json.dump(state, f, indent=4) # indent=4 makes the JSON file human-readable
        print(f"\n[Game saved to {filename}]")
    except Exception as e:
        print(f"\n[Error saving game: {e}]")

# Function to load game state (MODIFIED for robustness)
def load_game(filename=SAVE_FILE):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            print(f"\n[Game loaded from {filename}]")

            # --- NEW ROBUSTNESS CHECK ---
            # Ensure 'messages' key exists in the loaded state.
            # If an old save file without 'messages' is loaded, add it.
            if "messages" not in state:
                state["messages"] = []
                print("[Warning: 'messages' key missing in save file. Initialized empty.]")
            # --- END NEW CHECK ---

            return state
        except Exception as e:
            print(f"\n[Error loading game: {e}. Starting new game.]")
            # If load fails or file is corrupt, ensure initial_game_state has 'messages'
            # (which it already does, but good to be explicit here for fallback)
            temp_initial_state = initial_game_state.copy()
            if "messages" not in temp_initial_state:
                temp_initial_state["messages"] = []
            return temp_initial_state
    else:
        print(f"\n[No save file found ({filename}). Starting a new game.]")
        # Ensure initial_game_state has 'messages' for new game start
        temp_initial_state = initial_game_state.copy()
        if "messages" not in temp_initial_state:
            temp_initial_state["messages"] = []
        return temp_initial_state

# --- Game Loop ---
def run_game():
    print("Welcome to your text adventure!")
    print("Type 'quit' or 'exit' to end the game.")
    print("Type 'save' to save your current progress.")

    # (NEW) Start the try block earlier to cover all ollama.chat calls
    try:
        current_game_state = load_game()
        messages = current_game_state["messages"]

        # If it's a new game (or history not loaded properly), kick off the adventure
        if not messages:
            messages.append({'role': 'system', 'content': SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"})
            messages.append({'role': 'user', 'content': 'Begin the adventure.'})
            print("\nDM (thinking...)\n")
            response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)
            dm_response_content = response['message']['content']
            print("DM:", dm_response_content)
            messages.append({'role': 'assistant', 'content': dm_response_content})
        else:
            # If history exists, update the system prompt with the latest game state
            messages[0]['content'] = SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"
            print("\n[Continuing your adventure from the last saved point!]")
            last_dm_message = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'assistant'), None)
            if last_dm_message:
                print("DM (Last turn):", last_dm_message)

        # Main game loop
        while True:
            player_input = input("\n> Your action: ")

            if player_input.lower() in ["quit", "exit"]:
                print("Thank you for playing! Farewell, adventurer!")
                break
            elif player_input.lower() == "save":
                current_game_state["messages"] = messages
                save_game(current_game_state)
                continue
            elif player_input.lower() == "restart": # Handle restart command
                print("\n[Restarting campaign...]")

                # 1. Reset game state
                current_game_state = initial_game_state.copy() #.copy() to ensure it's a new dictionary

                #2. Reset messages history
                message = [] # Clear existing messages

                # 3. Re-initialize messages for a new game
                messages.append({'role': 'system', 'content': SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"})
                messages.append({'role': 'user', 'content': 'Begin the adventure.'})

                # 4. Get the new initial room description
                print("\nDM (thinking...)\n")
                response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)
                dm_response_content = response['message']['content']
                print("DM:", dm_response_content)
                messages.append({'role': 'assistant', 'content': dm_response_content}) # Add DM's first response to history

                # 5. Immediately save the new initial state (optional, but good practice)
                save_game(current_game_state)
                continue # Skip the rest of the loop, go back to next player input

            current_game_state["game_time"] += 1

            # Update the system prompt with new game state (always, as game_state might change)
            messages[0]['content'] = SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"

            messages.append({'role': 'user', 'content': player_input})

            print("\nDM (thinking...)\n")
            response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)

            dm_response_content = response['message']['content']
            print("DM:", dm_response_content)

            messages.append({'role': 'assistant', 'content': dm_response_content})

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure Ollama is running and the model is downloaded correctly.")
        print(f"You tried to use model: {LOCAL_MODEL_NAME}")
        print("You can check installed models with 'ollama list' in your terminal.")

if __name__ == "__main__":
    run_game()