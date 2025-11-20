import makeWASocket, { useMultiFileAuthState, DisconnectReason, Browsers } from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const logger = pino({ level: 'silent' });

class WhatsAppClient {
    constructor(sessionName = 'default') {
        this.sessionName = sessionName;
        this.sessionPath = path.join(__dirname, 'sessions', 'whatsapp', sessionName);
        this.sock = null;
        this.isConnected = false;
        this.qrCodeData = null;
        this.messageHandlers = [];
        this.connectionHandlers = [];
        
        if (!fs.existsSync(this.sessionPath)) {
            fs.mkdirSync(this.sessionPath, { recursive: true });
        }
    }

    async connect() {
        try {
            const { state, saveCreds } = await useMultiFileAuthState(this.sessionPath);

            this.sock = makeWASocket({
                auth: state,
                printQRInTerminal: true,
                logger,
                browser: Browsers.ubuntu('EMPIRE v13'),
                markOnlineOnConnect: false,
                getMessage: async (key) => {
                    return { conversation: '' };
                }
            });

            this.sock.ev.on('creds.update', saveCreds);

            this.sock.ev.on('connection.update', async (update) => {
                const { connection, lastDisconnect, qr } = update;

                if (qr) {
                    this.qrCodeData = qr;
                    const qrFilePath = path.join(__dirname, 'sessions', 'whatsapp', `${this.sessionName}_qr.txt`);
                    fs.writeFileSync(qrFilePath, qr);
                    
                    const qrPngPath = path.join(__dirname, 'sessions', 'whatsapp', `${this.sessionName}_qr.png`);
                    const QRCode = await import('qrcode');
                    await QRCode.toFile(qrPngPath, qr, {
                        errorCorrectionLevel: 'H',
                        type: 'png',
                        width: 500
                    });
                    
                    console.log(`[BAILEYS] QR Code generated: ${qrPngPath}`);
                    this.emitConnectionEvent('qr', { qr, qrFilePath, qrPngPath });
                }

                if (connection === 'close') {
                    const shouldReconnect = (lastDisconnect?.error instanceof Boom) &&
                        lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut;

                    console.log(`[BAILEYS] Connection closed. Reconnect: ${shouldReconnect}`);
                    
                    this.isConnected = false;
                    this.emitConnectionEvent('disconnected', { shouldReconnect, reason: lastDisconnect?.error });

                    if (shouldReconnect) {
                        setTimeout(() => this.connect(), 5000);
                    }
                } else if (connection === 'open') {
                    console.log(`[BAILEYS] ✅ Connected to WhatsApp: ${this.sessionName}`);
                    this.isConnected = true;
                    this.qrCodeData = null;
                    
                    const qrFiles = [
                        path.join(__dirname, 'sessions', 'whatsapp', `${this.sessionName}_qr.txt`),
                        path.join(__dirname, 'sessions', 'whatsapp', `${this.sessionName}_qr.png`)
                    ];
                    qrFiles.forEach(f => fs.existsSync(f) && fs.unlinkSync(f));
                    
                    this.emitConnectionEvent('connected', { sessionName: this.sessionName });
                }
            });

            this.sock.ev.on('messages.upsert', async ({ messages, type }) => {
                if (type !== 'notify') return;

                for (const msg of messages) {
                    if (msg.key.fromMe) continue;

                    const messageData = {
                        id: msg.key.id,
                        from: msg.key.remoteJid,
                        sender: msg.key.participant || msg.key.remoteJid,
                        timestamp: msg.messageTimestamp,
                        message: this.extractMessageText(msg),
                        isGroup: msg.key.remoteJid.endsWith('@g.us'),
                        raw: msg
                    };

                    console.log(`[BAILEYS] New message from ${messageData.from}: ${messageData.message}`);
                    this.emitMessage(messageData);
                }
            });

        } catch (error) {
            console.error(`[BAILEYS] Connection error:`, error);
            throw error;
        }
    }

