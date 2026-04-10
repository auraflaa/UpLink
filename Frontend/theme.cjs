const fs = require('fs');
const path = require('path');

function walkDir(dir, callback) {
    fs.readdirSync(dir).forEach(f => {
        let dirPath = path.join(dir, f);
        let isDirectory = fs.statSync(dirPath).isDirectory();
        isDirectory ? 
            walkDir(dirPath, callback) : callback(path.join(dir, f));
    });
}

function processFile(filePath) {
    if (!filePath.endsWith('.tsx') && !filePath.endsWith('.ts')) return;
    
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Replace standard colors with neutral
    let modified = content.replace(/\b(purple|blue|emerald|amber|red|green|yellow|indigo|pink|teal|cyan|rose|fuchsia|violet|sky|lime|orange)(-)(50|100|200|300|400|500|600|700|800|900|950)\b/g, 'neutral$2$3');
    
    if (content !== modified) {
        fs.writeFileSync(filePath, modified, 'utf8');
        console.log(`Replaced colors in ${filePath}`);
    }
}

// walk src dir
walkDir(path.join(__dirname, 'src'), processFile);
console.log("Done.");
