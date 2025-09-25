#!/bin/sh
set -e
cd /evolution

echo "Procurando arquivos alvo..."
TARGETS=$(find /evolution/dist/api/integrations/channel/whatsapp \
  -type f \( -name 'whatsapp.baileys.service.*.js' -o -name 'whatsapp.baileys.service.*.mjs' \) \
  -not -name '*.map' 2>/dev/null || true)

# fallback: tentar no main.(js|mjs) também
MAIN=$(find /evolution/dist -maxdepth 1 -type f \( -name 'main.js' -o -name 'main.mjs' \) -not -name '*.map' 2>/dev/null || true)
[ -n "$MAIN" ] && TARGETS="$TARGETS
$MAIN"

echo "Arquivos alvo:"
echo "$TARGETS" | sed 's/^/ - /'

AUTO_FLAG="${BAILEYS_ENABLE_AUTO_SESSION_RECREATION:-true}"
CACHE_FLAG="${BAILEYS_ENABLE_RECENT_MESSAGE_CACHE:-true}"

patch_one() {
  FILE="$1"
  [ -f "$FILE" ] || return 0
  echo "Patching: $FILE"

  node -e '
    const fs = require("fs");
    const path = process.argv[1];
    const AUTO  = (process.env.BAILEYS_ENABLE_AUTO_SESSION_RECREATION || "true") === "true";
    const CACHE = (process.env.BAILEYS_ENABLE_RECENT_MESSAGE_CACHE    || "true") === "true";
    let s = fs.readFileSync(path, "utf8");
    let changed = false;

    // 1) socketConfig = { ... }
    const reCfg = /(const|let|var)\s+socketConfig\s*=\s*\{([\s\S]*?)\}\s*([,;])/m;
    let m = s.match(reCfg);
    if (m) {
      let body = m[2];
      if (!/enableAutoSessionRecreation\s*:/.test(body)) {
        body = "\\n  enableAutoSessionRecreation: " + AUTO + ",\\n" + body;
        changed = true;
      }
      if (!/enableRecentMessageCache\s*:/.test(body)) {
        body = "\\n  enableRecentMessageCache: " + CACHE + ",\\n" + body;
        changed = true;
      }
      if (changed) {
        const replaced = m[0].replace(m[2], body);
        s = s.slice(0, m.index) + replaced + s.slice(m.index + m[0].length);
      }
    } else {
      // 2) fallback: makeWASocket({ ... })
      const reSocket = /makeWASocket\(\s*\{([\s\S]*?)\}\s*\)/m;
      const ms = s.match(reSocket);
      if (ms) {
        let body = ms[1];
        if (!/enableAutoSessionRecreation\s*:/.test(body)) {
          body = "\\n  enableAutoSessionRecreation: " + AUTO + ",\\n" + body;
          changed = true;
        }
        if (!/enableRecentMessageCache\s*:/.test(body)) {
          body = "\\n  enableRecentMessageCache: " + CACHE + ",\\n" + body;
          changed = true;
        }
        if (changed) {
          const replaced = ms[0].replace(ms[1], body);
          s = s.slice(0, ms.index) + replaced + s.slice(ms.index + ms[0].length);
        }
      } else {
        console.warn("[patch] Nem socketConfig nem makeWASocket({}) encontrados:", path);
      }
    }

    if (changed) {
      fs.writeFileSync(path, s, "utf8");
      console.log("  ✓ patched", path);
    } else {
      console.log("  (sem mudanças)", path);
    }
  ' "$FILE"
}

# aplicar
if [ -n "$TARGETS" ]; then
  echo "$TARGETS" | while IFS= read -r f; do
    [ -n "$f" ] && patch_one "$f"
  done
else
  echo "Nenhum arquivo alvo encontrado para patch."
fi

# iniciar Evolution normalmente
exec /bin/bash -c ". ./Docker/scripts/deploy_database.sh && npm run start:prod"
