const builder = require("electron-builder");

builder.build({
  config: {
    appId: "com.swarmforge.desktop",
    productName: "SwarmForge",
    directories: {
      output: "release",
    },
    files: [
      "dist/**/*",
      "server/**/*",
      "electron/**/*",
      "node_modules/**/*",
      "data/**/*",
      "package.json",
    ],
    mac: {
      target: ["dmg"],
      category: "public.app-category.developer-tools",
      icon: "assets/icon.icns",
    },
    dmg: {
      title: "SwarmForge",
    },
    asar: false, // Keep unpacked for tsx/native modules
  },
}).then(() => {
  console.log("Build complete");
}).catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
