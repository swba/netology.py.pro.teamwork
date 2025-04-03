from environs import env

from src.bot import Bot

if __name__ == "__main__":
    # Read environment variables.
    env.read_env()

    # Start the bot.
    bot = Bot()
    bot.run()
