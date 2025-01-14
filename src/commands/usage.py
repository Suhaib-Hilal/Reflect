from datetime import (
    datetime,
)

from discord import (
    Embed,
    InteractionResponse,
    SelectMenu,
    SelectOption,
    ApplicationContext
)
from discord.ui import (
    View,
    select
)
from discord.ext.commands import (
    Cog,
    slash_command
)

from ..bot import ICodeBot


class Help(Cog):
    """
    Help command
    """

    def __init__(self, bot: ICodeBot) -> None:
        """
        Initialize

        Args:
            bot (discord.Bot): iCODE-BOT
        """
        super().__init__()
        self._bot = bot

    @slash_command(name="help")
    async def _help(self, ctx: ApplicationContext) -> None:
        """
        Show usage help

        Args:
            ctx (ApplicationContext)
        """

        # Create embed for showing help
        # Set author, footer and thumbnail for the embed
        embed = Embed(
            description=f"{self._bot.description}\n"
                        "Choose a command group from the "
                        "below select menu to get help",
            color=ctx.author.color,
            timestamp=datetime.now()
        ).set_author(
            name="iCODE Usage Help",
            icon_url=self._bot.user.display_avatar
        ).set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.display_avatar
        ).set_thumbnail(
            url=self._bot.user.display_avatar
        )

        # Send embed with a view obj
        await ctx.respond(
            embed=embed,
            view=UsageView(self._bot, ctx)
        )


class UsageView(View):

    def __init__(self, bot: ICodeBot, ctx: ApplicationContext):
        """
        Initialize

        Args:
            bot (ICodeBot)
            ctx (ApplicationContext)
        """
        super().__init__(timeout=360)

        # Set attributes for View Obj
        self._bot = bot
        self.ctx = ctx

    # Create select menu for command groups
    @select(
        placeholder="Select command group",
        min_values=1,
        max_values=1,
        options=[
            SelectOption(
                label="General Commands",
                value="GeneralCommands"
            ),
            SelectOption(
                label="Moderation Commands",
                value="ModerationCommands"
            ),
            SelectOption(
                label="Miscellaneous Commands",
                value="MiscellaneousCommands"
            )
        ]
    )
    async def select_callback(
            self,
            select: SelectMenu,
            interaction: InteractionResponse
    ) -> None:
        """
        Cog selection menu

        Args:
            select (SelectMenu)
            interaction (InteractionResponse)
        """

        # Get command group
        cog = self._bot.get_cog(select.values[0])

        # Get command group description
        desc = cog.description

        # Create embed for help on this group
        embed = Embed(
            description=desc,
            color=self.ctx.author.color,
        ).set_author(
            name="iCODE Usage Help",
            icon_url=self._bot.user.display_avatar
        ).set_footer(
            text="<Required> - [Optional]",
            icon_url=self.ctx.author.display_avatar
        ).set_thumbnail(
            url=self._bot.user.display_avatar
        )

        # Generate command syntax
        emoji = self._bot.emoji_group.get_emoji("reply")
        for cmd in cog.get_commands():
            # Create a string of options
            options = " ".join(
                [f"<{option.name}>" if option.required else f"[{option.name}]"
                 for option in cmd.options]
            )

            # Add field to the embed
            embed.add_field(
                name=f"__/{cmd}__",
                value=f"{emoji} {cmd.description}\n"
                f"{emoji} Usage: `/{cmd} {options}`",
                inline=False
            )

        # Respond to the interaction
        await interaction.response.edit_message(
            embed=embed
        )
