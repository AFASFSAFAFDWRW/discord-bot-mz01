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

# ---------- КОМАНДЫ ----------
@bot.command(name="команды")
async def commands_list(ctx):
    embed = discord.Embed(
        title="📌 Команды Государственного помощника",
        description=(
            "**!предупредить @пользователь причина** — "
            "выдаёт устное предупреждение.\n\n"

            "**!МЗ @пользователь** — "
            "зачисляет пользователя в Министерство Здравоохранения, "
            "выдавая стартовые роли фракции.\n\n"

            "**!смена ника @пользователь новый_ник** — "
            "изменяет ник пользователя.\n\n"

            "**!уволить @пользователь причина** — "
            "увольняет сотрудника, снимая все роли и оставляя «Гражданский».\n\n"

            "**!аннулировать роли @пользователь** — "
            "аннулирует все роли и оставляет «Гражданский»."
        ),
        color=discord.Color.blue()
    )

    embed.set_footer(
        text="Система управления персоналом",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- ПРЕДУПРЕЖДЕНИЕ ----------
@bot.command()
@commands.has_role(ALLOWED_ROLE)
async def предупредить(ctx, member: discord.Member, *, reason: str):
    role = discord.utils.get(ctx.guild.roles, name=WARNING_ROLE)
    if not role:
        await ctx.send("❌ Роль 'Устное предупреждение' не найдена.")
        return

    await member.add_roles(role)

    await ctx.send(
        f"⚠️ {member.mention} получил устное предупреждение.\n"
        f"**Причина:** {reason}"
    )

# ---------- МЗ (ПЕРЕРАБОТАНО) ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):

    roles_to_add = []
    missing_roles = []

    for role_name in MZ_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            roles_to_add.append(role)
        else:
            missing_roles.append(role_name)

    if missing_roles:
        await ctx.send(
            f"❌ Не найдены роли:\n" + "\n".join(f"- {r}" for r in missing_roles)
        )
        return

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if civil_role and civil_role in member.roles:
        await member.remove_roles(civil_role)

    await member.add_roles(*roles_to_add)

    embed = discord.Embed(
        description=(
            "📝 **Лог: Зачисление во фракцию**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📌 Фракция: {FRACTION_NAME}\n\n"
            "**Выданные роли:**\n" +
            "\n".join(f"- {r.name}" for r in roles_to_add)
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- СМЕНА НИКА ----------
@bot.command(name="смена")
@has_any_role()
async def change_nick(ctx, action: str, member: discord.Member, *, new_nick: str):
    if action.lower() != "ника":
        await ctx.send("❌ Использование: !смена ника @пользователь НовыйНик")
        return

    old_nick = member.display_name

    try:
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        await ctx.send("❌ Нет прав на смену ника.")
        return

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

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- УВОЛИТЬ ----------
@bot.command(name="уволить")
@has_any_role()
async def fire(ctx, member: discord.Member, *, reason: str):

    member_role_names = [role.name for role in member.roles]

    if DOCS_ROLE in member_role_names:
        await ctx.send(
            embed=discord.Embed(
                description=(
                    "🚫 **Данное действие невозможно.**\n\n"
                    f"У сотрудника **{member.display_name}** отсутствует документация."
                ),
                color=discord.Color.red()
            )
        )
        return

    active_blocks = [r for r in member_role_names if r in BLOCK_FIRE_ROLES]
    if active_blocks:
        await ctx.send(
            embed=discord.Embed(
                description=(
                    "🚫 **Данное действие невозможно.**\n\n"
                    "**Активные взыскания:**\n" +
                    "\n".join(f"- {r}" for r in active_blocks)
                ),
                color=discord.Color.red()
            )
        )
        return

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil_role])

    embed = discord.Embed(
        description=(
            "📝 **Лог: Увольнение**\n\n"
            f"👤 {member.mention}\n"
            f"Ник: {member.display_name}\n"
            f"ID: {member.id}\n"
            f"Причина: {reason}"
        ),
        color=discord.Color.red()
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- АННУЛИРОВАТЬ ----------
@bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):
    if action.lower() != "роли":
        return

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    await member.edit(roles=[civil_role])

    embed = discord.Embed(
        description=(
            "📝 **Лог: Аннулирование ролей**\n\n"
            f"👤 {member.mention}\n"
            f"Ник: {member.display_name}\n"
            f"ID: {member.id}"
        ),
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
