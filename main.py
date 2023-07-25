import discord
import requests
import json

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + "-" + json_data[0]['a']
    return (quote)


def get_products():
    response = requests.get("https://aditya-impact.onrender.com/api/users")
    json_data = json.loads(response.text)
    image = json_data[0]["image"]
    name=json_data[0]["name"]
    return [image,name]


@client.event
async def on_ready():
    print("we have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$Inspire'):
        quote = get_quote()
        await message.channel.send(quote)

    if message.content.startswith('$image'):
        data = get_products()
        embed = discord.Embed(title="User")
        embed.set_image(url=data[0])
        embed.set_footer(text=data[1])
        embed.add_field("User-Name",data[1],inline=True)
        await message.channel.send(embed=embed)


client.run("MTEzMTk2NTA1ODY5MjQxOTYxNA.GB_aRI.Dfn6flXjbrDHAd77_xX2GQIyVgyCzrNnkO1dDU")