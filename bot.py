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
MZ_ROLE = "Министерство Здравоохранения"
CIVIL_ROLE = "Гражданский"
FRACTION_NAME = "Министерство Здравоохранения"

BLOCK_FIRE_ROLES = [
    "[-] Документы не утверждены",
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

# ---------- AUTO DELETE COMMAND ----------
@bot.event
async def on_command(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

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

# ---------- МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=MZ_ROLE)
    if not role:
        await ctx.send("❌ Роль МЗ не найдена.")
        return

    await member.add_roles(role)

    embed = discord.Embed(
        description=(
            "📝 **Лог:** Добавление роли\n\n"
            f"💊 **Роль:** <@&{role.id}>\n"
            f"👤 **Пользователь:** {member.mention}"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Выдал: {ctx.author.display_name}",
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
            "📝 **Лог:** Смена ника\n"
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
    active_blocks = [
        role.name for role in member.roles
        if role.name in BLOCK_FIRE_ROLES
    ]

    if active_blocks:
        embed = discord.Embed(
            description=(
                "🚫 **Данное действие невозможно.**\n\n"
                f"У сотрудника **{member.display_name}** присутствует активное дисциплинарное взыскание.\n\n"
                "**Дисциплинарное взыскание в виде:**\n"
                + "\n".join(f"- {r}" for r in active_blocks) +
                "\n\nДля осуществления данного действия, сотруднику необходимо снять все активные наказания."
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if not civil_role:
        await ctx.send("❌ Роль 'Гражданский' не найдена.")
        return

    await member.edit(roles=[civil_role])

    embed = discord.Embed(
        description=(
            "📝 **Лог: Увольнение**\n\n"
            f"👤 {member.mention}\n"
            f"Ник: {member.display_name}\n"
            f"ID: {member.id}\n"
            f"📄 Статус: Уволен\n"
            f"📝 Причина: {reason}"
        ),
        color=discord.Color.red()
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

    try:
        await member.send(
            f"Вы были уволены из фракции **{FRACTION_NAME}**.\n"
            f"Исполнитель: {ctx.author.display_name}\n"
            f"Причина: {reason}"
        )
    except discord.Forbidden:
        pass

# ---------- АННУЛИРОВАТЬ ----------
@bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):
    if action.lower() != "роли":
        await ctx.send("❌ Использование: !аннулировать роли @пользователь")
        return

    civil_role = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
    if not civil_role:
        await ctx.send("❌ Роль 'Гражданский' не найдена.")
        return

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
