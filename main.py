import ollama

# --- Configuration ---
LOCAL_MODEL_NAME = "llama3" # Make sure this matches the model you pulled (e.g., "llama3", "mistral", "phi3")

# --- DM Persona and Initial Scenario ---
# This is the "system prompt" that sets the AI's role and initial instructions.
SYSTEM_PROMPT = """
You are an impartial Dungeon Master for a text-based adventure game.
Your role is to describe the environment, react to player actions, and narrate the outcome.
You will primarily interact with the player, taking their input and describing the world.
Keep your descriptions concise, vivid, and engaging, typically 2-4 sentences.
Start by describing a simple, small, abandoned room.
"""

# --- Game Loop ---
def run_game():
    print("Welcome to your text adventure!")
    print("Type 'quit' or 'exit' to end the game.")

    # Initialize conversation history with the system prompt
    # The 'messages' list is crucial for maintaining conversation context.
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        # A user message to "kick off" the DM's initial description
        {'role': 'user', 'content': 'Begin the adventure.'}
    ]

    try:
        # Send the initial 'Begin the adventure' message to get the first room description
        print("\nDM (thinking...)\n") # Added this for user feedback while AI generates
        response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)
        dm_response_content = response['message']['content']
        print("DM:", dm_response_content)
        messages.append(response['message']) # Add DM's response to history

        while True:
            player_input = input("\n> Your action: ")

            if player_input.lower() in ["quit", "exit"]:
                print("Thank you for playing! Farewell, adventurer!")
                break

            # Add player's input to the conversation history
            messages.append({'role': 'user', 'content': player_input})

            # Send the full conversation history to Ollama
            print("\nDM (thinking...)\n") # Added this for user feedback while AI generates
            response = ollama.chat(model=LOCAL_MODEL_NAME, messages=messages)

            # Extract the DM's response and print it
            dm_response_content = response['message']['content']
            print("DM:", dm_response_content)

            # Add the DM's response to the conversation history
            messages.append(response['message'])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure Ollama is running and the model is downloaded correctly.")
        print(f"You tried to use model: {LOCAL_MODEL_NAME}")
        print("You can check installed models with 'ollama list' in your terminal.")

if __name__ == "__main__":
    run_game()