import discord
from discord.ext import commands
import asyncio
import os

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# =====================================================
# =================== КОМАНДЫ =========================
# =====================================================

# ---------- !МЗ ----------
@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):
    roles_names = [
        "Министерство Здравоохранения",
        "Государственная фракция",
        "[-] Документы не утверждены",
        "[ОИ] Отделение Интернатуры",
        "Интерн",
        "Младший состав"
    ]

    roles = []
    for name in roles_names:
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            await ctx.send(f"❌ Роль `{name}` не найдена.")
            return
        roles.append(role)

    civil = discord.utils.get(ctx.guild.roles, name="Гражданский")
    if civil and civil in member.roles:
        await member.remove_roles(civil)

    await member.add_roles(*roles)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Зачисление в МЗ**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    ))

# ---------- ГОС РОЛИ ----------
async def give_role(ctx, member, role_name, title):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Роль `{role_name}` не найдена.")
        return

    await member.add_roles(role)

    await ctx.send(embed=discord.Embed(
        description=(
            f"📝 **Лог: {title}**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    ))

@bot.command(name="правительство")
@has_any_role()
async def gov(ctx, member: discord.Member):
    await give_role(ctx, member, "Правительство", "Выдача роли Правительство")

@bot.command(name="ФСБ")
@has_any_role()
async def fsb(ctx, member: discord.Member):
    await give_role(ctx, member, "ФСБ", "Выдача роли ФСБ")

@bot.command(name="МВД")
@has_any_role()
async def mvd(ctx, member: discord.Member):
    await give_role(ctx, member, "МВД", "Выдача роли МВД")

@bot.command(name="МО")
@has_any_role()
async def mo(ctx, member: discord.Member):
    await give_role(ctx, member, "МО", "Выдача роли МО")

@bot.command(name="ФСИН")
@has_any_role()
async def fsin(ctx, member: discord.Member):
    await give_role(ctx, member, "ФСИН", "Выдача роли ФСИН")

@bot.command(name="ТРК")
@has_any_role()
async def trk(ctx, member: discord.Member):
    await give_role(ctx, member, "ТРК "Ритм"", "Выдача роли ТРК "Ритм"")

# ---------- !смена ника ----------
@bot.command(name="смена")
@has_any_role()
async def change_nick(ctx, action: str, member: discord.Member, *, new_nick: str):
    if action.lower() != "ника":
        return

    old = member.display_name
    await member.edit(nick=new_nick)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Смена ника**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"Старый ник: {old}\n"
            f"Новый ник: {new_nick}"
        ),
        color=discord.Color.green()
    ))

# ---------- !уволить ----------
@bot.command(name="уволить")
@has_any_role()
async def fire(ctx, member: discord.Member, *, reason: str):
    civil = discord.utils.get(ctx.guild.roles, name="Гражданский")
    if civil:
        await member.edit(roles=[civil])

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Увольнение**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📄 Причина: {reason}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.red()
    ))

# ---------- !аннулировать роли ----------
@bot.command(name="аннулировать")
@has_any_role()
async def annul(ctx, action: str, member: discord.Member):
    if action.lower() != "роли":
        return

    civil = discord.utils.get(ctx.guild.roles, name="Гражданский")
    if civil:
        await member.edit(roles=[civil])

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Аннулирование ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.orange()
    ))

# ---------- !мут ----------
@bot.command(name="мут")
@has_any_role()
async def mute(ctx, member: discord.Member, minutes: int, *, reason: str):
    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
    if not mute_role:
        await ctx.send("❌ Роль `Mute` не найдена.")
        return

    await member.add_roles(mute_role)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Мут**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"⏳ Время: {minutes} мин\n"
            f"📄 Причина: {reason}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.orange()
    ))

    await asyncio.sleep(minutes * 60)

    if mute_role in member.roles:
        await member.remove_roles(mute_role)

# ---------- !снять мут ----------
@bot.command(name="снять")
@has_any_role()
async def unmute(ctx, action: str, member: discord.Member, *, reason: str):
    if action.lower() != "мут":
        return

    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
    if not mute_role:
        await ctx.send("❌ Роль `Mute` не найдена.")
        return

    await member.remove_roles(mute_role)

    await ctx.send(embed=discord.Embed(
        description=(
            "📝 **Лог: Снятие мута**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📄 Причина: {reason}\n"
            f"Исполнитель: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    ))

# ---------- RUN ----------
bot.run(os.getenv("TOKEN"))
