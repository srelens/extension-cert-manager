import assert from 'node:assert/strict';
import { generateKeyPairSync, createHash, createPublicKey, verify } from 'node:crypto';
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

function run(key, expected) {
  const root = mkdtempSync(join(tmpdir(), 'cert-manager-sign-'));
  try {
    mkdirSync(join(root, 'scripts')); mkdirSync(join(root, 'dist'));
    copyFileSync(new URL('../scripts/sign.mjs', import.meta.url), join(root, 'scripts/sign.mjs'));
    writeFileSync(join(root, 'signing-public.pem'), expected.publicKey.export({type:'spki',format:'pem'}));
    writeFileSync(join(root, 'dist/manifest.json'), '{"id":"org.srelens.cert-manager","version":"0.1.0"}\n');
    const env = {...process.env};
    delete env.APP_SIGNING_PRIVATE_KEY;
    if (key) env.APP_SIGNING_PRIVATE_KEY = key.privateKey.export({type:'pkcs8',format:'pem'});
    const result = spawnSync(process.execPath, ['scripts/sign.mjs'], {cwd:root, env, encoding:'utf8'});
    if (result.status === 0) {
      const signature = JSON.parse(readFileSync(join(root,'dist/manifest.json.sig'),'utf8'));
      const publicDer = expected.publicKey.export({type:'spki',format:'der'});
      assert.equal(signature.keyid, createHash('sha256').update(publicDer.subarray(-32)).digest('hex'));
      assert.equal(verify(null, readFileSync(join(root,'dist/manifest.json')), expected.publicKey, Buffer.from(signature.sig,'base64')), true);
      assert.equal(verify(null, Buffer.from('modified manifest'), expected.publicKey, Buffer.from(signature.sig,'base64')), false);
    }
    return result;
  } finally { rmSync(root, {recursive:true,force:true}); }
}

test('signs exact bytes with a key-ID-bearing publisher signature', () => {
  const key=generateKeyPairSync('ed25519');
  assert.equal(run(key,key).status,0);
});
test('refuses an absent or mismatched signing key', () => {
  const key=generateKeyPairSync('ed25519');
  assert.notEqual(run(null,key).status,0);
  assert.notEqual(run(generateKeyPairSync('ed25519'),key).status,0);
});

