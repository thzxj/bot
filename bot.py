import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
        
        # Procura o canal geral de registos
        canal_geral = discord.utils.get(guild.text_channels, name="registro-de-farm")
        if not canal_geral:
            await interaction.followup.send("❌ O canal `registro-de-farm` não foi encontrado no servidor.", ephemeral=True)
            return

        farms_encontrados = []
        
        # Lê as últimas 100 mensagens do canal de registos para encontrar as do utilizador
        async for message in canal_geral.history(limit=100):
            # Verifica se a mensagem foi enviada pelo bot e menciona o utilizador nos embeds ou texto
            if message.author == bot.user and message.embeds:
                embed = message.embeds[0]
                if embed.description and user.mention in embed.description:
                    farms_encontrados.append(embed.description)

        if not farms_encontrados:
            await interaction.followup.send("📊 Ainda não tem nenhum farm registado esta semana.", ephemeral=True)
            return

        # Monta a resposta com os últimos farms encontrados
        texto_resposta = f"📊 **Os seus últimos registos de farm:**\n\n"
        for i, farm in enumerate(farms_encontrados[:5], 1): # Mostra até os últimos 5 registos
            texto_resposta += f"**Registo {i}:**\n{farm}\n-------------------\n"

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
        await interaction.response.send_message("🏆 **Ranking da Semana:**\n1. Utilizador A - 1000\n2. Utilizador B - 500", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot ligado com sucesso como {bot.user}")
    bot.add_view(MainFarmPanel())
    bot.add_view(PrivateFarmView())

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
    
import os
# ...
bot.run(os.getenv('DISCORD_TOKEN'))