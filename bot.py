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

# роли для команды !МЗ
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

# ---------- МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):

    roles_to_add = []
    role_mentions = []

    for role_name in MZ_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"❌ Роль `{role_name}` не найдена.")
            return
        roles_to_add.append(role)
        role_mentions.append(role.mention)

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if civil_role and civil_role in member.roles:
        await member.remove_roles(civil_role)

    await member.add_roles(*roles_to_add)

    # ---------- СООБЩЕНИЕ В ТОТ ЖЕ ЧАТ ----------
    embed_local = discord.Embed(
        description=(
            "📝 **Лог: Добавление роли**\n\n"
            "💊 **Роль:**\n" +
            "\n".join(role_mentions) +
            f"\n\n👤 **Пользователь:** {member.mention}"
        ),
        color=discord.Color.green()
    )

    embed_local.set_footer(
        text=f"Выдал: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed_local)

    # ---------- ЛОГ В ДОКУМЕНТООБОРОТ ----------
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL_NAME)
    if not log_channel:
        return

    embed_log = discord.Embed(
        description=(
            "📝 **Лог: Зачисление во фракцию**\n\n"
            f"👤 **Пользователь:** {member.mention}\n"
            f"🏛 **Фракция:** {FRACTION_NAME}\n\n"
            "**Выданные роли:**\n" +
            "\n".join(role_mentions)
        ),
        color=discord.Color.blue()
    )

    embed_log.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await log_channel.send(embed=embed_log)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
