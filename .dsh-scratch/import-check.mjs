const urls = [
  "file:///E:/%E6%96%B0%E5%A2%9E%E8%B3%87%E6%96%99%E5%A4%BE/SBA-work/dsh-github-link/index.js",
  "file:///E:/新增資料夾/SBA-work/dsh-github-link/index.js",
  "E:/新增資料夾/SBA-work/dsh-github-link/index.js",
  "E:\\新增資料夾\\SBA-work\\dsh-github-link\\index.js",
];
for (const u of urls) {
  try {
    const mod = await import(u);
    console.log("OK  ", u, "->", mod.name, "inject:", JSON.stringify(mod.inject), "apply:", typeof mod.apply);
  } catch (e) {
    console.log("FAIL", u, "->", e.message);
  }
}