    extractMessageText(msg) {
        if (msg.message?.conversation) return msg.message.conversation;
        if (msg.message?.extendedTextMessage?.text) return msg.message.extendedTextMessage.text;
        if (msg.message?.imageMessage?.caption) return msg.message.imageMessage.caption;
        if (msg.message?.videoMessage?.caption) return msg.message.videoMessage.caption;
        return '[Media]';
    }

    async sendMessage(jid, text, options = {}) {
        if (!this.isConnected) {
            throw new Error('WhatsApp not connected');
        }

        try {
            await this.sock.sendMessage(jid, {
                text: text,
                ...options
            });
            console.log(`[BAILEYS] Message sent to ${jid}`);
            return { success: true };
        } catch (error) {
            console.error(`[BAILEYS] Failed to send message:`, error);
            return { success: false, error: error.message };
        }
    }

    async sendImage(jid, imagePath, caption = '') {
        if (!this.isConnected) {
            throw new Error('WhatsApp not connected');
        }

        try {
            const imageBuffer = fs.readFileSync(imagePath);
            await this.sock.sendMessage(jid, {
                image: imageBuffer,
                caption: caption
            });
            console.log(`[BAILEYS] Image sent to ${jid}`);
            return { success: true };
        } catch (error) {
            console.error(`[BAILEYS] Failed to send image:`, error);
            return { success: false, error: error.message };
        }
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    onConnection(handler) {
        this.connectionHandlers.push(handler);
    }

    emitMessage(messageData) {
        this.messageHandlers.forEach(handler => {
            try {
                handler(messageData);
            } catch (error) {
                console.error('[BAILEYS] Message handler error:', error);
            }
        });
    }

    emitConnectionEvent(event, data) {
        this.connectionHandlers.forEach(handler => {
            try {
                handler(event, data);
            } catch (error) {
                console.error('[BAILEYS] Connection handler error:', error);
            }
        });
    }

    async disconnect() {
        if (this.sock) {
            await this.sock.logout();
            this.sock.end();
            this.isConnected = false;
            console.log(`[BAILEYS] Disconnected: ${this.sessionName}`);
        }
    }

    getStatus() {
        return {
            sessionName: this.sessionName,
            isConnected: this.isConnected,
            hasQR: !!this.qrCodeData
        };
    }
}

class WhatsAppManager {
    constructor() {
        this.clients = new Map();
        this.messageQueue = [];
        this.stateFile = path.join(__dirname, 'sessions', 'whatsapp', 'manager_state.json');
        this.httpServer = null;
    }

    async addClient(sessionName) {
        if (this.clients.has(sessionName)) {
            console.log(`[MANAGER] Client ${sessionName} already exists`);
            return this.clients.get(sessionName);
        }

        const client = new WhatsAppClient(sessionName);
        
        client.onMessage((messageData) => {
            this.messageQueue.push({
                sessionName,
                ...messageData,
                receivedAt: new Date().toISOString()
            });
            
            const queueFile = path.join(__dirname, 'sessions', 'whatsapp', 'message_queue.json');
            fs.writeFileSync(queueFile, JSON.stringify(this.messageQueue, null, 2));
        });

        client.onConnection((event, data) => {
            console.log(`[MANAGER] Connection event for ${sessionName}: ${event}`);
            const eventFile = path.join(__dirname, 'sessions', 'whatsapp', `${sessionName}_events.json`);
            const events = fs.existsSync(eventFile) ? JSON.parse(fs.readFileSync(eventFile, 'utf8')) : [];
            events.push({
                event,
                data,
                timestamp: new Date().toISOString()
            });
            fs.writeFileSync(eventFile, JSON.stringify(events, null, 2));
        });

        this.clients.set(sessionName, client);
        await client.connect();
        
        this.saveState();
        return client;
    }

    getClient(sessionName) {
        return this.clients.get(sessionName);
    }

    getAllClients() {
        return Array.from(this.clients.entries()).map(([name, client]) => ({
            name,
            status: client.getStatus()
        }));
    }

