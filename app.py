import chainlit as cl
import locale

@cl.on_chat_start
async def start():
    system_locale = locale.getdefaultlocale()[0]
    if system_locale.startswith('de'):
        await cl.Message("Willkommen bei Tohecho! Wie kann ich Ihnen heute helfen?").send()
    else:
        await cl.Message("Welcome to tohecho! How can I assist you today?").send()

@cl.on_message
async def main(message: str):
    system_locale = locale.getdefaultlocale()[0]
    if system_locale.startswith('de'):
        await cl.Message(f"Antwort: {message}").send()
    else:
        await cl.Message(f"Echo: {message}").send()
