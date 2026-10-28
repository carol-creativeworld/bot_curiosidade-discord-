import os
import asyncio
import discord
from discord.ext import commands
import requests
import pyttsx3
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurando o sintetizador de voz local (caso rode localmente)
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

voices = engine.getProperty('voices')
# Escolhendo uma voz em português se disponível
for voice in voices:
    if "portuguese" in voice.name.lower() or "brazil" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
else:
    if voices:
        engine.setProperty('voice', voices[0].id)

# Inicializando o tradutor uma única vez no começo do arquivo
tradutor = GoogleTranslator(source='en', target='pt')

# Permissões do bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def get_fact() -> str:
    base_url = "https://uselessfacts.jsph.pl/random.json?language=en"
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            fato_ingles = data.get("text", "")

            if fato_ingles:
                # Usando o tradutor global criado no início
                fato_traduzido = tradutor.translate(fato_ingles)
                return fato_traduzido
            else:
                print("Erro: Texto do fato vazio.")
                return "Não foi possível encontrar um fato no momento."
        else:
                print(
                    "Erro ao conectar com o serviço de fatos. "
                    f"Status: {response.status_code}"
                )
            return "Erro ao conectar com o serviço de fatos, tente novamente depois."
    except Exception as error:
        print(f"Erro ao buscar ou traduzir o fato: {error}")
        return "Ocorreu um erro ao buscar ou traduzir o fato."


def falar_texto(texto: str):
    """Função auxiliar para rodar a voz local de forma segura."""
    try:
        engine.say(texto)
        engine.runAndWait()
    except Exception as error:
        print(f"Erro ao sintetizar voz: {error}")


# Eventos
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


# Comando !start
@bot.command()
async def start(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! 👋 Bem-vindo ao servidor, meu nome é Kay!")


# Comando !fact com cooldown de 5 segundos por usuário
@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def fact(ctx):
    fato = await asyncio.to_thread(get_fact)
    await ctx.send(f"**Fato aleatório:** {fato}")

    # Executando a voz localmente em uma thread separada
    await asyncio.to_thread(falar_texto, fato)

# Tratando os erros para o cooldown
@fact.error
async def fact_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Calma aí! 🕒 Aguarde {error.retry_after:.1f} segundos para usar "
            "o comando novamente.",
            delete_after=5,
        )

# Executando o bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print(
            "Erro: Token do bot não encontrado! "
            "Verifique seu arquivo .env."
        )
    else:
        bot.run(TOKEN)