import {createHash, createPrivateKey, createPublicKey, sign, verify} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';

if (!process.env.APP_SIGNING_PRIVATE_KEY) throw new Error('APP_SIGNING_PRIVATE_KEY is required; refusing an unsigned release');
const key = createPrivateKey(process.env.APP_SIGNING_PRIVATE_KEY);
if (key.asymmetricKeyType !== 'ed25519') throw new Error('Expected an Ed25519 signing key');
const trusted = createPublicKey(readFileSync(new URL('../signing-public.pem', import.meta.url)));
const publicDer = createPublicKey(key).export({format:'der', type:'spki'});
if (!publicDer.equals(trusted.export({format:'der', type:'spki'}))) throw new Error('Signing key does not match published app key');
const raw = readFileSync('dist/manifest.json');
const signature = sign(null, raw, key);
if (!verify(null, raw, trusted, signature)) throw new Error('Signature verification failed');
writeFileSync('dist/manifest.json.sig', JSON.stringify({
  keyid: createHash('sha256').update(publicDer.subarray(-32)).digest('hex'),
  sig: signature.toString('base64'),
}) + '\n');
console.log('Signed and verified dist/manifest.json');

