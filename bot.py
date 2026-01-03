import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- КОНСТАНТЫ ----------
ALLOWED_ROLE = "[АБ] Администрация Больницы"
WARNING_ROLE = "Устное предупреждение"
CIVIL_ROLE = "Гражданский"
FRACTION_NAME = "Министерство Здравоохранения"
DOCS_ROLE = "[-] Документы не утверждены"
LOG_CHANNEL_NAME = "документооборот-прибывших-граждан"

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
            role.name in (
                "[АБ] Администрация Больницы",
                "Заведующие / Зам. Заведующие"
            )
            for role in ctx.author.roles
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
        title="📌 Доступные команды",
        description=(
            "**!МЗ @пользователь** — зачисление во фракцию МЗ и выдача стартовых ролей\n"
            "**!команды** — список доступных команд"
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)

# ---------- МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):

    roles_to_add = []
    for role_name in MZ_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"❌ Роль `{role_name}` не найдена.")
            return
        roles_to_add.append(role)

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if civil_role and civil_role in member.roles:
        await member.remove_roles(civil_role)

    await member.add_roles(*roles_to_add)

    # ---------- 1 СООБЩЕНИЕ (ТЕКУЩИЙ ЧАТ) ----------
    roles_mentions = " ".join(role.mention for role in roles_to_add)

    embed_main = discord.Embed(
        description=(
            "📝 **Лог: Добавление роли**\n\n"
            f"💊 **Роль:** {roles_mentions}\n"
            f"👤 **Пользователь:** {member.mention}\n\n"
            f"**Выдал:** {ctx.author.mention}"
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed_main)

    # ---------- 2 СООБЩЕНИЕ (ЛОГ-КАНАЛ) ----------
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL_NAME)
    if log_channel:
        embed_log = discord.Embed(
            description=(
                "📝 **Лог: Зачисление во фракцию**\n\n"
                f"👤 **Пользователь:** {member.mention}\n"
                f"🏛 **Фракция:** {FRACTION_NAME}"
            ),
            color=discord.Color.blue()
        )
        await log_channel.send(embed=embed_log)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
