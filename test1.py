import asyncio
from googletrans import Translator


async def TranslateText(text):
  async with Translator() as translator:
    result = await translator.translate(text, src="en", dest="es")
    print(result.text)

asyncio.run(TranslateText("Hello"))