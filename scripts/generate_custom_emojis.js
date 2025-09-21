import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const customEmojisDir = path.join(__dirname, '..', 'static', 'assets', 'custom_emojis');

function scanDirectory(dir, baseDir = dir) {
  const files = [];
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      files.push(...scanDirectory(fullPath, baseDir));
    } else if (stat.isFile()) {
      // 只处理图片文件
      if (['.png', '.jpg', '.jpeg', '.svg', '.gif'].includes(path.extname(item).toLowerCase())) {
        const relativePath = path.relative(baseDir, fullPath);
        files.push(relativePath);
      }
    }
  }

  return files;
}

function generateEmojisJSON() {
  const files = scanDirectory(customEmojisDir);
  const emojis = {};

  for (const file of files) {
    const dirName = path.dirname(file).split(path.sep)[0] || 'Custom';
    const fileName = path.basename(file, path.extname(file));

  // 保留中文字符（CJK）、字母、数字和下划线。先把文件名转换为大写，然后替换不允许的字符为下划线，
  // 再把连续的下划线折叠为一个，并去掉首尾的下划线。
  const rawName = `${dirName}_${fileName}`.toUpperCase();
  // 允许 A-Z, 0-9, underscore, 以及 Unicode 中的汉字/日文/韩文范围（\u4E00-\u9FFF, \u3040-\u30FF, \uAC00-\uD7AF）
  const sanitized = rawName.replace(/[^A-Z0-9_\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]/g, '_')
                .replace(/_+/g, '_')
                .replace(/^_+|_+$/g, '');
  const name = sanitized;
    const shortcode = `/assets/custom_emojis/${file.replace(/\\/g, '/')}`;
    const group = dirName.charAt(0).toUpperCase() + dirName.slice(1);

    emojis[name] = {
      shortcode,
      group
    };
  }

  return {
    emojis
  };
}

// 生成并输出 JSON
const json = generateEmojisJSON();
//console.log(JSON.stringify(json, null, 2));

// 写入文件
fs.writeFileSync(path.join(__dirname, '..', 'src', 'lib', 'custom-emojis.json'), JSON.stringify(json, null, 2));