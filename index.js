require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V27 starting...");

// ===== MAIN MENU =====
const mainMenu = {
  reply_markup: {
    keyboard: [
      ["🚀 Start", "📊 Status"],
      ["🧰 Tools", "❓ Help"]
    ],
    resize_keyboard: true
  }
};

// ===== TOOLS MENU =====
const toolsMenu = {
  reply_markup: {
    keyboard: [
      ["💰 BTC Price", "💎 ETH Price"],
      ["⚡ SOL Price"],
      ["⬅️ Back"]
    ],
    resize_keyboard: true
  }
};

// ===== START =====
bot.onText(/\/start|🚀 Start/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🔥 Miserbot V27\nChoose an option:", mainMenu);
});

// ===== HELP =====
bot.onText(/\/help|❓ Help/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    "Commands:\n/start\n/help\n/status\n/ping\n\nOr use buttons below 👇",
    mainMenu
  );
});

// ===== STATUS =====
bot.onText(/\/status|📊 Status/i, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running smoothly.");
});

// ===== TOOLS MENU =====
bot.onText(/🧰 Tools/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🧰 Tools Menu:", toolsMenu);
});

// ===== BACK =====
bot.onText(/⬅️ Back/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🔙 Back to main menu:", mainMenu);
});

// ===== BTC PRICE =====
bot.onText(/BTC Price/i, async (msg) => {
  try {
    const res = await axios.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');
    const price = res.data.bitcoin.usd;

    bot.sendMessage(msg.chat.id, `💰 BTC: $${price.toLocaleString()}`);
  } catch (err) {
    bot.sendMessage(msg.chat.id, "❌ Failed to fetch BTC price.");
  }
});

// ===== ETH PRICE =====
bot.onText(/ETH Price/i, async (msg) => {
  try {
    const res = await axios.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd');
    const price = res.data.ethereum.usd;

    bot.sendMessage(msg.chat.id, `💎 ETH: $${price.toLocaleString()}`);
  } catch (err) {
    bot.sendMessage(msg.chat.id, "❌ Failed to fetch ETH price.");
  }
});

// ===== SOL PRICE =====
bot.onText(/SOL Price/i, async (msg) => {
  try {
    const res = await axios.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd');
    const price = res.data.solana.usd;

    bot.sendMessage(msg.chat.id, `⚡ SOL: $${price.toLocaleString()}`);
  } catch (err) {
    bot.sendMessage(msg.chat.id, "❌ Failed to fetch SOL price.");
  }
});
