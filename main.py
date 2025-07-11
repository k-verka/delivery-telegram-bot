import asyncio
from bot import main as bot_main  # предполагаем, что в bot.py есть async def main()

async def run_bot():
    try:
        await bot_main()
    except Exception as e:
        with open("errlogs.txt", "a") as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_bot())

