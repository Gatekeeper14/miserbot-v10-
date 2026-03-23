const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== USER STATE =====
let users = {}; 
// { chatId: { mode: "main" | "trading" | "family" | "credit" } }

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== PRICE FETCH (STABLE) =====
async function getBTC() {
  try {
    const res = await axios.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
    return parseFloat(res.data.price);
  } catch {
    return null;
  }
}

// ===== MENU SYSTEM =====

function mainMenu(chatId) {
  users[chatId].mode = "main";

  send(chatId,
`👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status

Type a number or name`);
}

function tradingMenu(chatId) {
  users[chatId].mode = "trading";

  send(chatId,
`💰 Trading Hub

1. BTC Price
2. Back`);
}

function familyMenu(chatId) {
  users[chatId].mode = "family";

  send(chatId,
`❤️ Family Assistant

(Coming next)
Type 'back'`);
}

function creditMenu(chatId) {
  users[chatId].mode = "credit";

  send(chatId,
`💳 Credit System

(Coming next)
Type 'back'`);
}

// ===== COMMAND HANDLER =====

bot.on("message", async (msg) => {
  try {
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const text = msg.text.toLowerCase();

    if (!users[chatId]) {
      users[chatId] = { mode: "main" };
      return mainMenu(chatId);
    }

    const mode = users[chatId].mode;

    // ===== GLOBAL COMMANDS =====
    if (text === "/start" || text === "menu") {
      return mainMenu(chatId);
    }

    if (text === "status") {
      return send(chatId, "✅ Bot running (V40 HUB)");
    }

    // ===== MAIN MENU =====
    if (mode === "main") {
      if (text.includes("1") || text.includes("trading")) {
        return tradingMenu(chatId);
      }

      if (text.includes("2") || text.includes("family")) {
        return familyMenu(chatId);
      }

      if (text.includes("3") || text.includes("credit")) {
        return creditMenu(chatId);
      }

      if (text.includes("4")) {
        return send(chatId, "⚙️ System stable");
      }
    }

    // ===== TRADING MENU =====
    if (mode === "trading") {

      if (text.includes("btc")) {
        const price = await getBTC();

        if (!price) {
          return send(chatId, "❌ Price error");
        }

        return send(chatId, `💰 BTC: $${price.toFixed(2)}`);
      }

      if (text.includes("back") || text.includes("2")) {
        return mainMenu(chatId);
      }
    }

    // ===== FAMILY MENU =====
    if (mode === "family") {
      if (text.includes("back")) {
        return mainMenu(chatId);
      }
    }

    // ===== CREDIT MENU =====
    if (mode === "credit") {
      if (text.includes("back")) {
        return mainMenu(chatId);
      }
    }

  } catch (err) {
    console.log("Error:", err.message);
  }
});

console.log("🔥 Miserbot V40 HUB running");
