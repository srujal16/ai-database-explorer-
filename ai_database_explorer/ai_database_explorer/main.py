"""
main.py
Entry point for the AI Database Explorer chatbot.

Run with:
    python main.py
"""

from db_setup import build_database, DB_NAME
from chatbot import Chatbot, WELCOME_TEXT


def main():
    build_database(DB_NAME, overwrite=False)
    bot = Chatbot(DB_NAME)

    print(WELCOME_TEXT)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break

        if not user_input:
            continue

        reply = bot.respond(user_input)

        if reply == "__EXIT__":
            print("Bot: Goodbye! 👋")
            break

        print(f"Bot: {reply}\n")


if __name__ == "__main__":
    main()
