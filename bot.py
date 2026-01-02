import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLE = "[АБ] Администрация Больницы"
WARNING_ROLE = "Устное предупреждение"

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.command()
@commands.has_role(ALLOWED_ROLE)
async def предупредить(ctx, member: discord.Member, *, reason: str):
    role = discord.utils.get(ctx.guild.roles, name=WARNING_ROLE)

    if role is None:
        await ctx.send("❌ Роль 'Устное предупреждение' не найдена.")
        return

    await member.add_roles(role)

    await ctx.send(
        f"⚠️ Сотруднику {member.mention} было выдано Устное предупреждение.\n"
        f"**Причина:** {reason}"
    )

@предупредить.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ У вас нет прав на эту команду.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Использование: !предупредить @пользователь причина")

import os
bot.run(os.getenv("TOKEN"))