    async removeClient(sessionName) {
        const client = this.clients.get(sessionName);
        if (client) {
            await client.disconnect();
            this.clients.delete(sessionName);
            this.saveState();
            
            const sessionPath = path.join(__dirname, 'sessions', 'whatsapp', sessionName);
            if (fs.existsSync(sessionPath)) {
                fs.rmSync(sessionPath, { recursive: true, force: true });
            }
        }
    }

    getMessages(sessionName = null, limit = 50) {
        let messages = this.messageQueue;
        if (sessionName) {
            messages = messages.filter(m => m.sessionName === sessionName);
        }
        return messages.slice(-limit);
    }

    clearMessages() {
        this.messageQueue = [];
        const queueFile = path.join(__dirname, 'sessions', 'whatsapp', 'message_queue.json');
        fs.writeFileSync(queueFile, JSON.stringify([], null, 2));
    }

    saveState() {
        const state = {
            sessions: Array.from(this.clients.keys()),
            lastUpdated: new Date().toISOString()
        };
        const dir = path.dirname(this.stateFile);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(this.stateFile, JSON.stringify(state, null, 2));
    }

    async loadState() {
        if (fs.existsSync(this.stateFile)) {
            const state = JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));
            for (const sessionName of state.sessions) {
                console.log(`[MANAGER] Restoring session: ${sessionName}`);
                await this.addClient(sessionName);
            }
        }
    }

    startHTTPServer(port = 3000) {
        import('http').then(({ default: http }) => {
            this.httpServer = http.createServer(async (req, res) => {
                res.setHeader('Content-Type', 'application/json');
                
                const url = new URL(req.url, `http://${req.headers.host}`);
                const path = url.pathname;

                try {
                    if (path === '/status') {
                        res.writeHead(200);
                        res.end(JSON.stringify({
                            clients: this.getAllClients(),
                            messagesInQueue: this.messageQueue.length
                        }));
                    } else if (path === '/messages') {
                        const sessionName = url.searchParams.get('session');
                        const limit = parseInt(url.searchParams.get('limit')) || 50;
                        res.writeHead(200);
                        res.end(JSON.stringify(this.getMessages(sessionName, limit)));
                    } else if (path === '/send' && req.method === 'POST') {
                        let body = '';
                        req.on('data', chunk => { body += chunk.toString(); });
                        req.on('end', async () => {
                            const { sessionName, jid, message } = JSON.parse(body);
                            const client = this.getClient(sessionName);
                            if (!client) {
                                res.writeHead(404);
                                res.end(JSON.stringify({ error: 'Session not found' }));
                                return;
                            }
                            const result = await client.sendMessage(jid, message);
                            res.writeHead(200);
                            res.end(JSON.stringify(result));
                        });
                    } else {
                        res.writeHead(404);
                        res.end(JSON.stringify({ error: 'Not found' }));
                    }
                } catch (error) {
                    res.writeHead(500);
                    res.end(JSON.stringify({ error: error.message }));
                }
            });

            this.httpServer.listen(port, () => {
                console.log(`[MANAGER] HTTP server running on port ${port}`);
            });
        });
    }
}

const manager = new WhatsAppManager();

if (process.argv[2] === 'server') {
    const port = process.argv[3] || 3000;
    manager.startHTTPServer(port);
    manager.loadState();
    console.log(`[BAILEYS] WhatsApp Manager started in server mode on port ${port}`);
} else if (process.argv[2] === 'add') {
    const sessionName = process.argv[3] || 'default';
    manager.addClient(sessionName).then(() => {
        console.log(`[BAILEYS] Client added: ${sessionName}`);
    });
} else {
    console.log(`
EMPIRE v13 - Baileys WhatsApp Client
    
Usage:
  node baileys_client.js server [port]     - Start HTTP server (default port: 3000)
  node baileys_client.js add [sessionName] - Add new WhatsApp session
  
Examples:
  node baileys_client.js server 3000
  node baileys_client.js add my-number
    `);
}

export { WhatsAppClient, WhatsAppManager, manager };
