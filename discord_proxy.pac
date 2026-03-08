// PAC file: route only Discord traffic through mitmproxy
// Use this so only Discord goes through the proxy, not all web traffic.
// macOS: System Settings > Network > Wi-Fi > Details > Proxies > "Automatic Proxy Configuration"
//        URL: file:///path/to/discord_proxy.pac
function FindProxyForURL(url, host) {
  if (host === "gateway.discord.gg" || host === "discord.com" ||
      host.indexOf(".discord.") >= 0 || host.indexOf("discord.gg") >= 0) {
    return "PROXY 127.0.0.1:8082";
  }
  return "DIRECT";
}
