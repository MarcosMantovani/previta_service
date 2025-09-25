// /evolution/patches/baileys-wrap-loader.mjs
// Intercepta "baileys" e injeta logs + flags SEMPRE que makeWASocket for chamado.
// Além do console.log, grava JSONL em /tmp/baileys-wrap.calls.log
export async function resolve(specifier, context, nextResolve) {
    if (specifier === 'baileys') {
        const r = await nextResolve(specifier, context);

        const AUTO = String(process.env.BAILEYS_ENABLE_AUTO_SESSION_RECREATION ?? 'true');
        const CACHE = String(process.env.BAILEYS_ENABLE_RECENT_MESSAGE_CACHE ?? 'true');

        const source = `
        import * as orig from ${JSON.stringify(r.url)};
        import { appendFileSync } from 'node:fs';
  
        const AUTO  = ${JSON.stringify(AUTO)} === 'true';
        const CACHE = ${JSON.stringify(CACHE)} === 'true';
  
        const LOG_FILE = '/tmp/baileys-wrap.calls.log';
  
        const _safeAppend = (obj) => {
          try {
            appendFileSync(LOG_FILE, JSON.stringify(obj) + '\\n');
          } catch {}
        };
  
        const _wrapMake = (fn) => function patchedMakeWASocket(cfg = {}) {
          const merged = {
            enableAutoSessionRecreation: (cfg.enableAutoSessionRecreation ?? AUTO),
            enableRecentMessageCache:    (cfg.enableRecentMessageCache    ?? CACHE),
            ...cfg,
          };
  
          const record = {
            at: new Date().toISOString(),
            input: {
              enableAutoSessionRecreation: cfg?.enableAutoSessionRecreation,
              enableRecentMessageCache:    cfg?.enableRecentMessageCache,
            },
            merged: {
              enableAutoSessionRecreation: merged.enableAutoSessionRecreation,
              enableRecentMessageCache:    merged.enableRecentMessageCache,
            }
          };
  
          // log no stdout
          try {
            console.log('[baileys-wrap-loader]', record.at, 'flags input=', record.input, 'merged=', record.merged);
          } catch {}
          // e também arquivo
          _safeAppend(record);
  
          return fn.call(this, merged);
        };
  
        // Build default mantendo tudo e trocando makeWASocket se existir
        const _default = (orig?.default && typeof orig.default === 'object')
          ? { ...orig.default, ...(orig.default.makeWASocket ? { makeWASocket: _wrapMake(orig.default.makeWASocket) } : {}) }
          : orig;
  
        // Reexports
        export * from ${JSON.stringify(r.url)};
        export const makeWASocket = (orig.makeWASocket ? _wrapMake(orig.makeWASocket) : undefined);
        export default _default;
      `;

        const dataUrl = 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
        return { url: dataUrl, shortCircuit: true };
    }
    return nextResolve(specifier, context);
}

export async function load(url, context, nextLoad) {
    return nextLoad(url, context);
}
