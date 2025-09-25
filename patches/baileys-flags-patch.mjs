// /evolution/patches/baileys-flags-patch.mjs
(async () => {
    try {
        const mod = await import('baileys');
        const api =
            (mod && typeof mod.makeWASocket === 'function') ? mod :
                (mod?.default && typeof mod.default.makeWASocket === 'function') ? mod.default :
                    null;

        if (!api) {
            console.warn('[baileys-flags-patch.mjs] makeWASocket não encontrado; nada a fazer.');
            return;
        }

        const AUTO = String(process.env.BAILEYS_ENABLE_AUTO_SESSION_RECREATION ?? 'true') === 'true';
        const CACHE = String(process.env.BAILEYS_ENABLE_RECENT_MESSAGE_CACHE ?? 'true') === 'true';

        const original = api.makeWASocket;
        api.makeWASocket = function patchedMakeWASocket(cfg = {}) {
            const merged = {
                enableAutoSessionRecreation: (cfg.enableAutoSessionRecreation ?? AUTO),
                enableRecentMessageCache: (cfg.enableRecentMessageCache ?? CACHE),
                ...cfg,
            };
            return original.call(this, merged);
        };

        console.log('[baileys-flags-patch.mjs] Aplicado: enableAutoSessionRecreation=%s, enableRecentMessageCache=%s', AUTO, CACHE);
    } catch (e) {
        console.warn('[baileys-flags-patch.mjs] Falha ao aplicar:', e?.message ?? e);
    }
})();
