#!/usr/bin/env node
/**
 * NexusGenesis Agent Demo
 *
 * A self-contained example that demonstrates post-quantum (PQC) agent identity
 * with self-custody keys, signature verification, and optional LLM verification.
 *
 * Private keys NEVER leave the caller — the core NexusGenesis security principle.
 *
 * Run: npm install && node main.js
 *   or: OPENAI_API_KEY=sk-... node main.js  (for LLM verification step)
 *
 * Config priority: real environment variables first, then optional .env file
 * (dotenv never overrides variables that are already set in the environment).
 */

import 'dotenv/config';
import { PQCWallet } from 'nexusgenesis-agent-keys';

async function main() {
  console.log('');
  console.log('\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557');
  console.log('\u2551     NexusGenesis \u2014 Agent Identity Demo                  \u2551');
  console.log('\u2551     PQC Self-Custody Keys + Human Takeover              \u2551');
  console.log('\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d');
  console.log('');

  // Step 1: Generate PQC agent identity
  console.log('\u25b8 [1/4] Generating PQC agent identity...');
  console.log('  Algorithm: CRYSTALS-Dilithium2 (NIST FIPS 204)');
  const wallet = await PQCWallet.generate();
  console.log('  Address:     ' + wallet.address);
  console.log('  Public Key:  ' + wallet.publicKey.toString('hex').substring(0, 48) + '...');
  console.log('  \u2713 Private key generated \u2014 never leaves this process');
  console.log('');

  // Step 2: Sign a message
  console.log('\u25b8 [2/4] Signing a message with the agent private key...');
  const message = JSON.stringify({
    action: 'claim_task',
    taskId: 'demo-001',
    agent: wallet.address,
    timestamp: Date.now()
  });
  const signature = await wallet.sign(message);
  console.log('  Message:  ' + JSON.stringify(JSON.parse(message), null, 2));
  console.log('  Signature: ' + signature.substring(0, 64) + '...');
  console.log('');

  // Step 3: Verify locally
  console.log('\u25b8 [3/4] Verifying signature (local, no server needed)...');
  const isValid = await wallet.verify(message, signature);
  console.log('  Result: ' + (isValid ? '\u2713 SIGNATURE VALID' : '\u2717 SIGNATURE INVALID'));
  console.log('  This verification is done entirely locally \u2014 no network call.');
  console.log('');

  // Step 4 (optional): LLM verification
  const openaiKey = process.env.OPENAI_API_KEY;
  if (openaiKey) {
    console.log('\u25b8 [4/4] Asking LLM to verify the agent identity...');
    try {
      const { default: OpenAI } = await import('openai');
      const openai = new OpenAI({ apiKey: openaiKey });
      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: 'You are a blockchain security auditor. Verify agent identities and signatures.'
          },
          {
            role: 'user',
            content: [
              'Verify this NexusGenesis agent identity:',
              '',
              'Agent Address: ' + wallet.address,
              'Public Key (hex): ' + wallet.publicKey.toString('hex'),
              'Signed Message: ' + message,
              'Signature: ' + signature,
              '',
              'Questions:',
              '1. Is this a valid post-quantum signature?',
              '2. What does "self-custody" mean for agent security?',
              '3. Why is human takeover important for autonomous agents?'
            ].join('\n')
          }
        ]
      });
      console.log('  LLM response: ' + response.choices[0].message.content);
    } catch (err) {
      console.log('  \u26a0 LLM call failed: ' + err.message);
    }
  } else {
    console.log('\u25b8 [4/4] LLM verification \u2014 skipped');
    console.log('  Set OPENAI_API_KEY to enable this step.');
    console.log('  Example: OPENAI_API_KEY=sk-... node main.js');
  }
  console.log('');

  // Summary
  console.log('\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557');
  console.log('\u2551     Demo Complete                                       \u2551');
  console.log('\u2551                                                         \u2551');
  console.log('\u2551  Keys are self-custodied (never leave the caller).      \u2551');
  console.log('\u2551  Human can always take control back.                    \u2551');
  console.log('\u2551                                                         \u2551');
  console.log('\u2551  Learn more: https://github.com/nexus-genesis/nexusgenesis \u2551');
  console.log('\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d');
  console.log('');
}

main().catch(err => {
  console.error('Demo failed:', err);
  process.exit(1);
});
