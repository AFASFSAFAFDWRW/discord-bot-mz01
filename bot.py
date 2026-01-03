import discord
from discord.ext import commands
import asyncio
import os
import json
from datetime import datetime, timedelta, timezone

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

# ================= НАСТРОЙКИ =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

MSK = timezone(timedelta(hours=3))
BANS_FILE = "bans.json"

CIVIL_ROLE = "Гражданский"

# ================= ПРОВЕРКА РОЛЕЙ =================

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

# ================= БАН-ФАЙЛ =================

def load_bans():
    try:
        with open(BANS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_bans(data):
    with open(BANS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.event
async def on_command(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

# ================= !бан =================

@bot.command(name="бан")
@has_any_role()
async def ban_request(ctx, member: discord.Member, days: int, *, reason: str):
    guild = ctx.guild
    chief_role = discord.utils.get(guild.roles, name="Главный врач")

    if not chief_role:
        await ctx.send("❌ Роль `Главный врач` не найдена.")
        return

    chief_member = next((m for m in guild.members if chief_role in m.roles), None)
    if not chief_member:
        await ctx.send("❌ Главный врач не найден.")
        return

    embed = discord.Embed(
        description=(
            f"⚠️ {chief_member.mention}\n\n"
            f"Попытка забанить пользователя {member.mention}\n"
            f"🆔 ID: `{member.id}`\n"
            f"🗓️ Дни бана: {days}\n"
            f"📄 Причина: {reason}\n\n"
            "Ожидается подтверждение Главного Врача.\n"
            "✅ — подтвердить | ❌ — отклонить"
        ),
        color=discord.Color.orange()
    )

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(r, u):
        return r.message.id == msg.id and u == chief_member and str(r.emoji) in ("✅", "❌")

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=86400, check=check)
    except asyncio.TimeoutError:
        await msg.edit(embed=discord.Embed(description="⌛ Время ожидания истекло.", color=discord.Color.red()))
        return

    if str(reaction.emoji) == "❌":
        await msg.edit(embed=discord.Embed(description="❌ Бан отклонён.", color=discord.Color.red()))
        return

    now = datetime.now(MSK)
    unban_time = now + timedelta(days=days)

    bans = load_bans()
    bans[str(member.id)] = {
        "username": str(member),
        "reason": reason,
        "ban_date": now.strftime("%d.%m.%Y %H:%M"),
        "unban_date": unban_time.strftime("%d.%m.%Y %H:%M"),
        "initiator": str(ctx.author)
    }
    save_bans(bans)

    try:
        await member.send(
            embed=discord.Embed(
                description=(
                    f"🔴 Вы заблокированы на {days} дней\n\n"
                    f"🆔 ID: `{member.id}`\n"
                    f"📄 Причина: {reason}\n"
                    f"📅 Бан: {bans[str(member.id)]['ban_date']}\n"
                    f"🟢 Разбан: {bans[str(member.id)]['unban_date']}\n\n"
                    "Подтвердил: Главный Врач"
                ),
                color=discord.Color.red()
            )
        )
    except:
        pass

    await guild.ban(member, reason=reason)
    await msg.edit(embed=discord.Embed(description="✅ Бан выполнен.", color=discord.Color.green()))

# ================= !разбан =================

@bot.command(name="разбан")
@has_any_role()
async def unban_request(ctx, user_id: int, *, reason: str):
    guild = ctx.guild
    chief_role = discord.utils.get(guild.roles, name="Главный врач")

    chief_member = next((m for m in guild.members if chief_role in m.roles), None)
    if not chief_member:
        await ctx.send("❌ Главный врач не найден.")
        return

    try:
        ban_entry = await guild.fetch_ban(discord.Object(id=user_id))
        user = ban_entry.user
    except:
        await ctx.send("❌ Пользователь не найден в бан-листе.")
        return

    msg = await ctx.send(
        embed=discord.Embed(
            description=(
                f"⚠️ {chief_member.mention}\n\n"
                f"Запрос на разбан `{user}`\n"
                f"🆔 ID: `{user_id}`\n"
                f"📄 Причина: {reason}\n\n"
                "✅ — подтвердить | ❌ — отклонить"
            ),
            color=discord.Color.orange()
        )
    )

    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(r, u):
        return r.message.id == msg.id and u == chief_member and str(r.emoji) in ("✅", "❌")

    reaction, _ = await bot.wait_for("reaction_add", check=check)

    if str(reaction.emoji) == "❌":
        await msg.edit(embed=discord.Embed(description="❌ Разбан отклонён.", color=discord.Color.red()))
        return

    await guild.unban(user, reason=reason)

    bans = load_bans()
    bans.pop(str(user_id), None)
    save_bans(bans)

    try:
        await user.send(
            embed=discord.Embed(
                description=(
                    "🟢 Вас разбанили.\n\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"📄 Причина: {reason}\n"
                    f"📅 Дата: {datetime.now(MSK).strftime('%d.%m.%Y %H:%M')} (МСК)"
                ),
                color=discord.Color.green()
            )
        )
    except:
        pass

    await msg.edit(embed=discord.Embed(description="✅ Разбан выполнен.", color=discord.Color.green()))

# ================= !банлист =================

@bot.command(name="банлист")
@has_any_role()
async def banlist(ctx):
    bans = load_bans()
    if not bans:
        await ctx.send("✅ Бан-лист пуст.")
        return

    text = "**Пользователи в блокировке:**\n\n"
    for i, (uid, data) in enumerate(bans.items(), 1):
        text += (
            f"{i}. {data['username']} | {uid} | "
            f"{data['ban_date']} | {data['unban_date']} | {data['reason']}\n"
        )

    await ctx.send(embed=discord.Embed(description=text, color=discord.Color.orange()))

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
            "**!чистка кол-во строк** — удаляет указанное кол-во сообщений в том чате, где приминилась данная команда\n\n"
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

    intern_dep = discord.utils.get(guild.roles, name="[ОИ] Отделение Интернатуры")
    mz_role = discord.utils.get(guild.roles, name="Министерство Здравоохранения")
    state_role = discord.utils.get(guild.roles, name="Государственная фракция")
    junior_role = discord.utils.get(guild.roles, name="Младший состав")
    intern_role = discord.utils.get(guild.roles, name="Интерн")
    docs_role = discord.utils.get(guild.roles, name="[-] Документы не утверждены")
    civil = discord.utils.get(guild.roles, name=CIVIL_ROLE)

    required_roles = [
        mz_role,
        state_role,
        junior_role,
        intern_role,
        intern_dep,
        docs_role
    ]

    if any(r is None for r in required_roles):
        await ctx.send("❌ Не найдены необходимые роли.")
        return

    removed_roles = []
    added_roles = []

    if civil and civil in member.roles:
        removed_roles.append(civil)
        await member.remove_roles(civil)

    await member.add_roles(*required_roles)
    added_roles.extend(required_roles)

    removed_text = " ".join(r.mention for r in removed_roles) if removed_roles else "—"
    added_text = " ".join(r.mention for r in added_roles)

    # ---------- ЛОГ В ТЕКУЩИЙ КАНАЛ ----------
    embed = discord.Embed(
        description=(
            "📝 **Лог: Добавление ролей**\n\n"
            f"👤 Пользователь: {member.mention}\n"
            f"📌 Роли: {added_text}\n"
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
                f"📗 В данный момент сотрудник в отделе: {intern_dep.mention}\n"
                f"🗓️ Дата принятия: {now.strftime('%d.%m.%Y')}\n"
                f"⏳ Время принятия: {now.strftime('%H:%M')}\n"
                f"💼 Принимал во фракцию: {ctx.author.mention}"
            ),
            color=discord.Color.blue()
        )

        await audit_channel.send(embed=audit_embed)

# ====================== !бан ========================

from datetime import datetime, timedelta, timezone

MSK = timezone(timedelta(hours=3))

@bot.command(name="бан")
@has_any_role()
async def ban_request(ctx, member: discord.Member, days: int, *, reason: str):
    guild = ctx.guild

    chief_role = discord.utils.get(guild.roles, name="Главный врач")
    if not chief_role:
        await ctx.send("❌ Роль `Главный врач` не найдена.")
        return

    chief_member = None
    for m in guild.members:
        if chief_role in m.roles:
            chief_member = m
            break

    if not chief_member:
        await ctx.send("❌ Не найден пользователь с ролью `Главный врач`.")
        return

    request_embed = discord.Embed(
        description=(
            f"⚠️ {chief_member.mention}\n\n"
            f"Попытка забанить пользователя {member.mention}\n"
            f"🆔 **ID пользователя:** `{member.id}`\n\n"
            f"🗓️ **Дни бана:** {days}\n"
            f"📄 **Причина бана:** {reason}\n\n"
            "Данный запрос на блокировку пользователя Discord ожидает личного подтверждения от Главного Врача.\n\n"
            "🔔 **Подсказка Главному Врачу:**\n"
            "Нажмите ✅ — подтвердить бан\n"
            "Нажмите ❌ — отклонить бан"
        ),
        color=discord.Color.orange()
    )

    msg = await ctx.send(embed=request_embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            reaction.message.id == msg.id
            and user == chief_member
            and str(reaction.emoji) in ("✅", "❌")
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=86400, check=check)
    except asyncio.TimeoutError:
        await msg.edit(
            embed=discord.Embed(
                description="⌛ Запрос на бан был автоматически отменён (истекло время ожидания).",
                color=discord.Color.red()
            )
        )
        return

    if str(reaction.emoji) == "❌":
        await msg.edit(
            embed=discord.Embed(
                description=(
                    "❌ **Бан отклонён.**\n\n"
                    f"Пользователь: {member.mention}\n"
                    f"🆔 ID пользователя: `{member.id}`\n\n"
                    f"Решение принял: {chief_member.mention}"
                ),
                color=discord.Color.red()
            )
        )
        return

    now = datetime.now(MSK)
    unban_time = now + timedelta(days=days)

    try:
        dm_embed = discord.Embed(
            description=(
                f"🔴 **Вас выгнали и заблокировали на {days} дней из Discord сервера "
                f"фракции `Министерство Здравоохранения`.**\n\n"
                f"🆔 **Ваш ID:** `{member.id}`\n"
                f"📄 **Причина:** {reason}\n\n"
                f"👤 **Инициатор блокировки:** {ctx.author}\n"
                f"✅ **Подтвердил блокировку:** Главный Врач\n\n"
                f"📅 **Дата блокировки:** {now.strftime('%d.%m.%Y')}\n"
                f"⏰ **Время блокировки:** {now.strftime('%H:%M')} (МСК)\n\n"
                f"🟢 **Дата и время разблокировки:** "
                f"{unban_time.strftime('%d.%m.%Y %H:%M')} (МСК)\n\n"
                "В случае несогласия вы можете обратиться в раздел жалоб."
            ),
            color=discord.Color.red()
        )
        await member.send(embed=dm_embed)
    except:
        pass

    await guild.ban(
        member,
        reason=f"{reason} | Инициатор: {ctx.author} | Подтвердил: Главный Врач",
        delete_message_days=0
    )

    await msg.edit(
        embed=discord.Embed(
            description=(
                "✅ **Бан подтверждён и выполнен.**\n\n"
                f"👤 Пользователь: {member}\n"
                f"🆔 ID пользователя: `{member.id}`\n"
                f"🗓️ Срок: {days} дней\n"
                f"📄 Причина: {reason}\n\n"
                f"Инициатор: {ctx.author.mention}\n"
                f"Подтвердил блокировку: {chief_member.mention}"
            ),
            color=discord.Color.green()
        )
    )

# ================== !разбан =========================

@bot.command(name="разбан")
@has_any_role()
async def unban_request(ctx, user_id: int, *, reason: str):
    guild = ctx.guild

    chief_role = discord.utils.get(guild.roles, name="Главный врач")
    if not chief_role:
        await ctx.send("❌ Роль `Главный врач` не найдена.")
        return

    chief_member = None
    for m in guild.members:
        if chief_role in m.roles:
            chief_member = m
            break

    if not chief_member:
        await ctx.send("❌ Не найден пользователь с ролью `Главный врач`.")
        return

    try:
        banned_entry = await guild.fetch_ban(discord.Object(id=user_id))
    except discord.NotFound:
        await ctx.send("❌ Пользователь с таким ID не найден в бан-листе.")
        return

    # ⚠️ ВАЖНО: получаем пользователя НАПРЯМУЮ
    try:
        user = await bot.fetch_user(user_id)
    except:
        await ctx.send("❌ Не удалось получить пользователя по ID.")
        return

    request_embed = discord.Embed(
        description=(
            f"⚠️ {chief_member.mention}\n\n"
            f"Попытка **разблокировать пользователя** `{user}`\n"
            f"🆔 **ID пользователя:** `{user_id}`\n\n"
            f"📄 **Причина разблокировки:** {reason}\n\n"
            "Данный запрос ожидает личного подтверждения от Главного Врача.\n\n"
            "🔔 **Подсказка Главному Врачу:**\n"
            "Нажмите ✅ — подтвердить разбан\n"
            "Нажмите ❌ — отклонить разбан"
        ),
        color=discord.Color.orange()
    )

    msg = await ctx.send(embed=request_embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user_react):
        return (
            reaction.message.id == msg.id
            and user_react == chief_member
            and str(reaction.emoji) in ("✅", "❌")
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=86400, check=check)
    except asyncio.TimeoutError:
        await msg.edit(
            embed=discord.Embed(
                description="⌛ Запрос на разбан был автоматически отменён.",
                color=discord.Color.red()
            )
        )
        return

    if str(reaction.emoji) == "❌":
        await msg.edit(
            embed=discord.Embed(
                description=(
                    "❌ **Разбан отклонён.**\n\n"
                    f"🆔 ID пользователя: `{user_id}`\n"
                    f"Решение принял: {chief_member.mention}"
                ),
                color=discord.Color.red()
            )
        )
        return

    now = datetime.now(MSK)

    await guild.unban(
        user,
        reason=f"{reason} | Инициатор: {ctx.author} | Подтвердил: Главный Врач"
    )

    # ================= ЛИЧНОЕ УВЕДОМЛЕНИЕ =================
    try:
        dm_embed = discord.Embed(
            description=(
                "🔴 **Вас разбанили в Discord сервере фракции "
                "`Министерство Здравоохранения`.**\n\n"
                f"🆔 **Ваш ID:** `{user_id}`\n"
                f"📄 **Причина:** {reason}\n\n"
                f"👤 **Инициатор разблокировки:** {ctx.author}\n"
                f"✅ **Подтвердил разблокировку:** Главный Врач\n\n"
                f"📅 **Дата разблокировки:** {now.strftime('%d.%m.%Y')}\n"
                f"⏰ **Время разблокировки:** {now.strftime('%H:%M')} (МСК)\n\n"
                "🟢 **Теперь Вы можете вновь пользоваться данным Discord-сервером.**\n"
                "🔗 **Приглашение:** https://discord.gg/Ny4Vs6vEjd"
            ),
            color=discord.Color.green()
        )
        await user.send(embed=dm_embed)
    except:
        pass  # если ЛС закрыты — Discord не даст отправить

    await msg.edit(
        embed=discord.Embed(
            description=(
                "✅ **Разбан подтверждён и выполнен.**\n\n"
                f"👤 Пользователь: {user}\n"
                f"🆔 ID пользователя: `{user_id}`\n"
                f"📄 Причина: {reason}\n\n"
                f"Инициатор: {ctx.author.mention}\n"
                f"Подтвердил: {chief_member.mention}"
            ),
            color=discord.Color.green()
        )
    )

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

# ================= НАСТРОЙКИ =================

MEDICAL_RANKS = [
    "Интерн",
    "Фельдшер",
    "Участковый врач",
    "Терапевт",
    "Проктолог",
    "Хирург",
    "Заведующий отделением",
    "Заместитель Главного Врача"
]

AUDIT_CHANNEL_NAME = "кадровый-аудит-повышений-и-понижений-сотрудников"

BLOCK_PROMOTE_ROLES = [
    "[-] Документы не утверждены",
    "Переаттестация",
    "Строгий выговор 2/2",
    "Строгий выговор 1/2",
    "Выговор 2/2",
    "Выговор 1/2",
    "Устное предупреждение"
]

# ================= ПОВЫШЕНИЕ =================

@bot.command(name="повысить")
@has_any_role()
async def promote(ctx, action: str, member: discord.Member):
    if action.lower() != "должность":
        return

    audit_channel = discord.utils.get(
        ctx.guild.text_channels,
        name=AUDIT_CHANNEL_NAME
    )

    # ---- ПРОВЕРКА НА БЛОКИРУЮЩИЕ РОЛИ ----
    blocked_roles = []
    for role_name in BLOCK_PROMOTE_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role in member.roles:
            blocked_roles.append(role)

    if blocked_roles:
        embed = discord.Embed(
            description=(
                "❌ **Повышение данного сотрудника - невозможно.**\n\n"
                "У сотрудника есть активные ограничения:\n"
                f"{' '.join(r.mention for r in blocked_roles)}\n\n"
                "Чтобы повысить данного сотрудника, ему необходимо снять активные наказания.\n\n"
                f"Повышение выполнил: {ctx.author.mention}"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # ---- ПОИСК ТЕКУЩЕЙ ДОЛЖНОСТИ ----
    current_role = None
    for role_name in MEDICAL_RANKS:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role in member.roles:
            current_role = role
            break

    if not current_role:
        await ctx.send("❌ У пользователя нет должности.")
        return

    index = MEDICAL_RANKS.index(current_role.name)
    if index >= len(MEDICAL_RANKS) - 1:
        await ctx.send("❌ Пользователь уже на максимальной должности.")
        return

    new_role = discord.utils.get(
        ctx.guild.roles,
        name=MEDICAL_RANKS[index + 1]
    )

    await member.remove_roles(current_role)
    await member.add_roles(new_role)

    # ---- ЛОГ В ТЕКУЩИЙ ЧАТ ----
    embed = discord.Embed(
        description=(
            "📝 **Лог: Повышение в должности**\n\n"
            f"👤 Сотрудник: {member.mention}\n"
            f"Аудит: Повышен с {current_role.mention} на {new_role.mention}\n\n"
            f"Повышал: {ctx.author.mention}"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # ---- ЛОГ В КАДРОВЫЙ АУДИТ ----
    if audit_channel:
        audit_embed = discord.Embed(
            description=(
                "📝 **Лог: Повышение в должности**\n\n"
                f"👤 Сотрудник: {member.display_name}\n"
                f"📈 Повышен с {current_role.name} на {new_role.name}\n\n"
                f"Повышал: {ctx.author.mention}"
            ),
            color=discord.Color.green()
        )
        await audit_channel.send(embed=audit_embed)

# ================= ПОНИЖЕНИЕ =================

@bot.command(name="понизить")
@has_any_role()
async def demote(ctx, action: str, member: discord.Member):
    if action.lower() != "должность":
        return

    audit_channel = discord.utils.get(
        ctx.guild.text_channels,
        name=AUDIT_CHANNEL_NAME
    )

    current_role = None
    for role_name in MEDICAL_RANKS:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role in member.roles:
            current_role = role
            break

    if not current_role:
        await ctx.send("❌ У пользователя нет должности.")
        return

    index = MEDICAL_RANKS.index(current_role.name)
    if index == 0:
        await ctx.send("❌ Пользователь уже на минимальной должности.")
        return

    new_role = discord.utils.get(
        ctx.guild.roles,
        name=MEDICAL_RANKS[index - 1]
    )

    await member.remove_roles(current_role)
    await member.add_roles(new_role)

    # ---- ЛОГ В ТЕКУЩИЙ ЧАТ ----
    embed = discord.Embed(
        description=(
            "📝 **Лог: Понижение должности**\n\n"
            f"👤 Сотрудник: {member.mention}\n"
            f"Аудит: Понижен с {current_role.mention} на {new_role.mention}\n\n"
            f"Понижал: {ctx.author.mention}"
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

    # ---- ЛОГ В КАДРОВЫЙ АУДИТ ----
    if audit_channel:
        audit_embed = discord.Embed(
            description=(
                "📝 **Лог: Понижение в должности**\n\n"
                f"👤 Сотрудник: {member.display_name}\n"
                f"📉 Понижен с {current_role.name} на {new_role.name}\n\n"
                f"Понижал: {ctx.author.mention}"
            ),
            color=discord.Color.orange()
        )
        await audit_channel.send(embed=audit_embed)


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

# ---------- !чистка ----------
@bot.command(name="чистка")
@has_any_role()
async def clear_chat(ctx, amount: int):
    # embed: начало очистки
    start_embed = discord.Embed(
        description=f"⏳ Ожидайте. Начал очистку **{amount}** строк в данном чате.",
        color=discord.Color.orange()
    )

    start_msg = await ctx.send(embed=start_embed)

    # задержка 5 секунд
    await asyncio.sleep(5)

    # удаляем сообщения (amount + сообщение команды)
    deleted = await ctx.channel.purge(limit=amount + 1)

    # удаляем сообщение ожидания
    try:
        await start_msg.delete()
    except:
        pass

    # embed: результат
    result_embed = discord.Embed(
        description=(
            f"✅ По запросу от {ctx.author.mention} "
            f"было очищено **{len(deleted) - 1}** строк из данного чата."
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=result_embed)

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
