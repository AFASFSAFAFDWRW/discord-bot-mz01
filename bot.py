import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os
import asyncio

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- КОНСТАНТЫ ----------
CIVIL_ROLE = "Гражданский"
FRACTION_NAME = "Министерство Здравоохранения"
DOCS_ROLE = "[-] Документы не утверждены"

LOG_MZ_CHANNEL = "документооборот-прибывших-граждан"
LOG_FIRE_CHANNEL = "документооборот-уволенных-граждан"

MZ_ROLES = [
    "Министерство Здравоохранения",
    "Государственная фракция",
    "[-] Документы не утверждены",
    "[ОИ] Отделение Интернатуры",
    "Интерн",
    "Младший состав"
]

BLOCK_FIRE_ROLES = [
    "Запрет на увольнение",
    "Устное предупреждение",
    "Выговор 1/2",
    "Выговор 2/2",
    "Строгий выговор 1/2",
    "Строгий выговор 2/2",
    "Переаттестация"
]

# ---------- CHECK ----------
def has_any_role():
    async def predicate(ctx):
        return any(
            r.name in (
                "[АБ] Администрация Больницы",
                "Заведующие / Зам. Заведующие"
            )
            for r in ctx.author.roles
        )
    return commands.check(predicate)

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.event
async def on_command(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

# ---------- КОМАНДЫ ----------
@bot.command(name="команды")
async def commands_list(ctx):
    embed = discord.Embed(
        title="📌 Команды Государственного помощника",
        description=(
            "**!МЗ @пользователь** — зачисление в МЗ\n\n"
            "**!правительство @пользователь** — выдача роли Правительство\n\n"
            "**!ФСБ @пользователь** — выдача роли ФСБ\n\n"
            "**!МВД @пользователь** — выдача роли МВД\n\n"
            "**!МО @пользователь** — выдача роли МО\n\n"
            "**!ФСИН @пользователь** — выдача роли ФСИН\n\n"
            "**!ТРК @пользователь** — выдача роли ТРК «Ритм»\n\n"
            "**!смена ника @пользователь новый_ник** — смена ника\n\n"
            "**!уволить @пользователь причина** — увольнение\n\n"
            "**!аннулировать роли @пользователь** — аннулирование ролей\n\n"
            "**!мут @пользователь минуты причина** — мут\n\n"
            "**!снять мут @пользователь причина** — снять мут"
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# ---------- МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):
    roles_to_add = []
    for name in MZ_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            await ctx.send(f"❌ Роль `{name}` не найдена.")
            return
        roles_to_add.append(role)

    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if civil and civil in member.roles:
        await member.remove_roles(civil)

    await member.add_roles(*roles_to_add)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Добавление ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"🎖 Роли: {' '.join(r.mention for r in roles_to_add)}\n\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    ))

# ---------- СМЕНА НИКА ----------
@bot.command(name="смена")
@has_any_role()
async def change_nick(ctx, action: str, member: discord.Member, *, new_nick: str):
    if action.lower() != "ника":
        return

    old_nick = member.display_name
    await member.edit(nick=new_nick)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Смена ника**\n\n"
            f"👤 {member.mention}\n"
            f"Старый: {old_nick}\n"
            f"Новый: {new_nick}"
        ),
        color=discord.Color.green()
    ))

# ---------- УВОЛИТЬ ----------
@bot.command(name="уволить")
@has_any_role()
async def fire(ctx, member: discord.Member, *, reason: str):
    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil])

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Увольнение**\n\n"
            f"👤 {member.mention}\n"
            f"Причина: {reason}"
        ),
        color=discord.Color.red()
    ))

# ---------- АННУЛИРОВАТЬ ----------
@bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):
    if action.lower() != "роли":
        return

    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil])

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Аннулирование ролей**\n\n"
            f"👤 {member.mention}"
        ),
        color=discord.Color.orange()
    ))

# ---------- МУТ ----------
@bot.command(name="мут")
@has_any_role()
async def mute(ctx, member: discord.Member, minutes: int, *, reason: str):
    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
    await member.add_roles(mute_role)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Мут**\n\n"
            f"👤 {member.mention}\n"
            f"⏳ {minutes} мин\n"
            f"📄 {reason}"
        ),
        color=discord.Color.orange()
    ))

    await asyncio.sleep(minutes * 60)
    if mute_role in member.roles:
        await member.remove_roles(mute_role)

# ---------- СНЯТЬ МУТ ----------
@bot.command(name="снять")
@has_any_role()
async def unmute(ctx, action: str, member: discord.Member, *, reason: str):
    if action.lower() != "мут":
        return

    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
    await member.remove_roles(mute_role)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Снятие мута**\n\n"
            f"👤 {member.mention}\n"
            f"📄 {reason}"
        ),
        color=discord.Color.green()
    ))

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
