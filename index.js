require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

const VERSION = "V25";

console.log(`🚀 Miserbot ${VERSION} starting...`);

// =======================
// MAIN KEYBOARD
// =======================
const mainKeyboard = {
  reply_markup: {
    keyboard: [
      ['🚀 Start', '📊 Status'],
      ['🧰 Tools', '❓ Help']
    ],
    resize_keyboard: true
  }
};

// =======================
// TOOLS KEYBOARD
// =======================
const toolsKeyboard = {
  reply_markup: {
    keyboard: [
      ['💰 BTC Price'],
      ['⬅️ Back']
    ],
    resize_keyboard: true
  }
};

// =======================
// START
// =======================
bot.onText(/\/start|🚀 Start/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    `🔥 Miserbot ${VERSION}\nChoose an option:`,
    mainKeyboard
  );
});

// =======================
// STATUS
// =======================
bot.onText(/\/status|📊 Status/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    `✅ Bot running\nVersion: ${VERSION}`
  );
});

// =======================
// HELP
// =======================
bot.onText(/\/help|❓ Help/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    `/start\n/help\n/status\n/ping\n/version`
  );
});

// =======================
// TOOLS MENU
// =======================
bot.onText(/\/tools|🧰 Tools/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    `🧰 Tools Menu:`,
    toolsKeyboard
  );
});

// =======================
// BTC TOOL (REAL API)
// =======================
bot.onText(/💰 BTC Price/i, async (msg) => {
  try {
    const res = await axios.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json");
    const price = res.data.bpi.USD.rate;
    bot.sendMessage(msg.chat.id, `₿ BTC Price: $${price}`);
  } catch {
    bot.sendMessage(msg.chat.id, "Error fetching BTC price.");
  }
});

// =======================
// BACK BUTTON
// =======================
bot.onText(/⬅️ Back/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    `🔥 Miserbot ${VERSION}`,
    mainKeyboard
  );
});

// =======================
// PING
// =======================
bot.onText(/\/ping/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🏓 Pong!");
});

// =======================
// VERSION
// =======================
bot.onText(/\/version/i, (msg) => {
  bot.sendMessage(msg.chat.id, `📦 ${VERSION}`);
});
