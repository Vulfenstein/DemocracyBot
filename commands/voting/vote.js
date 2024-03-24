const { ActionRowBuilder, ButtonBuilder, ButtonStyle, ComponentType, SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('vote')
        .setDescription('Vote to kick a user currently in voice chat')
        .addUserOption(option =>
            option
                .setName('target')
                .setDescription('user')
                .setRequired(true))
        .addStringOption(option =>
            option
                .setName('reason')
                .setDescription('The reason for the vote'),
        ),
    async execute(interaction) {
        const userToKick = interaction.options.getUser('target');
        const reasonForKick = interaction.options.getString('reason') ?? 'No reason';

        // Check that user who initiated vote is in voice channel
        if (interaction.member.voice.channel == null) {
            return interaction.reply({ content: 'Only users in voice can call a vote.', ephemeral: true });
        }

        const usersCurrentlyInVoice = interaction.member.voice.channel.members;
        let userDetails;
        const userVotes = new Map();

        // check for user in voice channel
        usersCurrentlyInVoice.each(user => {
            userVotes.set(user.id, undefined);
            if (user.id == userToKick.id) {
                userDetails = user;
            }
        });

        // If user to kick is not in voice channel return error response
        if (userDetails == undefined) {
            return interaction.reply({ content: `${userToKick} is not currently in voice channel.`, ephemeral: true });
        }

        // Create buttons for voting poll
        const yesButton = new ButtonBuilder()
            .setCustomId('Yes')
            .setLabel('Yes')
            .setStyle(ButtonStyle.Success);

        const noButton = new ButtonBuilder()
            .setCustomId('No')
            .setLabel('No')
            .setStyle(ButtonStyle.Danger);

        const row = new ActionRowBuilder()
            .addComponents(yesButton, noButton);

        // emit voting message and create collector for responses. Voting will end automatically after 30 seconds
        const response = await interaction.reply({ content: `${interaction.user} has voted to kick ${interaction.options.getUser('target')}\n Do you agree?`, components: [row] });
        const collector = response.createMessageComponentCollector({ componentType: ComponentType.Button, time: 10000 });

        // Collect votes, ensure users currently in voice chat vote only once
        collector.on('collect', async i => {
            if (userVotes.get(i.user.id) != undefined) {
                await i.reply({ content: 'You have already voted', ephemeral: true });
            }
            else {

                // Set vote choice for the given user and display message
                userVotes.set(i.user.id, i.customId);
                const selection = i.customId;
                await i.reply(`${i.user} has voted ${selection}`);

                collector.stop('kick_user_yes');

                // Check if end voting condition has been met
                let yesVotes, noVotes = 0;
                userVotes.forEach((value) => {
                    if (value == 'Yes') yesVotes++;
                    else if (value == 'No') noVotes++;
                });

                // if all have voted or a majority has been established, complete voting period
                if (yesVotes > (userVotes.length / 2)) {
                    collector.stop('kick_user_yes');
                }
                else if (noVotes > (userVotes.length / 2)) {
                    collector.stop('kick_user_no');
                }
                else if (yesVotes + noVotes == userVotes.length) {
                    collector.stop('kick_user_tie');
                }
            }
        });

        // When voting has ended due to time or voting complete. Handle results
        collector.on('end', (collected, reason) => {
            switch (reason) {
                case 'kick_user_yes':
                    userDetails.voice.disconnect();
                    break;
                case 'kick_user_no':
                case 'kick_user_tie':
            }
            console.log(collected);
            console.log(reason);
        });

    },
};