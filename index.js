const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== USER STATE =====
let users = {};
// { chatId: { mode: "main" | "trading" | "family" | "credit", credit: { started: false, day: 1 } } }

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== BTC PRICE (BULLETPROOF) =====
async function getBTC() {
  try {
    const res = await axios.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
    return parseFloat(res.data.price);
  } catch {
    try {
      const res = await axios.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
      return res.data.bitcoin.usd;
    } catch {
      try {
        const res = await axios.get("https://api.coinbase.com/v2/prices/BTC-USD/spot");
        return parseFloat(res.data.data.amount);
      } catch {
        return null;
      }
    }
  }
}

// ===== MENUS =====

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

1. Start Plan
2. Next Step
3. Progress
4. Back`);
}

// ===== MAIN HANDLER =====

bot.on("message", async (msg) => {
  try {
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const text = msg.text.toLowerCase();

    // INIT USER
    if (!users[chatId]) {
      users[chatId] = {
        mode: "main",
        credit: {
          started: false,
          day: 1
        }
      };
      return mainMenu(chatId);
    }

    const mode = users[chatId].mode;

    // ===== GLOBAL =====
    if (text === "/start" || text === "menu") {
      return mainMenu(chatId);
    }

    if (text === "status") {
      return send(chatId, "✅ Bot running (V41)");
    }

    // ===== MAIN MENU =====
    if (mode === "main") {
      if (text.includes("1") || text.includes("trading")) return tradingMenu(chatId);
      if (text.includes("2") || text.includes("family")) return familyMenu(chatId);
      if (text.includes("3") || text.includes("credit")) return creditMenu(chatId);
      if (text.includes("4")) return send(chatId, "⚙️ System stable");
    }

    // ===== TRADING =====
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

    // ===== FAMILY =====
    if (mode === "family") {
      if (text.includes("back")) return mainMenu(chatId);
    }

    // ===== CREDIT =====
    if (mode === "credit") {

      const credit = users[chatId].credit;

      if (text.includes("start")) {
        credit.started = true;
        credit.day = 1;

        return send(chatId,
`💳 Credit Plan Started

📅 Day 1:
✔ Get your credit report
✔ Review negative accounts

🎯 Goal: Awareness`);
      }

      if (text.includes("next")) {
        if (!credit.started) {
          return send(chatId, "⚠️ Start plan first");
        }

        credit.day++;

        let step = "";

        if (credit.day === 2) {
          step = `📅 Day 2:
✔ Dispute incorrect items

🎯 Clean errors`;
        } else if (credit.day === 3) {
          step = `📅 Day 3:
✔ Lower balances under 30%

🎯 Reduce utilization`;
        } else if (credit.day === 4) {
          step = `📅 Day 4:
✔ Setup auto-pay

🎯 Never miss payments`;
        } else if (credit.day === 5) {
          step = `📅 Day 5:
✔ Maintain low usage

📈 Score improving`;
        } else {
          step = `📅 Day ${credit.day}:
✔ Stay consistent

📈 Progress continues`;
        }

        return send(chatId, step);
      }

      if (text.includes("progress")) {
        if (!credit.started) {
          return send(chatId, "⚠️ Start plan first");
        }

        const percent = Math.min(credit.day * 15, 100);

        return send(chatId,
`📊 Credit Progress

Day: ${credit.day}
Progress: ${percent}%

Stay consistent`);
      }

      if (text.includes("back") || text.includes("4")) {
        return mainMenu(chatId);
      }
    }

  } catch (err) {
    console.log("Error:", err.message);
  }
});

console.log("🔥 Miserbot V41 running");
