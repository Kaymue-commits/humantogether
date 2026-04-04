// Test if \u000d and \u000a work in JS string literals embedded in HTML

// Test 1: The old broken way (CR encoded as \r in JSON)
const brokenJson = '{"description": "line1\\r\\nline2"}';
const brokenHtml = '<script>var x = ' + brokenJson + ';</script>';
console.log('=== Test 1 (old broken - escaped CR): ===');
console.log('HTML contains backslash-r:', brokenHtml.includes('\\r'));
try {
    const match = brokenHtml.match(/<script>(.*?)<\/script>/s);
    eval(match[1]);
    console.log('Result: OK - parsed successfully');
    console.log('x.description:', JSON.stringify(x.description));
} catch(e) {
    console.log('Result: ERROR -', e.message);
}

// Test 2: The fixed way (CR encoded as \u000d in JSON)
const fixedJson = '{"description": "line1\\u000d\\u000aline2"}';
const fixedHtml = '<script>var x = ' + fixedJson + ';</script>';
console.log('\n=== Test 2 (fixed - Unicode CR): ===');
console.log('HTML contains \\u000d:', fixedHtml.includes('\\u000d'));
try {
    const match = fixedHtml.match(/<script>(.*?)<\/script>/s);
    eval(match[1]);
    console.log('Result: OK - parsed successfully');
    console.log('x.description:', JSON.stringify(x.description));
    console.log('Has CR:', x.description.includes('\r'));
    console.log('Has LF:', x.description.includes('\n'));
} catch(e) {
    console.log('Result: ERROR -', e.message);
}
