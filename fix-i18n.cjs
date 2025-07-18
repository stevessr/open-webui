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

// Function to fix i18n usage in a file
function fixI18nUsage(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  
  // Check if file uses i18n
  if (content.includes('$i18n.t(') || content.includes('getContext(\'i18n\')')) {
    console.log(`Fixing ${filePath}`);
    
    // Replace getContext('i18n') with getI18n() import
    if (content.includes('getContext(\'i18n\')')) {
      // Add import if not present
      if (!content.includes('import { getI18n }')) {
        const scriptMatch = content.match(/<script[^>]*>/);
        if (scriptMatch) {
          const importLine = '\timport { getI18n } from \'$lib/i18n/helpers\';\n';
          const insertPos = scriptMatch.index + scriptMatch[0].length;
          
          // Check if there are already imports
          const existingImports = content.slice(insertPos).match(/^\s*import[^;]+;/gm);
          if (existingImports) {
            // Add after last import
            const lastImportMatch = content.slice(insertPos).match(/^(\s*import[^;]+;)\s*$/gm);
            if (lastImportMatch) {
              const lastImport = lastImportMatch[lastImportMatch.length - 1];
              const lastImportPos = content.indexOf(lastImport, insertPos) + lastImport.length;
              content = content.slice(0, lastImportPos) + '\n' + importLine + content.slice(lastImportPos);
            } else {
              content = content.slice(0, insertPos) + '\n' + importLine + content.slice(insertPos);
            }
          } else {
            content = content.slice(0, insertPos) + '\n' + importLine + content.slice(insertPos);
          }
          modified = true;
        }
      }
      
      // Replace getContext usage
      content = content.replace(/const\s+i18n\s*=\s*getContext\(['"]i18n['"]\);?/g, 'const i18n = getI18n();');
      content = content.replace(/import\s*{\s*getContext\s*}\s*from\s*['"]svelte['"];?\s*\n\s*const\s+i18n\s*=\s*getContext\(['"]i18n['"]\);?/g, '');
      
      // Remove getContext import if it's only used for i18n
      const getContextUsages = (content.match(/getContext/g) || []).length;
      if (getContextUsages === 0) {
        content = content.replace(/,\s*getContext/g, '');
        content = content.replace(/getContext,\s*/g, '');
        content = content.replace(/import\s*{\s*getContext\s*}\s*from\s*['"]svelte['"];?\s*/g, '');
      }
      
      modified = true;
    }
    
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
    fixI18nUsage(file);
  } catch (error) {
    console.error(`Error processing ${file}:`, error.message);
  }
}

console.log('Done!');
