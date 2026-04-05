const fs = require('fs');
const path = require('path');

const filesToFix = [
  'apps/agent-console/app/api/conversations/route.ts',
  'apps/agent-console/app/api/tags/route.ts',
  'apps/agent-console/app/api/risk-flags/route.ts',
  'apps/agent-console/app/api/audit-logs/route.ts',
  'apps/agent-console/app/api/analytics/summaries/route.ts',
  'apps/agent-console/app/api/follow-up/tasks/route.ts',
];

const listApiFiles = [
  'apps/agent-console/app/api/conversations/route.ts',
  'apps/agent-console/app/api/tags/route.ts',
  'apps/agent-console/app/api/risk-flags/route.ts',
  'apps/agent-console/app/api/audit-logs/route.ts',
  'apps/agent-console/app/api/follow-up/tasks/route.ts',
];

const baseDir = '/home/kkk/Project/platform-sim/reference/omni-csx-v35';

filesToFix.forEach(file => {
  const filePath = path.join(baseDir, file);
  let content = fs.readFileSync(filePath, 'utf8');
  
  content = content.replace(/http:\/\/100\.92\.134\.46:8001/g, 'http://localhost:8001');
  
  fs.writeFileSync(filePath, content);
  console.log(`Fixed URL in: ${file}`);
});

listApiFiles.forEach(file => {
  const filePath = path.join(baseDir, file);
  let content = fs.readFileSync(filePath, 'utf8');
  
  if (content.includes('return NextResponse.json(data)') {
    const newListContent = content.replace(
      /const data = await response\.json\(\);\s+return NextResponse\.json\(data\);/g,
      `const data = await response.json();
    if (data && data.data && data.data.items) {
      return NextResponse.json(data.data.items, { status: response.status });
    }
    return NextResponse.json(data, { status: response.status });`
    );
    
    fs.writeFileSync(filePath, newListContent);
    console.log(`Fixed data extraction in: ${file}`);
  }
});

console.log('Done!');
