require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V29 starting...");

// ===== STORE ACTIVE INTERVALS =====
const liveSessions = {};

// ===== MAIN MENU =====
const mainMenu = {
  reply_markup: {
    keyboard: [
      ["🚀 Start", "📊 Status"],
      ["🧰 Tools", "📊 Dashboard"],
      ["🟢 Live Prices", "🔴 Stop Live"],
      ["❓ Help"]
    ],
    resize_keyboard: true
  }
};

// ===== TOOLS MENU =====
const toolsMenu = {
  reply_markup: {
    keyboard: [
      ["💰 BTC Price", "⚡ SOL Price"],
      ["⬅️ Back"]
    ],
    resize_keyboard: true
  }
};

// ===== START =====
bot.onText(/\/start|🚀 Start/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🔥 Miserbot V29\nChoose an option:", mainMenu);
});

// ===== HELP =====
bot.onText(/\/help|❓ Help/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    "Commands:\n/start\n/help\n/status\n\nUse buttons below 👇",
    mainMenu
  );
});

// ===== STATUS =====
bot.onText(/\/status|📊 Status/i, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running smoothly.");
});

// ===== TOOLS =====
bot.onText(/🧰 Tools/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🧰 Tools Menu:", toolsMenu);
});

// ===== BACK =====
bot.onText(/⬅️ Back/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🔙 Back to main menu:", mainMenu);
});

// ===== BTC =====
bot.onText(/BTC Price/i, async (msg) => {
  try {
    const res = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    );

    const price = res.data.bitcoin.usd;
    bot.sendMessage(msg.chat.id, `💰 BTC: $${price.toLocaleString()}`);
  } catch {
    bot.sendMessage(msg.chat.id, "❌ BTC fetch failed.");
  }
});

// ===== SOL =====
bot.onText(/SOL Price/i, async (msg) => {
  try {
    const res = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd'
    );

    const price = res.data.solana.usd;
    bot.sendMessage(msg.chat.id, `⚡ SOL: $${price.toLocaleString()}`);
  } catch {
    bot.sendMessage(msg.chat.id, "❌ SOL fetch failed.");
  }
});

// ===== DASHBOARD =====
bot.onText(/📊 Dashboard/i, async (msg) => {
  try {
    const res = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,solana&vs_currencies=usd'
    );

    const btc = res.data.bitcoin.usd;
    const sol = res.data.solana.usd;

    bot.sendMessage(msg.chat.id,
`📊 Crypto Dashboard

💰 BTC: $${btc.toLocaleString()}
⚡ SOL: $${sol.toLocaleString()}`
    );
  } catch {
    bot.sendMessage(msg.chat.id, "❌ Failed to load dashboard.");
  }
});

// ===== LIVE PRICES START =====
bot.onText(/🟢 Live Prices/i, (msg) => {
  const chatId = msg.chat.id;

  if (liveSessions[chatId]) {
    bot.sendMessage(chatId, "⚠️ Live already running.");
    return;
  }

  bot.sendMessage(chatId, "🟢 Live prices started (updates every 10s)");

  liveSessions[chatId] = setInterval(async () => {
    try {
      const res = await axios.get(
        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,solana&vs_currencies=usd'
      );

      const btc = res.data.bitcoin.usd;
      const sol = res.data.solana.usd;

      bot.sendMessage(chatId,
`📡 Live Update

💰 BTC: $${btc.toLocaleString()}
⚡ SOL: $${sol.toLocaleString()}`
      );
    } catch {
      bot.sendMessage(chatId, "❌ Live update failed.");
    }
  }, 10000); // every 10 seconds
});

// ===== STOP LIVE =====
bot.onText(/🔴 Stop Live/i, (msg) => {
  const chatId = msg.chat.id;

  if (liveSessions[chatId]) {
    clearInterval(liveSessions[chatId]);
    delete liveSessions[chatId];
    bot.sendMessage(chatId, "🔴 Live updates stopped.");
  } else {
    bot.sendMessage(chatId, "⚠️ No live session running.");
  }
});
