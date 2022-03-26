import logging
import asyncio
from datetime import datetime
from random import choice

from discord import (
    ApplicationContext,
    Bot,
    Embed,
    Emoji,
    Game,
    Member,
    Message,
    Role,
    Status,
    TextChannel,
    Webhook,
)

from .utils.color import Colors
from .utils.emoji import EmojiGroup
from .utils.bump_timer import BumpTimer
from .utils.constants import (
    GENERAL_CHAT_CHANNEL_ID,
    WELCOME_MESSAGES,
    FAREWELL_MESSAGES,
    CONSOLE_CHANNEL_ID,
    TERMINAL_CHANNEL_ID,
    SELF_ROLES_CHANNEL_ID,
    MAINTENANCE_CHANNEL_ID,
    INTRODUCTION_CHANNEL_ID,
    SERVER_RULES_CHANNEL_ID,
    BUMPER_ROLE_ID,
    DISBOARD_ID,
)


class ICodeBot(Bot):
    """
    The BOT made for 'iCODE' Discord server.
    """

    def __init__(self, description=None, maintenance=False, *args, **options):
        """
        Instantiate iCODE Bot

        Args:
            description (str, optional): Bot description. Defaults to None.
            maintenance (bool, optional): Whether the bot is under maintenance. Defaults to False.
        """

        super().__init__(description, *args, **options)
        self.MAINTENANCE_MODE = maintenance

    async def on_ready(self) -> None:
        """
        Called when the bot has finished logging in and setting things up
        """

        logging.info(msg=f"Logged in as {self.user}")

        # Create EmojiGroup instance
        logging.info(msg="Initializing EmojiGroup")
        self.emoji_group = EmojiGroup(self)

        # Create BumpTimer instance
        logging.info(msg="Initializing BumpTimer")
        self.bump_timer = BumpTimer()

        # If the bot is running in maintenance mode,
        if self.MAINTENANCE_MODE:
            # set MAINTENANCE_CHANNEL attribute to maintenance channel
            self.MAINTENANCE_CHANNEL = self.get_channel(MAINTENANCE_CHANNEL_ID)

            # set presence (status & activity)
            await self.change_presence(
                status=Status.do_not_disturb,
                activity=Game(name="| Under Maintenance")
            )

        # Otherwise
        else:
            # start bump timer
            previous_bump_time = self.bump_timer.get_bump_time()
            delta = (datetime.now() - previous_bump_time).total_seconds()
            delay = 0 if delta >= 7200 else (7200 - delta)

            self.dispatch("bump_done", int(delay))

            # set presence (activity)
            await self.change_presence(activity=Game(name="/emojis | .py"))

    async def on_bump_done(self, delay: int) -> None:
        """
        Called when a user bumps the server

        Args:
            channel (TextChannel): The channel to which bump reminder 
                                   will be sent
        """

        # Sleep for `delay` number of seconds
        self.bump_timer.running = True
        await asyncio.sleep(delay=delay)
        self.bump_timer.running = False

        # Set up receiver channel
        channel: TextChannel = self.get_channel(TERMINAL_CHANNEL_ID)

        # Get bumper role
        bumper: Role = channel.guild.get_role(BUMPER_ROLE_ID)

        # Get `reminder` emoji
        reminder: Emoji = self.emoji_group.get_emoji("reminder")

        # Send embed to the receiver channel
        await channel.send(
            content=f"{bumper.mention}",
            embed=Embed(
                title=f"Bump Reminder {reminder}",
                description="Help grow this server. Run `/bump`",
                color=Colors.GOLD
            )
        )

    async def on_maintenance(self, ctx: ApplicationContext) -> None:
        """
        Called when a member runs a command in maintenance mode

        Args:
            ctx (ApplicationContext)
        """

        # Get `warning` emoji
        emoji: Emoji = self.emoji_group.get_emoji("warning")

        # Send embed to maintenance channel
        await ctx.respond(
            content=ctx.author.mention,
            embed=Embed(
                title=f"Maintenance Break {emoji}",
                description="iCODE is under maintenance. Commands will work\n"
                            f"only in {self.MAINTENANCE_CHANNEL} channel.",
                color=Colors.GOLD
            ),
            delete_after=5
        )

    async def on_member_join(self, member: Member) -> None:
        """
        Called when a new member joins

        Args:
            member (Member): New member
        """

        # Set up required channels
        console: TextChannel = self.get_channel(CONSOLE_CHANNEL_ID)
        g_chat_channel: TextChannel = self.get_channel(GENERAL_CHAT_CHANNEL_ID)
        intro_channel: TextChannel = self.get_channel(INTRODUCTION_CHANNEL_ID)
        rules_channel: TextChannel = self.get_channel(SERVER_RULES_CHANNEL_ID)
        roles_channel: TextChannel = self.get_channel(SELF_ROLES_CHANNEL_ID)

        # Send embed with random welcome msg to receiver channel
        await console.send(
            embed=Embed(
                description=choice(
                    WELCOME_MESSAGES
                ).format(
                    member.display_name
                ),
                color=Colors.GREEN
            )
        )

        # Send embed to general-chat channel
        await g_chat_channel.send(
            content=member.mention,
            embed=Embed(
                title=f"Welcome to the server {member.display_name}!",
                description="Glad to have you here. "
                            "Have a look around the server.\n\n"
                            f"Introduce yourself in {intro_channel.mention}\n"
                            f"Read server rules in   {rules_channel.mention}\n"
                            f"Get self roles from     {roles_channel.mention}",
                color=Colors.GOLD,
                timestamp=datetime.now()
            ).set_thumbnail(
                url=member.display_avatar
            ).set_footer(
                text=f"{self.user.display_name} Staff",
                icon_url=self.user.display_avatar
            )
        )

    async def on_member_remove(self, member: Member) -> None:
        """
        Called when a member leaves the server

        Args:
            member (Member): Leaving member
        """

        # Set receiver channel
        channel: TextChannel = self.get_channel(CONSOLE_CHANNEL_ID)

        # Send embed with random farewell msg to receiver channel
        await channel.send(
            embed=Embed(
                description=choice(
                    FAREWELL_MESSAGES
                ).format(
                    member.display_name
                ),
                color=Colors.RED
            )
        )

    async def on_message(self, message: Message) -> None:
        """
        Called when some user sends a messsage in the server

        Args:
            message (Message): Message sent by a user
        """

        # Warn if it's maintenance mode
        if (self.MAINTENANCE_MODE and
                message.channel != self.MAINTENANCE_CHANNEL):
            return

        # Check if it's a Webhook
        if message.webhook_id:
            # Check if the message is from Disboard
            if message.author.id == DISBOARD_ID:
                if "Bump done" in message.embeds[0].description:
                    self.bump_timer.update_bump_time(datetime.now())
                    self.dispatch("bump_done", 7200)
            return

        # AEWN: Animated Emojis Without Nitro
        if message.content.count(":") > 1:
            await self._animated_emojis(message)

    async def _animated_emojis(self, message: Message) -> None:
        """
        Animated Emojis Without Nitro

        Args:
            message (Message): Message with emojis
        """

        emoji = None
        temp = []

        # Iterate through all the words in the msg
        for word in message.content.split():

            # Check if some word is wrapped in between colons
            if word[0] == word[-1] == ":" and len(word) > 2 and word not in temp:

                try:
                    # Try to get the emoji with name `word`
                    emoji: Emoji = self.emoji_group.get_emoji(word[1:-1])

                    # Replace that word with emoji string
                    message.content = message.content.replace(word, str(emoji))

                    # Add the word to temp list so as to skip it
                    # in the next iterations
                    temp.append(word)

                # Raise AttributeError if not successfull
                except AttributeError:
                    pass

        # Check if there was an animated emoji in the msg
        if emoji:
            # Get all webhooks currently in the msg channel
            webhooks = await message.channel.webhooks()

            # Check if there exists a webhook with id
            # equal to bot's id. In that case, break
            webhook: Webhook
            for webhook in webhooks:
                if webhook.user.id == self.user.id:
                    break

            # Otherwise
            else:
                # Get msg author's avatar
                avatar: bytes = await message.author.display_avatar.read()

                # and create a new webhook for the channel
                webhook: Webhook = await message.channel.create_webhook(
                    name="iCODE-BOT",
                    avatar=avatar,
                    reason="Animated Emoji Usage"
                )

            # Send webhook to the channel with username as the name
            # of msg author and avatar as msg author's avatar
            await webhook.send(content=message.content,
                               username=message.author.display_name,
                               avatar_url=message.author.display_avatar)

            # Delete the original msg
            await message.delete()