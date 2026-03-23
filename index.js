require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V30 starting...");

// ===== LIVE SESSION STORAGE =====
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

// ===== SAFE FETCH FUNCTION =====
async function getPrices() {
  try {
    const res = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,solana&vs_currencies=usd',
      { timeout: 5000 }
    );

    return {
      btc: res.data.bitcoin.usd,
      sol: res.data.solana.usd
    };
  } catch (err) {
    return null; // silent fail
  }
}

// ===== START =====
bot.onText(/\/start|🚀 Start/i, (msg) => {
  bot.sendMessage(msg.chat.id, "🔥 Miserbot V30\nChoose an option:", mainMenu);
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
  const data = await getPrices();

  if (!data) {
    bot.sendMessage(msg.chat.id, "⚠️ Try again in a moment...");
    return;
  }

  bot.sendMessage(msg.chat.id, `💰 BTC: $${data.btc.toLocaleString()}`);
});

// ===== SOL =====
bot.onText(/SOL Price/i, async (msg) => {
  const data = await getPrices();

  if (!data) {
    bot.sendMessage(msg.chat.id, "⚠️ Try again in a moment...");
    return;
  }

  bot.sendMessage(msg.chat.id, `⚡ SOL: $${data.sol.toLocaleString()}`);
});

// ===== DASHBOARD =====
bot.onText(/📊 Dashboard/i, async (msg) => {
  const data = await getPrices();

  if (!data) {
    bot.sendMessage(msg.chat.id, "⚠️ Dashboard temporarily unavailable.");
    return;
  }

  bot.sendMessage(msg.chat.id,
`📊 Crypto Dashboard

💰 BTC: $${data.btc.toLocaleString()}
⚡ SOL: $${data.sol.toLocaleString()}`
  );
});

// ===== LIVE START =====
bot.onText(/🟢 Live Prices/i, (msg) => {
  const chatId = msg.chat.id;

  if (liveSessions[chatId]) {
    bot.sendMessage(chatId, "⚠️ Live already running.");
    return;
  }

  bot.sendMessage(chatId, "🟢 Live started (updates every 20s)");

  liveSessions[chatId] = setInterval(async () => {
    const data = await getPrices();

    if (!data) return; // no spam

    bot.sendMessage(chatId,
`📡 Live Update

💰 BTC: $${data.btc.toLocaleString()}
⚡ SOL: $${data.sol.toLocaleString()}`
    );
  }, 20000); // slower = safer
});

// ===== STOP LIVE =====
bot.onText(/🔴 Stop Live/i, (msg) => {
  const chatId = msg.chat.id;

  if (liveSessions[chatId]) {
    clearInterval(liveSessions[chatId]);
    delete liveSessions[chatId];
    bot.sendMessage(chatId, "🔴 Live stopped.");
  } else {
    bot.sendMessage(chatId, "⚠️ No live session.");
  }
});
