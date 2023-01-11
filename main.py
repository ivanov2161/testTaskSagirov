import asyncio

from service import run_polling
from browser import check_available

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.create_task(run_polling())
    loop.create_task(check_available())
    loop.run_forever()
