// /evolution/patches/fix-baileys-esm-wa.mjs
import fs from 'node:fs';
import path from 'node:path';

const ROOT = '/evolution/node_modules/baileys';
const WA_DIR = path.join(ROOT, 'WAProto');

if (!fs.existsSync(ROOT)) {
    console.error('[fix-baileys-esm-wa] baileys não encontrado em', ROOT);
    process.exit(0);
}

let targetFile = null;
for (const cand of ['WAProto.js', 'index.js']) {
    const p = path.join(WA_DIR, cand);
    if (fs.existsSync(p)) { targetFile = cand; break; }
}

if (!targetFile) {
    console.warn('[fix-baileys-esm-wa] Não achei WAProto.js nem index.js em', WA_DIR, '— nada a fazer.');
    process.exit(0);
}

const ABS_SPEC = `baileys/WAProto/${targetFile}`;
const REL_SPEC = `../WAProto/${targetFile}`;
const REL2_SPEC = `../../WAProto/${targetFile}`;
const REL3_SPEC = `../../../WAProto/${targetFile}`;

// Arquivos alvo conhecidos + varredura geral em lib/
const candidates = new Set([
    path.join(ROOT, 'lib/Utils/message-retry-manager.js'),
    path.join(ROOT, 'lib/Utils/message-retry-manager.mjs'),
]);

// incluir todo o lib para garantir (sem .map)
const libDir = path.join(ROOT, 'lib');
if (fs.existsSync(libDir)) {
    const walk = dir => {
        for (const f of fs.readdirSync(dir)) {
            const p = path.join(dir, f);
            const st = fs.statSync(p);
            if (st.isDirectory()) walk(p);
            else if ((p.endsWith('.js') || p.endsWith('.mjs')) && !p.endsWith('.map')) candidates.add(p);
        }
    };
    walk(libDir);
}

let patched = 0;
for (const file of candidates) {
    if (!fs.existsSync(file)) continue;
    let s = fs.readFileSync(file, 'utf8');
    const before = s;

    // substitui import ABS (ex.: from "baileys/WAProto")
    s = s.replace(/from\s+['"]baileys\/WAProto['"]/g, `from '${ABS_SPEC}'`);

    // substitui import relativos (../WAProto, ../../WAProto, …)
    s = s.replace(/from\s+['"]\.\.\/WAProto['"]/g, `from '${REL_SPEC}'`);
    s = s.replace(/from\s+['"]\.\.\/\.\.\/WAProto['"]/g, `from '${REL2_SPEC}'`);
    s = s.replace(/from\s+['"]\.\.\/\.\.\/\.\.\/WAProto['"]/g, `from '${REL3_SPEC}'`);

    if (s !== before) {
        fs.writeFileSync(file, s, 'utf8');
        patched++;
        console.log('[fix-baileys-esm-wa] patched:', file);
    }
}

console.log(`[fix-baileys-esm-wa] Done. Files patched: ${patched}. Target: ${targetFile}`);
