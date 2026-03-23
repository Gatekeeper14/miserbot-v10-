require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V26 starting...");

// =========================
// START COMMAND
// =========================
bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id,
        "🔥 Miserbot V26\nChoose an option:",
        {
            reply_markup: {
                keyboard: [
                    ["🚀 Start", "📊 Status"],
                    ["🧰 Tools", "❓ Help"]
                ],
                resize_keyboard: true
            }
        }
    );
});

// =========================
// HELP
// =========================
bot.onText(/\/help/, (msg) => {
    bot.sendMessage(msg.chat.id,
        "Commands:\n/start\n/help\n/status\n/ping"
    );
});

// =========================
// STATUS
// =========================
bot.onText(/\/status/, (msg) => {
    bot.sendMessage(msg.chat.id, "✅ Bot running smoothly.");
});

// =========================
// BUTTON HANDLER
// =========================
bot.on('message', async (msg) => {
    const text = msg.text;

    // START BUTTON
    if (text === "🚀 Start") {
        bot.sendMessage(msg.chat.id, "System initialized.");
    }

    // STATUS BUTTON
    if (text === "📊 Status") {
        bot.sendMessage(msg.chat.id, "✅ Bot running smoothly.");
    }

    // HELP BUTTON
    if (text === "❓ Help") {
        bot.sendMessage(msg.chat.id, "Use the buttons to navigate.");
    }

    // TOOLS MENU
    if (text === "🧰 Tools") {
        bot.sendMessage(msg.chat.id,
            "🧰 Tools Menu:",
            {
                reply_markup: {
                    keyboard: [
                        ["💰 BTC Price"],
                        ["⬅️ Back"]
                    ],
                    resize_keyboard: true
                }
            }
        );
    }

    // BACK BUTTON
    if (text === "⬅️ Back") {
        bot.sendMessage(msg.chat.id,
            "Main Menu:",
            {
                reply_markup: {
                    keyboard: [
                        ["🚀 Start", "📊 Status"],
                        ["🧰 Tools", "❓ Help"]
                    ],
                    resize_keyboard: true
                }
            }
        );
    }

    // =========================
    // REAL BTC PRICE (API)
    // =========================
    if (text === "💰 BTC Price") {
        try {
            const res = await axios.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            );

            const price = res.data.bitcoin.usd;

            bot.sendMessage(msg.chat.id,
                `💰 BTC Price: $${price.toLocaleString()}`
            );

        } catch (err) {
            bot.sendMessage(msg.chat.id,
                "❌ Failed to fetch BTC price."
            );
        }
    }
});
