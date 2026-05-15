const crypto = require('crypto');

function base64urlEncode(buffer) {
  return buffer.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function generateCodeVerifier() {
  return base64urlEncode(crypto.randomBytes(32));
}

function generateCodeChallenge(codeVerifier) {
  const hash = crypto.createHash('sha256').update(codeVerifier).digest();
  return base64urlEncode(hash);
}

const codeVerifier = generateCodeVerifier();
const codeChallenge = generateCodeChallenge(codeVerifier);

console.log('code_verifier:', codeVerifier);
console.log('code_challenge:', codeChallenge);

// https://sso.mf.uz/oauth2/login?clientId=imv-trip&redirectUri=http://localhost:3000/login&codeChallenge=sXIZyOuOz6GbaPV63GQeAydeL5kpypGVPa-bKiCcFNA
