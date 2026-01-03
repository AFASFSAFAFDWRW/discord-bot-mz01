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
            "**!МЗ @пользователь** — зачисление\n\n"
            "**!смена ника @пользователь новый_ник** — смена ника\n\n"
            "**!уволить @пользователь причина** — увольнение\n\n"
            "**!аннулировать роли @пользователь** — аннулирование ролей"
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

    # 1️⃣ ТЕКУЩИЙ ЧАТ
    embed_main = discord.Embed(
        description=(
            "📝 **Лог: Добавление ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"🎖 Роли: {' '.join(r.mention for r in roles_to_add)}\n\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed_main)

    # 2️⃣ ДОКУМЕНТООБОРОТ
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_MZ_CHANNEL)
    if log_channel:
        embed_log = discord.Embed(
            description=(
                "📄 **Документооборот**\n\n"
                f"Сотрудник: {member.mention}\n"
                f"Ник: {member.display_name}\n"
                f"ID: {member.id}\n"
                f"Статус: Зачислен"
            ),
            color=discord.Color.blue()
        )
        await log_channel.send(embed=embed_log)

# ---------- СМЕНА НИКА ----------
@bot.command(name="смена")
@has_any_role()
async def change_nick(ctx, action: str, member: discord.Member, *, new_nick: str):
    if action.lower() != "ника":
        return

    old_nick = member.display_name
    await member.edit(nick=new_nick)

    now = datetime.now(timezone(timedelta(hours=3)))

    embed = discord.Embed(
        description=(
            "📝 **Лог: Смена ника**\n\n"
            f"👤 {member.mention}\n"
            f"Старый: {old_nick}\n"
            f"Новый: {new_nick}\n"
            f"Дата: {now:%d.%m.%Y %H:%M} МСК"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Исполнитель: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# ---------- УВОЛИТЬ ----------
@bot.command(name="уволить")
@has_any_role()
async def fire(ctx, member: discord.Member, *, reason: str):

    role_names = [r.name for r in member.roles]

    # ❌ НЕТ ДОКУМЕНТОВ
    if DOCS_ROLE in role_names:
        await ctx.send(embed=discord.Embed(
            title="🚫 Увольнение невозможно",
            description=f"👤 {member.mention}\nПричина: **Документы не утверждены**",
            color=discord.Color.red()
        ))
        return

    # ❌ ВЫГОВОРЫ
    blocked = [r for r in role_names if r in BLOCK_FIRE_ROLES]
    if blocked:
        await ctx.send(embed=discord.Embed(
            title="🚫 Увольнение невозможно",
            description=(
                f"👤 {member.mention}\n"
                f"Причина: **{', '.join(blocked)}**"
            ),
            color=discord.Color.red()
        ))
        return

    # ✅ УВОЛЬНЕНИЕ
    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil])

    # 1️⃣ ТЕКУЩИЙ ЧАТ
    embed_chat = discord.Embed(
        description=(
            "📝 **Лог: Увольнение**\n\n"
            f"👤 {member.mention}\n"
            f"Ник: {member.display_name}\n"
            f"ID: {member.id}\n"
            f"Причина: {reason}"
        ),
        color=discord.Color.red()
    )
    embed_chat.set_footer(text=f"Исполнитель: {ctx.author.display_name}")
    await ctx.send(embed=embed_chat)

    # 2️⃣ ДОКУМЕНТООБОРОТ
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_FIRE_CHANNEL)
    if log_channel:
        embed_log = discord.Embed(
            description=(
                "📄 **Документооборот (увольнение)**\n\n"
                f"Сотрудник: {member.mention}\n"
                f"Ник: {member.display_name}\n"
                f"ID: {member.id}\n"
                f"Причина: {reason}\n\n"
                f"Исполнитель: {ctx.author.display_name}"
            ),
            color=discord.Color.dark_red()
        )
        await log_channel.send(embed=embed_log)

    # 📩 ЛИЧНОЕ СООБЩЕНИЕ
    try:
        await member.send(embed=discord.Embed(
            title="📄 Уведомление об увольнении",
            description=(
                f"Вы были уволены из фракции **{FRACTION_NAME}**.\n\n"
                f"Причина: **{reason}**\n"
                f"Дата: {datetime.now(timezone(timedelta(hours=3))):%d.%m.%Y %H:%M} МСК\n"
                f"Вас уволил: {ctx.author.mention}"
            ),
            color=discord.Color.dark_red()
        ))
    except discord.Forbidden:
        pass

# ---------- АННУЛИРОВАТЬ ----------
@bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):
    if action.lower() != "роли":
        return

    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil])

    embed = discord.Embed(
        description=(
            "📝 **Лог: Аннулирование ролей**\n\n"
            f"👤 {member.mention}\n"
            f"Ник: {member.display_name}\n"
            f"ID: {member.id}"
        ),
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Исполнитель: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
