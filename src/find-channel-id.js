/**
 * Helper script to find your Telegram Channel ID
 * 
 * Steps:
 * 1. Add your bot as admin to the channel
 * 2. Send a message in the channel
 * 3. Run this script: npm run find-channel
 */

require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

const token = process.env.TELEGRAM_BOT_TOKEN;

if (!token) {
    console.error('❌ TELEGRAM_BOT_TOKEN is not set in .env file');
    process.exit(1);
}

console.log('🔍 Searching for your Channel ID...');
console.log('📌 Make sure you have:');
console.log('   1. Added the bot as ADMIN to your channel');
console.log('   2. Sent at least ONE message in the channel');
console.log('');

const bot = new TelegramBot(token, { polling: false });

async function findChannelId() {
    try {
        const response = await bot.getUpdates({ offset: 0, limit: 100 });
        
        if (response.length === 0) {
            console.log('⚠️  No updates found.');
            console.log('');
            console.log('💡 Try these steps:');
            console.log('   1. Open your Telegram channel "Gold&New"');
            console.log('   2. Go to Manage → Administrators → Add Administrator');
            console.log('   3. Search for your bot and add it as admin');
            console.log('   4. Send a message in the channel');
            console.log('   5. Run this script again: npm run find-channel');
            return;
        }

        console.log('📋 Found updates! Here are your chats:\n');
        
        const seenChats = new Set();
        
        for (const update of response) {
            let chat = null;
            
            if (update.message) {
                chat = update.message.chat;
            } else if (update.channel_post) {
                chat = update.channel_post.chat;
            } else if (update.my_chat_member) {
                chat = update.my_chat_member.chat;
            }
            
            if (chat && !seenChats.has(chat.id)) {
                seenChats.add(chat.id);
                const type = chat.type || 'unknown';
                const title = chat.title || chat.first_name || 'N/A';
                const username = chat.username ? `@${chat.username}` : 'No username';
                
                console.log(`  ┌─────────────────────────────────`);
                console.log(`  │ 📛 Name: ${title}`);
                console.log(`  │ 🆔 Chat ID: ${chat.id}`);
                console.log(`  │ 📝 Type: ${type}`);
                console.log(`  │ 👤 Username: ${username}`);
                console.log(`  └─────────────────────────────────`);
                console.log('');
            }
        }
        
        if (seenChats.size === 0) {
            console.log('⚠️  Updates found but no chat info. Send a message in your channel and try again.');
        } else {
            console.log('✅ Copy the Chat ID of your channel and paste it into .env file as TELEGRAM_CHAT_ID');
        }
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

findChannelId();
