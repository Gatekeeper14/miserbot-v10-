const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== USER STATE =====
let users = {};
// { chatId: { mode, credit, family } }

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== BTC PRICE =====
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

1. Add Member
2. List Members
3. Send Check-in
4. Back`);
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
        credit: { started: false, day: 1 },
        family: { members: [], step: null }
      };
      return mainMenu(chatId);
    }

    const user = users[chatId];
    const mode = user.mode;

    // ===== GLOBAL =====
    if (text === "/start" || text === "menu") return mainMenu(chatId);

    if (text === "status") return send(chatId, "✅ Bot running (V42)");

    if (text.includes("my id")) return send(chatId, `🆔 Your ID: ${chatId}`);

    if (text.includes("help")) {
      return send(chatId,
`❓ Help

Use menu:
1 Trading
2 Family
3 Credit

Commands:
BTC Price
My ID
Status`);
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
        if (!price) return send(chatId, "❌ Price error");
        return send(chatId, `💰 BTC: $${price.toFixed(2)}`);
      }
      if (text.includes("back") || text.includes("2")) return mainMenu(chatId);
    }

    // ===== FAMILY =====
    if (mode === "family") {

      // STEP: ADD MEMBER NAME
      if (user.family.step === "add_name") {
        user.family.tempName = msg.text;
        user.family.step = "add_id";
        return send(chatId, "📱 Send their Chat ID");
      }

      // STEP: ADD MEMBER ID
      if (user.family.step === "add_id") {
        user.family.members.push({
          name: user.family.tempName,
          id: msg.text
        });

        user.family.step = null;

        return send(chatId, "✅ Member added");
      }

      if (text.includes("add")) {
        user.family.step = "add_name";
        return send(chatId, "👤 Send name");
      }

      if (text.includes("list")) {
        if (user.family.members.length === 0) {
          return send(chatId, "No members saved");
        }

        let list = "👨‍👩‍👧 Members:\n";
        user.family.members.forEach((m, i) => {
          list += `${i + 1}. ${m.name}\n`;
        });

        return send(chatId, list);
      }

      if (text.includes("check")) {
        if (user.family.members.length === 0) {
          return send(chatId, "No members saved");
        }

        user.family.members.forEach(m => {
          send(m.id, `❤️ Check-in from your assistant:\nHope you're doing well!`);
        });

        return send(chatId, "✅ Check-in sent");
      }

      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

    // ===== CREDIT =====
    if (mode === "credit") {

      const credit = user.credit;

      if (text.includes("start")) {
        credit.started = true;
        credit.day = 1;

        return send(chatId,
`💳 Credit Plan Started

Day 1:
Get your credit report
Review negative accounts`);
      }

      if (text.includes("next")) {
        if (!credit.started) return send(chatId, "⚠️ Start first");

        credit.day++;

        return send(chatId, `📅 Day ${credit.day}: Stay consistent`);
      }

      if (text.includes("progress")) {
        if (!credit.started) return send(chatId, "⚠️ Start first");

        return send(chatId, `📊 Day ${credit.day}`);
      }

      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

  } catch (err) {
    console.log(err.message);
  }
});

console.log("🔥 Miserbot V42 running");
