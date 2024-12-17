import asyncpg
import asyncio


async def main():
    conn = await asyncpg.connect("postgresql://user:pass@localhost:5432/db")
    print(conn)


if __name__ == "__main__":
    asyncio.run(main())
