import ollama
import json
import os

# --- ANSI Color Codes ---
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m" # For DM responses
    YELLOW = "\033[93m" # For System/Game messages (save, load, restart)
    BLUE = "\033[94m" # For Player Input prompt
    MAGENTA = "\033[95m" # For DM (thinking...)
    CYAN = "\033[96m" # For instructions/farewell
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

# --- Configuration ---
LOCAL_MODEL_NAME = "llama3"
SAVE_FILE = "game_save.json"

# Define common game action keywords for AI guidance
ACTION_KEYWORDS = [
    "attack", "fight", "hit", "strike",
    "look", "examine", "inspect", "observe",
    "take", "pick up", "grab", "collect",
    "use", "apply", "activate",
    "talk", "speak", "ask", "converse",
    "inventory", "items", "bag", "check inventory",
    "north", "south", "east", "west", "up", "down", "move", "go"
]

# Initial Game State
initial_game_state = {
    "current_location": "Abandoned Room",
    "player_health": 100,
    "player_inventory": [],
    "game_time": 0,
    "visited_locations": ["Abandoned Room"],
    "messages": [] # Will store conversation history if no save exists
}

# --- System Prompt for the AI DM ---
SYSTEM_PROMPT = f"""You are the Dungeon Master (DM) for a text-based adventure game.
Your goal is to narrate the game world, respond to player actions, and manage the game state.
Keep responses concise and engaging, usually 1-3 paragraphs.
Always incorporate the current game state into your narrative subtly.

RULES FOR PLAYER ACTIONS:
When the player issues a command, interpret it within the game context.
Prioritize the following action keywords if they are clearly present in the player's input:
{', '.join([f"'{kw}'" for kw in ACTION_KEYWORDS])}

- For **Movement Actions** (like 'go north', 'move east'): The game system will update the player's location. Your role is to **describe the new location** based on the updated 'current_location' in the game state, and how the player arrives there. Do not block movement, just narrate the new scene.
- For recognized **Non-Movement Actions**: Describe the immediate outcome, success or failure, and any changes in the environment or game state.
- For impossible actions: Clearly state why the action cannot be performed (e.g., "You don't have that item," "The enemy is too far").
- If no clear keyword is present: Narrate the scene and respond to the general intent, but still try to move the plot forward.

Always end your turn by prompting the player for their next action.
"""

# Function to handle player movement (NEW)
def move_player(game_state, direction):
    # For simplicity, we'll just append the direction to the current location for now.
    # Later, we can define specific rooms and connections.
    old_location = game_state["current_location"]
    new_location = f"{old_location} ({direction} exit)" # AI will describe this
    game_state["current_location"] = new_location

    if new_location not in game_state["visited_locations"]:
        game_state["visited_locations"].append(new_location)

    # Return the new location name to be used in AI prompt
    return new_location

# Function to save game state
def save_game(state, filename=SAVE_FILE):
    try:
        with open(filename, 'w') as f:
            json.dump(state, f, indent=4)
        print(f"\n{Colors.YELLOW}[Game saved to {filename}]{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}[Error saving game: {e}]{Colors.RESET}")

# Function to load game state
def load_game(filename=SAVE_FILE):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            print(f"\n{Colors.YELLOW}[Game loaded from {filename}]{Colors.RESET}")

            # Ensure 'messages' key exists in the loaded state.
            if "messages" not in state:
                state["messages"] = []
                print(f"{Colors.YELLOW}[Warning: 'messages' key missing in save file. Initialized empty.]{Colors.RESET}")

            return state
        except Exception as e:
            print(f"\n{Colors.RED}[Error loading game: {e}. Starting new game.]{Colors.RESET}")
            # If load fails or file is corrupt, ensure initial_game_state has 'messages'
            temp_initial_state = initial_game_state.copy()
            if "messages" not in temp_initial_state:
                temp_initial_state["messages"] = []
            return temp_initial_state
    else:
        print(f"\n{Colors.YELLOW}[No save file found ({filename}). Starting a new game.]{Colors.RESET}")
        # Ensure initial_game_state has 'messages' for new game start
        temp_initial_state = initial_game_state.copy()
        if "messages" not in temp_initial_state:
            temp_initial_state["messages"] = []
        return temp_initial_state

