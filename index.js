const TelegramBot = require("node-telegram-bot-api");

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

// ===== STORAGE =====
let userState = {};
let familyContacts = {};
let familyMode = {};

// ===== MAIN MENU =====
function showMenu(chatId) {
    bot.sendMessage(chatId,
`👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status
5. 🤖 Auto Mode

Type a number or name`
    );
}

// ===== FAMILY SYSTEM =====
function showFamilyMenu(chatId) {
    bot.sendMessage(chatId,
`❤️ Family System

1. Add Contact
2. Send Message
3. List Contacts
4. Back

Type option number`
    );
}

function addFamilyContact(chatId, name, targetId) {
    if (!familyContacts[chatId]) familyContacts[chatId] = [];
    familyContacts[chatId].push({ name, id: targetId });
}

function sendFamilyMessage(chatId, name, message) {
    const contacts = familyContacts[chatId] || [];
    const person = contacts.find(p => p.name.toLowerCase() === name.toLowerCase());

    if (!person) {
        bot.sendMessage(chatId, "❌ Contact not found");
        return;
    }

    bot.sendMessage(person.id, `📩 Message from your assistant:\n\n${message}`);
    bot.sendMessage(chatId, `✅ Sent to ${person.name}`);
}

function handleFamily(chatId, text) {

    if (!familyMode[chatId]) {
        if (text === "2" || text.toLowerCase() === "family") {
            showFamilyMenu(chatId);
            familyMode[chatId] = { step: "menu" };
            return true;
        }
    }

    const mode = familyMode[chatId];
    if (!mode) return false;

    if (mode.step === "menu") {
        if (text === "1") {
            bot.sendMessage(chatId, "Enter name:");
            mode.step = "add_name";
        }
        else if (text === "2") {
            bot.sendMessage(chatId, "Enter contact name:");
            mode.step = "send_name";
        }
        else if (text === "3") {
            const contacts = familyContacts[chatId] || [];
            if (contacts.length === 0) {
                bot.sendMessage(chatId, "No contacts saved");
            } else {
                let list = "📋 Contacts:\n";
                contacts.forEach(c => list += `• ${c.name} (${c.id})\n`);
                bot.sendMessage(chatId, list);
            }
        }
        else if (text === "4" || text.toLowerCase() === "back") {
            familyMode[chatId] = null;
            showMenu(chatId);
        }
        return true;
    }

    if (mode.step === "add_name") {
        mode.name = text;
        bot.sendMessage(chatId, "Enter their Chat ID:");
        mode.step = "add_id";
        return true;
    }

    if (mode.step === "add_id") {
        addFamilyContact(chatId, mode.name, text);
        bot.sendMessage(chatId, `✅ ${mode.name} added`);
        mode.step = "menu";
        showFamilyMenu(chatId);
        return true;
    }

    if (mode.step === "send_name") {
        mode.name = text;
        bot.sendMessage(chatId, "Enter message:");
        mode.step = "send_message";
        return true;
    }

    if (mode.step === "send_message") {
        sendFamilyMessage(chatId, mode.name, text);
        mode.step = "menu";
        showFamilyMenu(chatId);
        return true;
    }

    return false;
}

// ===== BASIC COMMANDS =====
bot.onText(/\/start/, (msg) => {
    showMenu(msg.chat.id);
});

bot.on("message", async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    if (!text) return;

    // ===== FAMILY HANDLER =====
    if (handleFamily(chatId, text)) return;

    // ===== MAIN MENU =====
    if (text.toLowerCase() === "menu") {
        showMenu(chatId);
        return;
    }

    if (text === "1" || text.toLowerCase() === "trading") {
        bot.sendMessage(chatId,
`💰 Trading Hub

1. BTC Price
2. Back`
        );
        userState[chatId] = "trading";
        return;
    }

    if (text === "4" || text.toLowerCase() === "status") {
        bot.sendMessage(chatId, "✅ Bot running\nPlan: FREE");
        return;
    }

    if (text === "5" || text.toLowerCase() === "auto mode") {
        bot.sendMessage(chatId, "🤖 Auto Mode coming soon");
        return;
    }

    // ===== TRADING =====
    if (userState[chatId] === "trading") {
        if (text === "1" || text.toLowerCase() === "btc price") {
            try {
                const res = await fetch("https://api.coindesk.com/v1/bpi/currentprice/BTC.json");
                const data = await res.json();
                const price = data.bpi.USD.rate;

                bot.sendMessage(chatId, `💰 BTC: $${price}`);
            } catch (err) {
                bot.sendMessage(chatId, "❌ Price error");
            }
            return;
        }

        if (text === "2" || text.toLowerCase() === "back") {
            userState[chatId] = null;
            showMenu(chatId);
            return;
        }
    }

});
