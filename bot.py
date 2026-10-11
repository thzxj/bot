import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import re
import unicodedata
from datetime import datetime, timedelta, timezone
 
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
 
bot = commands.Bot(command_prefix="!", intents=intents)
 
# Nome exato do cargo que a pessoa aceita recebe
CARGO_APROVADO = "MEMBROS"
 
# Cargo que todo mundo recebe ao entrar no servidor
CARGO_VISITANTE = "VISITANTE"
 
 
# ================== SETAGEM ==================
 
class SetagemModal(discord.ui.Modal, title="Pedido de Setagem"):
    nome_ingame = discord.ui.TextInput(
        label="Nome in game",
        placeholder="Ex: João Silva",
        required=True,
        max_length=50
    )
    passaporte = discord.ui.TextInput(
        label="Passaporte",
        placeholder="Ex: 12345",
        required=True,
        max_length=20
    )
    recrutador = discord.ui.TextInput(
        label="Quem te recrutou",
        placeholder="Nome de quem te recrutou",
        required=True,
        max_length=50
    )
    telefone = discord.ui.TextInput(
        label="Telefone in game",
        placeholder="Ex: 555-1234",
        required=True,
        max_length=20
    )
 
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Novo Pedido de Setagem",
            description=f"**Membro:** {interaction.user.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Nome in game", value=self.nome_ingame.value, inline=False)
        embed.add_field(name="Passaporte", value=self.passaporte.value, inline=False)
        embed.add_field(name="Recrutado por", value=self.recrutador.value, inline=False)
        embed.add_field(name="Telefone", value=self.telefone.value, inline=False)
        embed.set_footer(text=f"ID: {interaction.user.id}")
 
        canal_setagem = discord.utils.get(interaction.guild.text_channels, name="pedidos-de-setagem")
        if not canal_setagem:
            await interaction.response.send_message("❌ O canal `pedidos-de-setagem` não foi encontrado no servidor.", ephemeral=True)
            return
 
        await canal_setagem.send(embed=embed, view=AprovarSetagemView())
        await interaction.response.send_message("✅ O seu pedido de setagem foi enviado com sucesso!", ephemeral=True)
 
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ Ocorreu um erro ao enviar o pedido.", ephemeral=True)
 
 
class AprovarSetagemView(View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅", custom_id="btn_aceitar_setagem")
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Você não tem permissão pra isso.", ephemeral=True)
            return
 
        await interaction.response.defer(ephemeral=True)
 
        embed = interaction.message.embeds[0]
        campos = {f.name: f.value for f in embed.fields}
        user_id = int(embed.footer.text.replace("ID: ", ""))
 
        membro = interaction.guild.get_member(user_id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_APROVADO)
 
        if not membro:
            await interaction.followup.send("❌ Esse usuário não está mais no servidor.", ephemeral=True)
            return
        if not cargo:
            await interaction.followup.send(f"❌ O cargo `{CARGO_APROVADO}` não foi encontrado.", ephemeral=True)
            return
 
        novo_nick = f"{campos['Nome in game']} | {campos['Passaporte']}"[:32]
 
        try:
            await membro.add_roles(cargo)
            cargo_visitante = discord.utils.get(interaction.guild.roles, name=CARGO_VISITANTE)
            if cargo_visitante and cargo_visitante in membro.roles:
                await membro.remove_roles(cargo_visitante)
            await membro.edit(nick=novo_nick)
        except discord.Forbidden:
            await interaction.followup.send("❌ O bot não tem permissão pra dar o cargo ou trocar o apelido dessa pessoa.", ephemeral=True)
            return
 
        embed.title = "✅ Setagem Aceita"
        embed.color = discord.Color.green()
        embed.add_field(name="Aceito por", value=interaction.user.mention, inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.followup.send(f"✅ {membro.mention} foi setado como **{novo_nick}**.", ephemeral=True)
 
    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="btn_recusar_setagem")
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Você não tem permissão pra isso.", ephemeral=True)
            return
 
        embed = interaction.message.embeds[0]
        embed.title = "❌ Setagem Recusada"
        embed.color = discord.Color.red()
        embed.add_field(name="Recusado por", value=interaction.user.mention, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
 
 
class SetagemPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Pedir Setagem", style=discord.ButtonStyle.success, emoji="📋", custom_id="btn_pedir_setagem")
    async def pedir_setagem(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetagemModal())
 
 
# ================== FARM ==================
 
def inicio_da_semana():
    """Segunda-feira 00:00 no horário de Brasília (UTC-3). O farm conta a partir daqui."""
    br = timezone(timedelta(hours=-3))
    agora = datetime.now(br)
    segunda = (agora - timedelta(days=agora.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return segunda
 
 
class PrivateFarmView(View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Registar Farm", style=discord.ButtonStyle.green, emoji="📋", custom_id="btn_registrar_farm")
    async def registrar_farm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("📝 Basta digitar diretamente no chat os itens e quantidades (Ex: `pólvora 500, espoleta 100`). O bot irá registar automaticamente!", ephemeral=True)
 
    @discord.ui.button(label="Meus Farms", style=discord.ButtonStyle.primary, emoji="📊", custom_id="btn_meus_farms")
    async def meus_farms(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
 
        guild = interaction.guild
        user = interaction.user
 
        canal_geral = discord.utils.get(guild.text_channels, name="registro-de-farm")
        if not canal_geral:
            await interaction.followup.send("❌ O canal `registro-de-farm` não foi encontrado no servidor.", ephemeral=True)
            return
 
        def normalizar(texto):
            # tira acento e deixa minúsculo: "Pólvora" e "polvora" viram o mesmo item
            sem_acento = unicodedata.normalize("NFD", texto)
            sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
            return sem_acento.lower().strip()
 
        totais = {}  # nome normalizado -> [nome pra exibir, quantidade]
 
        async for message in canal_geral.history(limit=500, after=inicio_da_semana()):
            if message.author == bot.user and message.embeds:
                embed = message.embeds[0]
                if not embed.description or user.mention not in embed.description:
                    continue
 
                trechos = re.findall(r"`([^`]+)`", embed.description)
                if not trechos:
                    continue
 
                for parte in trechos[-1].split(","):
                    parte = parte.strip()
                    # aceita "polvora 50" e também "50 polvora"
                    m = re.match(r"^(.+?)\s+(\d+)$", parte) or re.match(r"^(\d+)\s+(.+)$", parte)
                    if not m:
                        continue
                    if m.group(1).isdigit():
                        qtd, nome = int(m.group(1)), m.group(2)
                    else:
                        nome, qtd = m.group(1), int(m.group(2))
 
                    chave = normalizar(nome)
                    if chave not in totais:
                        totais[chave] = [nome.strip().capitalize(), 0]
                    totais[chave][1] += qtd
 
        if not totais:
            await interaction.followup.send("📊 Ainda não tem nenhum farm registado esta semana.", ephemeral=True)
            return
 
        linhas = [f"• **{nome}:** {qtd}" for nome, qtd in sorted(totais.values(), key=lambda x: -x[1])]
        texto_resposta = "📊 **O seu farm da semana:**\n\n" + "\n".join(linhas)
 
        await interaction.followup.send(texto_resposta, ephemeral=True)
 
    @discord.ui.button(label="Notificar", style=discord.ButtonStyle.blurple, emoji="🔔", custom_id="btn_notificar")
    async def notificar(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔔 A moderação foi notificada no seu canal.", ephemeral=True)
 
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_fechar_canal")
    async def fechar_canal(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 Este canal será encerrado em instantes...", ephemeral=True)
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass
 
class MainFarmPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Iniciar Farm", style=discord.ButtonStyle.primary, emoji="📝", custom_id="btn_iniciar_farm")
    async def iniciar_farm(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        channel_name = f"📁・{user.name.lower()}"
 
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"❌ Já possui um canal aberto: {existing_channel.mention}", ephemeral=True)
            return
 
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
 
        category = interaction.channel.category
        new_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
 
        embed_interno = discord.Embed(
            title="📁 Canal de Farm",
            description="**Digite no chat o que você farmou.**\n\n"
                        "Escreva o nome do item e a quantidade separado por vírgula.\n"
                        "Exemplo: `pólvora 500, espoleta 100`\n\n"
                        "🔫 **MUNIÇÃO:**\n"
                        "• Pólvora\n• Projétil de Rifle\n• Espoleta\n\n"
                        "⚔️ **ARMAS:**\n"
                        "• Gatilho de Arma\n• Corpo de Arma\n• Alça de SMG\n"
                        "• Alça de Rifle\n• Alça de Pistola\n"
                        "• Carregador de Rifle\n• Carregador de Pistola\n"
                        "• Carregador de SMG\n\n"
                        "Você tem **5 minutos** para digitar.",
            color=discord.Color.dark_green()
        )
        embed_interno.set_footer(text="Amsterdan Farm Bot")
 
        await new_channel.send(content=f"{user.mention}", embed=embed_interno, view=PrivateFarmView())
        await interaction.response.send_message(f"✅ O seu canal foi criado com sucesso: {new_channel.mention}", ephemeral=True)
 
    @discord.ui.button(label="Ranking Semanal", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="btn_ranking_farm")
    async def ranking_semanal(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
 
        canal_geral = discord.utils.get(interaction.guild.text_channels, name="registro-de-farm")
        if not canal_geral:
            await interaction.followup.send("❌ O canal `registro-de-farm` não foi encontrado no servidor.", ephemeral=True)
            return
 
        totais = {}  # id do membro -> total de itens farmados na semana
 
        async for message in canal_geral.history(limit=1000, after=inicio_da_semana()):
            if message.author != bot.user or not message.embeds:
                continue
 
            desc = message.embeds[0].description
            if not desc:
                continue
 
            membro = re.search(r"<@!?(\d+)>", desc)
            trechos = re.findall(r"`([^`]+)`", desc)
            if not membro or not trechos:
                continue
 
            soma = 0
            for parte in trechos[-1].split(","):
                m = re.match(r"^(.+?)\s+(\d+)$", parte.strip()) or re.match(r"^(\d+)\s+(.+)$", parte.strip())
                if not m:
                    continue
                soma += int(m.group(2)) if m.group(1).strip() and not m.group(1).isdigit() else int(m.group(1))
 
            uid = int(membro.group(1))
            totais[uid] = totais.get(uid, 0) + soma
 
        if not totais:
            await interaction.followup.send("🏆 Ninguém registou farm esta semana ainda.", ephemeral=True)
            return
 
        medalhas = ["🥇", "🥈", "🥉"]
        ranking = sorted(totais.items(), key=lambda x: -x[1])[:10]
        linhas = []
        for pos, (uid, total) in enumerate(ranking):
            prefixo = medalhas[pos] if pos < 3 else f"**{pos + 1}.**"
            linhas.append(f"{prefixo} <@{uid}> — **{total}** itens")
 
        await interaction.followup.send("🏆 **Ranking da Semana:**\n\n" + "\n".join(linhas), ephemeral=True)
 
@bot.event
async def on_ready():
    print(f"Bot ligado com sucesso como {bot.user}")
    bot.add_view(MainFarmPanel())
    bot.add_view(PrivateFarmView())
    bot.add_view(SetagemPanel())
    bot.add_view(AprovarSetagemView())
 
@bot.event
async def on_member_join(member):
    cargo = discord.utils.get(member.guild.roles, name=CARGO_VISITANTE)
    if cargo:
        try:
            await member.add_roles(cargo)
        except discord.Forbidden:
            print(f"Sem permissão pra dar o cargo {CARGO_VISITANTE} a {member}")
 
@bot.event
async def on_message(message):
    if message.author.bot:
        return
 
    if message.channel.name.startswith("📁・"):
        conteudo = message.content
        
        if "," in conteudo or any(char.isdigit() for char in conteudo):
            embed_privado = discord.Embed(
                title="✅ Farm Registado com Sucesso!",
                description=f"**Itens enviados:**\n`{conteudo}`",
                color=discord.Color.green()
            )
            embed_privado.set_footer(text="Amsterdan Farm Bot")
            await message.channel.send(embed=embed_privado)
 
            canal_geral = discord.utils.get(message.guild.text_channels, name="registro-de-farm")
            if canal_geral:
                embed_geral = discord.Embed(
                    title="📊 Novo Registo de Farm",
                    description=f"**Membro:** {message.author.mention}\n"
                                f"**Canal:** {message.channel.mention}\n"
                                f"**Itens Farmados:**\n`{conteudo}`",
                    color=discord.Color.blue()
                )
                embed_geral.set_footer(text="Amsterdan Farm Bot - Registos")
                await canal_geral.send(embed=embed_geral)
 
    await bot.process_commands(message)
 
@bot.command()
@commands.has_permissions(administrator=True)
async def painelfarm(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="🌾 Painel de Farm — Amsterdan",
        description="**Registe os seus farms semanais aqui!**\n\n"
                    "📝 Clique em **Iniciar Farm** para abrir o seu canal privado.\n"
                    "🏆 Clique em **Ranking** para ver quem farmou mais esta semana.\n\n"
                    "O ranking reseta toda **segunda-feira**.",
        color=discord.Color.green()
    )
    embed.set_footer(text="Amsterdan Farm Bot")
    await ctx.send(embed=embed, view=MainFarmPanel())
 
@bot.command()
@commands.has_permissions(administrator=True)
async def painelsetagem(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="📋 Setagem — Amsterdã",
        description="Clique no botão abaixo e preencha o formulário pra pedir a sua setagem.\n\n"
                    "Depois é só aguardar a análise da staff.",
        color=discord.Color.orange()
    )
    embed.set_footer(text="Amsterdan Farm Bot")
    await ctx.send(embed=embed, view=SetagemPanel())
    
import os
# ...
bot.run(os.getenv('DISCORD_TOKEN'))