# --- Game Loop ---
def run_game():
    print(f"{Colors.GREEN}{Colors.BOLD}Welcome to your text adventure!{Colors.RESET}")
    print(f"{Colors.CYAN}Type 'quit' or 'exit' to end the game.{Colors.RESET}")
    print(f"{Colors.CYAN}Type 'save' to save your current progress.{Colors.RESET}")
    print(f"{Colors.CYAN}Type 'restart' to begin a new campaign.{Colors.RESET}") # Added restart instruction

    # Start the try block earlier to cover all ollama.chat calls
    try:
        current_game_state = load_game()
        messages = current_game_state["messages"]

        # If it's a new game (or history not loaded properly), kick off the adventure
        if not messages:
            messages.append({'role': 'system', 'content': SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"})
            messages.append({'role': 'user', 'content': 'Begin the adventure.'})
            print(f"\n{Colors.MAGENTA}DM (thinking...){Colors.RESET}\n")
            response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)
            dm_response_content = response['message']['content']
            print(f"{Colors.GREEN}DM:{Colors.RESET} {dm_response_content}")
            messages.append({'role': 'assistant', 'content': dm_response_content}) # Fix: Ensure JSON serializable

        else:
            # If history exists, update the system prompt with the latest game state
            messages[0]['content'] = SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"
            print(f"\n{Colors.YELLOW}[Continuing your adventure from the last saved point!]{Colors.RESET}")
            last_dm_message = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'assistant'), None)
            if last_dm_message:
                print(f"{Colors.GREEN}DM (Last turn):{Colors.RESET} {last_dm_message}")

        # Main game loop
        while True:
            player_input = input(f"\n{Colors.BLUE}> Your action: {Colors.RESET}")

            if player_input.lower() in ["quit", "exit"]:
                print(f"{Colors.CYAN}Thank you for playing! Farewell, adventurer!{Colors.RESET}")
                break
            elif player_input.lower() == "save":
                current_game_state["messages"] = messages
                save_game(current_game_state)
                continue # Skip sending to AI, go back to next player input
            elif player_input.lower() == "restart":
                print(f"\n{Colors.YELLOW}[Restarting campaign...]{Colors.RESET}")
                current_game_state = initial_game_state.copy()
                messages = current_game_state["messages"] # Crucial fix: re-assign 'messages'
                messages.append({'role': 'system', 'content': SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"})
                messages.append({'role': 'user', 'content': 'Begin the adventure.'})
                print(f"\n{Colors.MAGENTA}DM (thinking...){Colors.RESET}\n")
                response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)
                dm_response_content = response['message']['content']
                print(f"{Colors.GREEN}DM:{Colors.RESET} {dm_response_content}")
                messages.append({'role': 'assistant', 'content': dm_response_content}) # Fix: Ensure JSON serializable
                save_game(current_game_state)
                continue # Skip the rest of the loop, go back to next player input

            current_game_state["game_time"] += 1

            # --- Handle Player Actions (NEW BLOCK) ---
            # Default response if no specific action is handled
            ai_input_message = player_input
            action_handled = False

            # Simple movement parsing
            player_input_lower = player_input.lower()
            movement_directions = ["north", "south", "east", "west", "up", "down"]
            detected_direction = None

            for direction in movement_directions:
                if f"go {direction}" in player_input_lower or \
                f"move {direction}" in player_input_lower or \
                player_input_lower == direction: # Allows just typing "north"
                    detected_direction = direction
                    break

            if detected_direction:
                new_location_name = move_player(current_game_state, detected_direction)
                # Formulate the message to the AI after state change
                ai_input_message = f"I moved {detected_direction}. I am now in '{new_location_name}'. Describe this new location."
                action_handled = True
            # --- END NEW BLOCK ---

            # Update the system prompt with new game state (always, as game_state might change)
            messages[0]['content'] = SYSTEM_PROMPT + f"\nCurrent Game State: {current_game_state}"

            # Use ai_input_message instead of raw player_input for AI's turn
            messages.append({'role': 'user', 'content': ai_input_message}) # MODIFIED THIS LINE

            print(f"\n{Colors.MAGENTA}DM (thinking...){Colors.RESET}\n")
            response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)

            dm_response_content = response['message']['content']
            print(f"{Colors.GREEN}DM: {dm_response_content}.{Colors.RESET}")

            messages.append({'role': 'assistant', 'content': dm_response_content}) # Fix: Ensure JSON serializable

    except Exception as e:
        print(f"{Colors.RED}\nAn error occurred: {e}{Colors.RESET}")
        print(f"{Colors.RED}Please ensure Ollama is running and the model is downloaded correctly.{Colors.RESET}")
        print(f"{Colors.RED}You tried to use model: {LOCAL_MODEL_NAME}{Colors.RESET}")
        print(f"{Colors.RED}You can check installed models with 'ollama list' in your terminal.{Colors.RESET}")

if __name__ == "__main__":
    run_game()