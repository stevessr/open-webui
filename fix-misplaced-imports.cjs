#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Function to recursively find all .svelte files
function findSvelteFiles(dir, files = []) {
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      findSvelteFiles(fullPath, files);
    } else if (item.endsWith('.svelte')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// Function to fix misplaced imports in a file
function fixMisplacedImports(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  
  // Look for misplaced import statements (not at the top level)
  const misplacedImportPattern = /^(\s+)import\s+\{[^}]+\}\s+from\s+['"][^'"]+['"];?\s*$/gm;
  
  const matches = [...content.matchAll(misplacedImportPattern)];
  
  if (matches.length > 0) {
    console.log(`Fixing misplaced imports in ${filePath}`);
    
    // Remove all misplaced imports
    for (const match of matches) {
      content = content.replace(match[0], '');
      modified = true;
    }
    
    // Clean up any extra empty lines
    content = content.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    if (modified) {
      fs.writeFileSync(filePath, content);
      console.log(`Fixed ${filePath}`);
    }
  }
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const svelteFiles = findSvelteFiles(srcDir);

console.log(`Found ${svelteFiles.length} Svelte files`);

for (const file of svelteFiles) {
  try {
    fixMisplacedImports(file);
  } catch (error) {
    console.error(`Error processing ${file}:`, error.message);
  }
}

console.log('Done!');
