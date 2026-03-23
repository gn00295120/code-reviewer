import express from "express";
import { createServer } from "http";
import { WebSocketServer, WebSocket } from "ws";
import path from "path";
import fs from "fs";
import reviewRoutes, { activeSessions } from "./routes/reviews";
import settingsRoutes from "./routes/settings";

const PORT = parseInt(process.env.PORT || "3001", 10);

const app = express();
const server = createServer(app);

// CORS middleware
const ALLOWED_ORIGINS = [
  "http://localhost:3001",
  "http://127.0.0.1:3001",
  "http://localhost:5173",
];

app.use((req, res, next) => {
  const origin = req.headers.origin || "";
  if (ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader(
      "Access-Control-Allow-Methods",
      "GET, POST, PUT, DELETE, PATCH"
    );
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  }
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  next();
});

app.use(express.json());

// Health check (must be before static catch-all)
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "swarmforge-desktop" });
});

// API routes
app.use("/api/reviews", reviewRoutes);
app.use("/api/settings", settingsRoutes);

// Serve built React app in production (catch-all MUST be last)
const distDir = path.join(__dirname, "..", "dist");
if (fs.existsSync(distDir)) {
  app.use(express.static(distDir));
  app.get("*", (req, res) => {
    if (!req.path.startsWith("/api") && !req.path.startsWith("/ws")) {
      res.sendFile(path.join(distDir, "index.html"));
    }
  });
}

// WebSocket server
const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws: WebSocket) => {
  let subscribedReviewId: string | null = null;

  ws.on("message", (data: Buffer) => {
    try {
      const msg = JSON.parse(data.toString()) as {
        type?: string;
        reviewId?: string;
      };

      if (msg.type === "subscribe" && msg.reviewId) {
        subscribedReviewId = msg.reviewId;
        const session = activeSessions.get(msg.reviewId);
        if (session) {
          session.subscribe(ws);
          ws.send(
            JSON.stringify({
              type: "subscribed",
              reviewId: msg.reviewId,
              running: session.running,
            })
          );
        }
      }
    } catch {
      // Ignore malformed messages
    }
  });

  ws.on("close", () => {
    if (subscribedReviewId) {
      const session = activeSessions.get(subscribedReviewId);
      session?.unsubscribe(ws);
    }
  });

  // Heartbeat ping every 30 s
  const heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.ping();
  }, 30_000);

  ws.on("close", () => clearInterval(heartbeat));
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(
    `SwarmForge Desktop server running at http://127.0.0.1:${PORT}`
  );
});
