import test from 'node:test';
import assert from 'node:assert/strict';
import { Challenge } from './game-state.mjs';
test('the challenge runs for exactly 120 seconds and rejects late placement',()=>{
 const g=new Challenge();g.start(500);assert.equal(g.remaining,120000);
 assert.equal(g.place(1,501),false);assert.equal(g.place(0,501),true);
 assert.equal(g.place(0,502),false);g.tick(120499);assert.equal(g.status,'playing');
 assert.equal(g.place(1,120500),false);assert.equal(g.status,'lost');assert.equal(g.placed,1);
});
test('all 18 groups complete once, and restart clears the result',()=>{
 const g=new Challenge();g.start(100);
 for(let i=0;i<18;i++)assert.equal(g.place(i,100+i*500),true);
 assert.equal(g.status,'won');assert.equal(g.placed,18);assert.equal(g.place(18,9999),false);
 g.start(200000);assert.equal(g.placed,0);assert.equal(g.remaining,120000);assert.equal(g.status,'playing');
});
test('a delayed update cannot extend the deadline',()=>{
 const g=new Challenge();g.start(0);g.tick(300000);assert.equal(g.status,'lost');assert.equal(g.remaining,0);
});
