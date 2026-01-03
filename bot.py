import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os

# ---------- CHECK ----------
def has_any_role():
    async def predicate(ctx):
        return any(
            role.name in ("[АБ] Администрация Больницы", "Заведующие / Зам. Заведующие")
            for role in ctx.author.roles
        )
    return commands.check(predicate)

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- КОНСТАНТЫ ----------
ALLOWED_ROLE = "[АБ] Администрация Больницы"
WARNING_ROLE = "Устное предупреждение"

MZ_ROLE = "Министерство Здравоохранения"
ROLE_1 = "[АБ] Администрация Больницы"
ROLE_2 = "Заведующие / Зам. Заведующие"

CIVIL_ROLE = "Гражданский"
FRACTION_NAME = "Министерство Здравоохранения"

# ---------- CHECK ----------
def has_any_role():
    async def predicate(ctx):
        return any(
            role.name in (ROLE_1, ROLE_2)
            for role in ctx.author.roles
        )
    return commands.check(predicate)

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

# ---------- КОМАНДЫ ----------

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

# ---------- МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):

    # Удаляем сообщение с командой
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    role = discord.utils.get(ctx.guild.roles, name=MZ_ROLE)

    if role is None:
        await ctx.send("❌ Роль **Министерство Здравоохранения** не найдена.")
        return

    await member.add_roles(role)

    embed = discord.Embed(
        description=(
            "📝 **Лог:** Добавление роли пользователю\n\n"
            f"✅ **Роль успешно добавлена**\n\n"
            f"💊 **Роль фракции** <@&{role.id}>\n"
            f"👤 **Пользователь:** {member.mention}"
        ),
        color=discord.Color.green()
    )

    embed.set_author(
        name="Система управления ролями",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    embed.set_footer(
        text=f"Выдал: {ctx.author}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- СМЕНА НИКА ----------
@bot.command(name="смена")
@has_any_role()
async def change_nick(ctx, action: str, member: discord.Member, *, new_nick: str):
    if action.lower() != "ника":
        await ctx.send("❌ Использование: !смена ника @пользователь Новый ник")
        return

    old_nick = member.display_name

    try:
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        await ctx.send("❌ У меня нет прав для смены ника.")
        return

    moscow_tz = timezone(timedelta(hours=3))
    now = datetime.now(moscow_tz)

    embed = discord.Embed(
        description=(
            "📝 **Лог:** Изменение имени пользователя\n"
            f"👤 **Пользователь:** {member.mention}\n"
            f"**Старое имя:** {old_nick}\n"
            f"**Новое имя:** {new_nick}\n"
            f"**Дата:** {now.strftime('%d.%m.%Y')}\n"
            f"**Время:** {now.strftime('%H:%M')} (МСК)"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=f"Изменил: {ctx.author}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

@bot.command(name="уволить")
@has_any_role()
async def fire(ctx, member: discord.Member, *, reason: str):

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    guild = ctx.guild
    civil_role = discord.utils.get(guild.roles, name=CIVIL_ROLE)

    if civil_role is None:
        await ctx.send("❌ Роль **Гражданский** не найдена.")
        return

    roles_to_remove = [
        role for role in member.roles
        if role != guild.default_role
    ]

    try:
        await member.remove_roles(*roles_to_remove)
        await member.add_roles(civil_role)
    except discord.Forbidden:
        await ctx.send("❌ Недостаточно прав для управления ролями.")
        return

    embed = discord.Embed(
        description=(
            "📝 **Лог: Увольнение сотрудника**\n\n"
            f"👤 **Сотрудник:** {member.mention}\n"
            f"Данные о сотруднике: {member.display_name}\n"
            f"ID пользователя: {member.id}\n\n"
            "📄 **Статус:** Уволен\n"
            f"📝 **Причина:** {reason}"
        ),
        color=discord.Color.red()
    )

    embed.set_author(
        name="Система управления персоналом",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

    try:
        await member.send(
            f"Уважаемый {member.display_name},\n\n"
            f"Вы были уволены из фракции {FRACTION_NAME}.\n"
            f"Исполнитель: {ctx.author.display_name}\n"
            f"Причина: {reason}"
        )
    except discord.Forbidden:
        pass

  @bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):

    if action.lower() != "роли":
        await ctx.send("❌ Использование: !аннулировать роли @пользователь")
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    guild = ctx.guild
    civil_role = discord.utils.get(guild.roles, name=CIVIL_ROLE)

    if civil_role is None:
        await ctx.send("❌ Роль **Гражданский** не найдена.")
        return

    roles_to_remove = [
        role for role in member.roles
        if role != guild.default_role
    ]

    try:
        await member.remove_roles(*roles_to_remove)
        await member.add_roles(civil_role)
    except discord.Forbidden:
        await ctx.send("❌ Недостаточно прав для управления ролями.")
        return

    embed = discord.Embed(
        description=(
            "📝 **Лог: Аннулирование ролей**\n\n"
            "✅ **Роли успешно аннулированы**\n\n"
            f"👤 **Пользователь:** {member.mention}\n"
            f"Данные о сотруднике: {member.display_name}\n"
            f"ID пользователя: {member.id}"
        ),
        color=discord.Color.orange()
    )

    embed.set_author(
        name="Система управления персоналом",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    embed.set_footer(
        text=f"Исполнитель: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )

    await ctx.send(embed=embed)

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
