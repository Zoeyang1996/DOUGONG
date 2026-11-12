export class Challenge {
  constructor(total=18, duration=120000) { this.total=total; this.duration=duration; this.reset(); }
  reset() { this.status='ready'; this.placed=0; this.deadline=0; this.remaining=this.duration; }
  start(now) { this.status='playing'; this.placed=0; this.deadline=now+this.duration; this.remaining=this.duration; }
  tick(now) { if(this.status==='playing'){this.remaining=Math.max(0,this.deadline-now);if(this.remaining===0)this.status='lost';} return this.status; }
  place(index,now) { this.tick(now); if(this.status!=='playing'||index!==this.placed)return false; this.placed++;if(this.placed===this.total)this.status='won';return true; }
}
