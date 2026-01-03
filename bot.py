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

# ---------- КОНСТАНТЫ ----------
CIVIL_ROLE = "Гражданский"
FRACTION_NAME = "Министерство Здравоохранения"
DOCS_ROLE = "[-] Документы не утверждены"

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

# ================= кмд командыы =====================

@bot.command(name="команды")
async def commands_list(ctx):
    embed = discord.Embed(
        title="📌 Команды Государственного помощника",
        description=(
            "**!правительство @пользователь** — выдача роли Правительство\n\n"
            "**!ФСБ @пользователь** — выдача роли ФСБ\n\n"
            "**!МО @пользователь** — выдача роли МО\n\n"
            "**!МВД @пользователь** — выдача роли МВД\n\n"
            "**!ФСИН @пользователь** — выдача роли ФСИН\n\n"
            "**!МЗ @пользователь** — принятие во фракцию МЗ\n\n"
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

# =====================================================
# =================== КОМАНДЫ =========================
# =====================================================

@bot.command(name="МЗ")
@has_any_role()
async def mz(ctx, member: discord.Member):
    guild = ctx.guild
    intern_role = discord.utils.get(
    ctx.guild.roles,
    name="[ОИ] Отделение Интернатуры"
)

    mz_role = discord.utils.get(guild.roles, name="Министерство Здравоохранения")
    state_role = discord.utils.get(guild.roles, name="Государственная фракция")
    civil = discord.utils.get(guild.roles, name=CIVIL_ROLE)

    if not mz_role or not state_role:
        await ctx.send("❌ Не найдены необходимые роли.")
        return

    removed_roles = []

    if civil and civil in member.roles:
        removed_roles.append(civil)
        await member.remove_roles(civil)

    await member.add_roles(mz_role, state_role)

    removed_text = " ".join(r.mention for r in removed_roles) if removed_roles else "—"

    # ---------- ЛОГ В ТЕКУЩИЙ КАНАЛ ----------
    embed = discord.Embed(
        description=(
            "📝 **Лог: Добавление ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📌 Роли: {mz_role.mention} {state_role.mention}\n"
            f"❌ Снятые роли: {removed_text}\n\n"
            f"Выдал роли: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

    # ---------- ЛОГ В АУДИТ ----------
    audit_channel = discord.utils.get(
        guild.text_channels,
        name="кадровый-аудит-принятия-и-увольнения-сотрудников"
    )

    if audit_channel:
        now = discord.utils.utcnow()

        audit_embed = discord.Embed(
            description=(
                "📝 **Лог: Принятие во фракцию**\n"
                f"👤 Имя сотрудника: {member.display_name}\n"
                f"📗 В данный момент сотрудник в отделе: {intern_role.mention}\n"
                f"🗓️ Дата принятия: {now.strftime('%d.%m.%Y')}\n"
                f"⏳ Время принятия: {now.strftime('%H:%M')}\n"
                f"💼 Принимал во фракцию: {ctx.author.mention}"
            ),
            color=discord.Color.blue()
        )

        await audit_channel.send(embed=audit_embed)

# =====================================================
# ========== НОВЫЕ КОМАНДЫ ГОС ФРАКЦИЙ =================
# =====================================================

async def give_state_role(ctx, member, main_role_name):
    main_role = discord.utils.get(ctx.guild.roles, name=main_role_name)
    state_role = discord.utils.get(ctx.guild.roles, name="Государственная фракция")
    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)

    if not main_role:
        await ctx.send(f"❌ Роль `{main_role_name}` не найдена.")
        return

    if not state_role:
        await ctx.send("❌ Роль `Государственная фракция` не найдена.")
        return

    removed_roles = []

    if civil and civil in member.roles:
        removed_roles.append(civil)
        await member.remove_roles(civil)

    await member.add_roles(main_role, state_role)

    removed_text = " ".join(r.mention for r in removed_roles) if removed_roles else "—"

    embed = discord.Embed(
        description=(
            "📝 **Лог: Добавление ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📌 Роли: {main_role.mention} {state_role.mention}\n"
            f"❌ Снятые роли: {removed_text}\n\n"
            f"Выдал роли: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

@bot.command(name="правительство", aliases=["Правительство"])
@has_any_role()
async def government(ctx, member: discord.Member):
    await give_state_role(ctx, member, "Правительство")

@bot.command(name="фсб", aliases=["ФСБ"])
@has_any_role()
async def fsb(ctx, member: discord.Member):
    await give_state_role(ctx, member, "ФСБ")

@bot.command(name="мвд", aliases=["МВД"])
@has_any_role()
async def mvd(ctx, member: discord.Member):
    await give_state_role(ctx, member, "МВД")

@bot.command(name="мо", aliases=["МО"])
@has_any_role()
async def mo(ctx, member: discord.Member):
    await give_state_role(ctx, member, "МО")

@bot.command(name="фсин", aliases=["ФСИН"])
@has_any_role()
async def fsin(ctx, member: discord.Member):
    await give_state_role(ctx, member, "ФСИН")

@bot.command(name="трк", aliases=["ТРК"])
@has_any_role()
async def trk(ctx, member: discord.Member):
    await give_state_role(ctx, member, 'ТРК "Ритм"')

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
    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
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

    civil = discord.utils.get(ctx.guild.roles, name=CIVIL_ROLE)
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
