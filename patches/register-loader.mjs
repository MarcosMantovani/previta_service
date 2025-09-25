import { register } from 'node:module';
import { pathToFileURL } from 'node:url';

// registra o seu loader ESM estável
register('/evolution/patches/baileys-wrap-loader.mjs', pathToFileURL(process.cwd() + '/'));
