import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os
import asyncio  # ← ДОБАВЛЕНО ДЛЯ !мут

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
            "**!мут @пользователь минуты причина** — мут пользователя"
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# =====================================================
# ==================== МУТ ============================
# =====================================================

@bot.command(name="мут")
@has_any_role()
async def mute(ctx, member: discord.Member, minutes: int, *, reason: str):
    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")

    if not mute_role:
        await ctx.send("❌ Роль `Mute` не найдена.")
        return

    if mute_role in member.roles:
        await ctx.send("❌ Пользователь уже в муте.")
        return

    await member.add_roles(mute_role)

    embed = discord.Embed(
        description=(
            "📝 **Лог: Мут пользователя**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"⏳ Время: {minutes} мин.\n"
            f"📄 Причина: {reason}\n\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

    await asyncio.sleep(minutes * 60)

    if mute_role in member.roles:
        await member.remove_roles(mute_role)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
