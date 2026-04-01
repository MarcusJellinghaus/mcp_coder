const fs = require('fs');
const p = process.argv[2];
const d = JSON.parse(fs.readFileSync(p, 'utf8'));
const lines = d.result.split('\n');
let c = 0;
lines.forEach(function(l, i) {
  if (l.indexOf('display_status_table(') >= 0) {
    c++;
    var s = Math.max(0, i - 2);
    var e = Math.min(lines.length, i + 16);
    for (var j = s; j < e; j++) {
      console.log(String(j + 1).padStart(4) + ': ' + lines[j]);
    }
    console.log('---');
  }
});
console.log('TOTAL: ' + c);
