import os
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

# ── CONFIG ──────────────────────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN", "MTU0MzczNzgyODkzOTQwNzQ2MA.GqNmkT.aBdPbJIPR0q5GNO_ItmyxvSvgIBre4wlEF3UQ8")
GUILD_ID = int(os.getenv("1543692983625326602", "0"))              # ID-ul serverului
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "1543693563597037769"))             # rolul staff (poate folosi comenzile)
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "1543698909019373718"))   # categoria unde se creeaza tichetele

EMBED_COLOR = 0xE02B2B
POINTS_FILE = "puncte.json"

# ── STORAGE PUNCTE ──────────────────────────────────────────────────────
def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_points(data):
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── BOT SETUP ───────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_staff(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
    return staff_role in interaction.user.roles if staff_role else False


# ── VIEWS (butoane) ─────────────────────────────────────────────────────
class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="muiala", style=discord.ButtonStyle.danger, custom_id="open_ticket_button")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        author = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{author.name.lower()}")
        if existing:
            await interaction.response.send_message(
                f"Ai deja un tichet deschis: {existing.mention}", ephemeral=True
            )
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{author.name.lower()}",
            category=category,
            overwrites=overwrites,
            reason=f"Tichet deschis de {author}",
        )

        embed = discord.Embed(
            title="bun venit în iad",
            description=(
                "@ daca ai tacut mai mult de 2 minute ai LOSE instant\n\n"
                "@ daca ai auto/macro LOSE instant\n\n"
                "@ daca refuzi parta/task etc LOSE\n\n"
                "@ daca dati mai mult de 4 pinguri ownerului timeout 1 minut."
            ),
            color=EMBED_COLOR,
        )
        embed.set_footer(text="Powered by tickets.bot")
        await channel.send(content=author.mention, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Tichetul tău a fost creat: {channel.mention}", ephemeral=True)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Închide Ticket", style=discord.ButtonStyle.secondary, custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tichetul se închide în 5 secunde...", ephemeral=False)
        channel = interaction.channel
        await asyncio.sleep(5)
        await channel.delete(reason=f"Tichet închis de {interaction.user}")


# ── SLASH COMMANDS ──────────────────────────────────────────────────────
@bot.tree.command(name="setup", description="Trimite panoul de tickete în acest canal")
async def setup_cmd(interaction: discord.Interaction):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return

    embed = discord.Embed(
        title="/bronx",
        description="pt a intra in arena apasa pe butonul de mai jos",
        color=EMBED_COLOR,
    )
    embed.set_footer(text="Powered by tickets.bot")
    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.response.send_message("Panou trimis.", ephemeral=True)


@bot.tree.command(name="rename", description="Redenumeste canalul curent (tichet)")
@app_commands.describe(nume="Noul nume al canalului")
async def rename_cmd(interaction: discord.Interaction, nume: str):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.channel.edit(name=nume)
    await interaction.response.send_message(f"Canalul a fost redenumit în `{nume}`.", ephemeral=True)


@bot.tree.command(name="add", description="Adauga o persoana in tichetul curent")
@app_commands.describe(user="Persoana de adaugat")
async def add_cmd(interaction: discord.Interaction, user: discord.Member):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
    await interaction.response.send_message(f"{user.mention} a fost adăugat în tichet.")


PUNCTE_CHOICES = [
    app_commands.Choice(name="-100", value=-100),
    app_commands.Choice(name="-50", value=-50),
    app_commands.Choice(name="-40", value=-40),
    app_commands.Choice(name="-30", value=-30),
    app_commands.Choice(name="-20", value=-20),
    app_commands.Choice(name="-15", value=-15),
    app_commands.Choice(name="-10", value=-10),
    app_commands.Choice(name="+10", value=10),
    app_commands.Choice(name="+20", value=20),
    app_commands.Choice(name="+30", value=30),
    app_commands.Choice(name="+40", value=40),
    app_commands.Choice(name="+50", value=50),
    app_commands.Choice(name="+100", value=100),
]


@bot.tree.command(name="puncte", description="Adauga sau scade puncte unui user")
@app_commands.describe(user="Userul", valoare="Cate puncte adaugi/scazi")
@app_commands.choices(valoare=PUNCTE_CHOICES)
async def puncte_cmd(interaction: discord.Interaction, user: discord.Member, valoare: app_commands.Choice[int]):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return

    data = load_points()
    uid = str(user.id)
    data[uid] = data.get(uid, 0) + valoare.value
    save_points(data)

    semn = "+" if valoare.value > 0 else ""
    await interaction.response.send_message(
        f"{user.mention} a primit {semn}{valoare.value} puncte. Total: **{data[uid]}**"
    )


@bot.tree.command(name="listapuncte", description="Arata topul cu cele mai multe puncte")
async def listapuncte_cmd(interaction: discord.Interaction):
    data = load_points()
    if not data:
        await interaction.response.send_message("Nu există puncte înregistrate încă.", ephemeral=True)
        return

    ranked = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, pts) in enumerate(ranked, start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        prefix = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{prefix} **{name}** — {pts} puncte")

    embed = discord.Embed(
        title="🏆 Top Puncte",
        description="\n".join(lines),
        color=EMBED_COLOR,
    )
    await interaction.response.send_message(embed=embed)


# ── RESET PUNCTE ────────────────────────────────────────────────────────
@bot.tree.command(name="status", description="Arata cate puncte are un user (sau tu, daca nu specifici)")
@app_commands.describe(user="Userul (optional)")
async def status_cmd(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    data = load_points()
    pts = data.get(str(target.id), 0)
    embed = discord.Embed(
        title="📊 Status Puncte",
        description=f"{target.mention} are **{pts}** puncte.",
        color=EMBED_COLOR,
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="resetpuncte", description="Reseteaza punctele unui user la 0")
@app_commands.describe(user="Userul")
async def resetpuncte_cmd(interaction: discord.Interaction, user: discord.Member):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    data = load_points()
    data[str(user.id)] = 0
    save_points(data)
    await interaction.response.send_message(f"Punctele lui {user.mention} au fost resetate la 0.")


@bot.tree.command(name="resetpuncteall", description="Reseteaza punctele tuturor")
async def resetpuncteall_cmd(interaction: discord.Interaction):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    save_points({})
    await interaction.response.send_message("Punctele tuturor au fost resetate.")


# ── ROLE ────────────────────────────────────────────────────────────────
role_group = app_commands.Group(name="role", description="Gestionare roluri")


@role_group.command(name="add", description="Adauga un rol unui user")
@app_commands.describe(user="Userul", role="Rolul de adaugat")
async def role_add(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await user.add_roles(role, reason=f"Adaugat de {interaction.user}")
    await interaction.response.send_message(f"Rolul {role.mention} a fost adăugat lui {user.mention}.")


@role_group.command(name="remove", description="Elimina un rol de la un user")
@app_commands.describe(user="Userul", role="Rolul de eliminat")
async def role_remove(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await user.remove_roles(role, reason=f"Eliminat de {interaction.user}")
    await interaction.response.send_message(f"Rolul {role.mention} a fost eliminat de la {user.mention}.")


bot.tree.add_command(role_group)


# ── BAN ─────────────────────────────────────────────────────────────────
ban_group = app_commands.Group(name="ban", description="Gestionare ban-uri")


@ban_group.command(name="add", description="Baneaza un user")
@app_commands.describe(user="Userul", motiv="Motivul (optional)")
async def ban_add(interaction: discord.Interaction, user: discord.Member, motiv: str = "Fara motiv specificat"):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.guild.ban(user, reason=motiv)
    await interaction.response.send_message(f"{user.mention} a fost banat. Motiv: {motiv}")


@ban_group.command(name="remove", description="Deblocheaza un user banat (dupa ID)")
@app_commands.describe(user_id="ID-ul userului de deblocat")
async def ban_remove(interaction: discord.Interaction, user_id: str):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    try:
        user_obj = discord.Object(id=int(user_id))
        await interaction.guild.unban(user_obj)
        await interaction.response.send_message(f"Userul cu ID `{user_id}` a fost deblocat.")
    except (ValueError, discord.NotFound):
        await interaction.response.send_message("ID invalid sau userul nu e banat.", ephemeral=True)


bot.tree.add_command(ban_group)


# ── TIMEOUT ─────────────────────────────────────────────────────────────
timeout_group = app_commands.Group(name="timeout", description="Gestionare timeout")


@timeout_group.command(name="add", description="Pune un user in timeout")
@app_commands.describe(user="Userul", minute="Durata in minute", motiv="Motivul (optional)")
async def timeout_add(interaction: discord.Interaction, user: discord.Member, minute: int, motiv: str = "Fara motiv specificat"):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    import datetime
    duration = datetime.timedelta(minutes=minute)
    await user.timeout(duration, reason=motiv)
    await interaction.response.send_message(f"{user.mention} a primit timeout {minute} minute. Motiv: {motiv}")


@timeout_group.command(name="remove", description="Elimina timeout-ul unui user")
@app_commands.describe(user="Userul")
async def timeout_remove(interaction: discord.Interaction, user: discord.Member):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await user.timeout(None, reason=f"Eliminat de {interaction.user}")
    await interaction.response.send_message(f"Timeout-ul lui {user.mention} a fost eliminat.")


bot.tree.add_command(timeout_group)


# ── KICK (din tichet) ───────────────────────────────────────────────────
@bot.tree.command(name="kick", description="Scoate un user din tichetul curent")
@app_commands.describe(user="Userul de scos din tichet")
async def kick_cmd(interaction: discord.Interaction, user: discord.Member):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.channel.set_permissions(user, overwrite=None)
    await interaction.response.send_message(f"{user.mention} a fost scos din tichet.")


# ── TICKET PUBLIC / PRIVAT ──────────────────────────────────────────────
ticket_group = app_commands.Group(name="ticket", description="Gestionare tichet curent")


@ticket_group.command(name="public", description="Face tichetul curent vizibil tuturor")
async def ticket_public(interaction: discord.Interaction):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True, send_messages=False)
    await interaction.response.send_message("Tichetul a fost făcut public (vizibil tuturor).")


@ticket_group.command(name="privat", description="Face tichetul curent privat (doar staff + opener)")
async def ticket_privat(interaction: discord.Interaction):
    if not is_staff(interaction):
        await interaction.response.send_message("Nu ai voie să folosești comanda asta.", ephemeral=True)
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await interaction.response.send_message("Tichetul a fost făcut privat.")


bot.tree.add_command(ticket_group)


# ── CLOSE (sterge tichetul) ─────────────────────────────────────────────
@bot.tree.command(name="close", description="Sterge tichetul curent")
async def close_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("Tichetul se închide în 5 secunde...")
    channel = interaction.channel
    await asyncio.sleep(5)
    await channel.delete(reason=f"Tichet închis de {interaction.user}")


# ── READY / SYNC ────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"Conectat ca {bot.user}")
    bot.add_view(OpenTicketView())
    bot.add_view(CloseTicketView())

    if GUILD_ID:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
    else:
        synced = await bot.tree.sync()

    print(f"Sincronizate {len(synced)} comenzi slash.")


bot.run(TOKEN)
