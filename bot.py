import os
import discord
from discord.ext import commands

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------------------------------------
# PAINEL DE CONTAGEM DENTRO DO CANAL DE FARM
# -------------------------------------------------------------
class ContagemFarmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.contador = 0

    @discord.ui.button(label="➕ Registar Item", style=discord.ButtonStyle.green, custom_id="btn_registar_farm")
    async def registar_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.contador += 1
        await interaction.response.send_message(
            f"✅ Farm registado com sucesso! Total registado nesta sessão: **{self.contador}**", 
            ephemeral=True
        )

    @discord.ui.button(label="📊 Ver Total", style=discord.ButtonStyle.blurple, custom_id="btn_ver_total")
    async def ver_total(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"📊 Atualmente tens **{self.contador}** itens registados neste canal.", 
            ephemeral=True
        )

# -------------------------------------------------------------
# 1. SISTEMA DE FARM (Cria na categoria certa + Painel de Contagem)
# -------------------------------------------------------------
class FarmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Iniciar Farm", 
        style=discord.ButtonStyle.blurple, 
        custom_id="btn_iniciar_farm"
    )
    async def iniciar_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        # ⚠️ SUBSTITUA PELO ID DA CATEGORIA ONDE OS CANAIS DE FARM DEVEM SER CRIADOS
        ID_CATEGORIA_FARM = 1543768794600706129  
        categoria = guild.get_channel(ID_CATEGORIA_FARM)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel_name = f"farm-{member.name}".lower()
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)

        if existing_channel:
            await interaction.response.send_message(
                f"❌ Já tens um canal de farm aberto: {existing_channel.mention}", 
                ephemeral=True
            )
            return

        # Cria o canal dentro da categoria especificada
        novo_canal = await guild.create_text_channel(
            name=channel_name, 
            category=categoria if isinstance(categoria, discord.CategoryChannel) else None,
            overwrites=overwrites
        )
        
        embed_painel = discord.Embed(
            title="🌾 Painel de Contagem de Farm",
            description=f"Olá {member.mention}! Usa os botões abaixo para gerizar e contabilizar o teu farm neste canal.",
            color=discord.Color.green()
        )

        await novo_canal.send(content=member.mention, embed=embed_painel, view=ContagemFarmView())
        
        await interaction.response.send_message(
            f"✅ O teu canal privado foi criado com sucesso: {novo_canal.mention}!", 
            ephemeral=True
        )

# -------------------------------------------------------------
# 2. SISTEMA DE SETAGEM (Modal / Formulário)
# -------------------------------------------------------------
class SetagemModal(discord.ui.Modal, title='Formulário de Setagem'):
    nome = discord.ui.TextInput(
        label='Seu Nome em Game',
        placeholder='Ex: João Silva',
        required=True
    )
    passaporte = discord.ui.TextInput(
        label='Seu Passaporte / ID',
        placeholder='Ex: 1234',
        required=True,
        max_length=10
    )
    recrutador = discord.ui.TextInput(
        label='Quem te recrutou?',
        placeholder='Ex: Carlos / ID 5678',
        required=True
    )
    telefone = discord.ui.TextInput(
        label='Telefone In-Game',
        placeholder='Ex: 555-0192',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # ⚠️ SUBSTITUA PELO ID DO CANAL ONDE A STAFF VAI RECEBER OS PEDIDOS
        ID_CANAL_LOGS = 1558854475848880198  

        canal_logs = interaction.guild.get_channel(ID_CANAL_LOGS)

        embed = discord.Embed(
            title="📋 Novo Pedido de Setagem",
            color=discord.Color.blue()
        )
        embed.add_field(name="Usuário Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Nome no Game", value=str(self.nome.value), inline=True)
        embed.add_field(name="Passaporte", value=str(self.passaporte.value), inline=True)
        embed.add_field(name="Recrutador", value=str(self.recrutador.value), inline=False)
        embed.add_field(name="Telefone", value=str(self.telefone.value), inline=False)

        if canal_logs:
            await canal_logs.send(embed=embed)

        await interaction.response.send_message(
            "✅ Seu formulário de setagem foi enviado com sucesso!", 
            ephemeral=True
        )

class SetagemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="PEDIR SETAGEM", 
        style=discord.ButtonStyle.green, 
        custom_id="btn_pedir_setagem"
    )
    async def pedir_setagem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetagemModal())

# -------------------------------------------------------------
# EVENTO ON_READY (Regista as Views)
# -------------------------------------------------------------
@bot.event
async def on_ready():
    bot.add_view(FarmView())
    bot.add_view(ContagemFarmView())
    bot.add_view(SetagemView())
    print(f'🤖 Bot {bot.user} está online e pronto!')

# -------------------------------------------------------------
# COMANDOS PARA ENVIAR OS PAINÉIS
# -------------------------------------------------------------
@bot.command()
async def enviar_farm(ctx):
    embed = discord.Embed(
        title="🌾 Sistema de Farm",
        description="Clica no botão abaixo para abrir o teu canal privado de farm.",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=FarmView())

@bot.command()
async def enviar_setagem(ctx):
    embed = discord.Embed(
        title="📋 Registro de Setagem",
        description="Clique no botão abaixo para preencher suas informações e solicitar a sua setagem.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=SetagemView())

# -------------------------------------------------------------
# INICIALIZAÇÃO DO BOT
# -------------------------------------------------------------
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ ERRO: A variável de ambiente DISCORD_TOKEN não foi encontrada.")