/**
 * Demo 6: Deno Sandbox Runner
 * ============================
 * This script is executed BY the agent inside Deno with restricted permissions.
 * The agent generates Python-like analysis logic, but this shows how Deno's
 * permission model restricts what the code can do.
 *
 * Run with restricted permissions:
 *   deno run --allow-read=./sample-data --deny-net --deny-env --deny-run sandbox_runner.ts <script>
 *
 * Try to break it:
 *   deno run --allow-read=./sample-data --deny-net --deny-env --deny-run sandbox_runner.ts malicious
 */

const mode = Deno.args[0] || "analyze";

if (mode === "analyze") {
  // Normal analysis — reads the CSV and computes revenue per region
  console.log("📊 Analyzing sales data...\n");

  const data = await Deno.readTextFile("./sample-data/sales_data.csv");
  const lines = data.trim().split("\n");
  const header = lines[0].split(",");

  const regionIdx = header.indexOf("region");
  const qtyIdx = header.indexOf("quantity");
  const priceIdx = header.indexOf("unit_price");

  const revenue: Record<string, number> = {};

  for (const line of lines.slice(1)) {
    const cols = line.split(",");
    const region = cols[regionIdx];
    const qty = parseFloat(cols[qtyIdx]);
    const price = parseFloat(cols[priceIdx]);
    revenue[region] = (revenue[region] || 0) + qty * price;
  }

  console.log("Total Revenue per Region:");
  console.log("─".repeat(30));
  for (const [region, total] of Object.entries(revenue).sort()) {
    console.log(`  ${region.padEnd(8)} $${total.toFixed(2)}`);
  }
  console.log("─".repeat(30));
  const grandTotal = Object.values(revenue).reduce((a, b) => a + b, 0);
  console.log(`  TOTAL    $${grandTotal.toFixed(2)}`);

} else if (mode === "malicious") {
  // Attempt various malicious operations — ALL will be denied by Deno

  console.log("🔴 Attempting malicious operations...\n");

  // Attempt 1: Read sensitive file
  console.log("1️⃣  Attempting to read /etc/passwd...");
  try {
    const passwd = await Deno.readTextFile("/etc/passwd");
    console.log(`   ✅ SUCCESS (this shouldn't happen!): ${passwd.slice(0, 100)}`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  // Attempt 2: Read SSH keys
  console.log("2️⃣  Attempting to read ~/.ssh/id_rsa...");
  try {
    const home = Deno.env.get("HOME") || "/home";
    const key = await Deno.readTextFile(`${home}/.ssh/id_rsa`);
    console.log(`   ✅ SUCCESS (this shouldn't happen!): ${key.slice(0, 100)}`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  // Attempt 3: Read environment variables
  console.log("3️⃣  Attempting to read environment variables...");
  try {
    const apiKey = Deno.env.get("AZURE_OPENAI_API_KEY");
    console.log(`   ✅ SUCCESS (this shouldn't happen!): ${apiKey}`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  // Attempt 4: Network access
  console.log("4️⃣  Attempting network request to google.com...");
  try {
    const resp = await fetch("https://google.com");
    console.log(`   ✅ SUCCESS (this shouldn't happen!): ${resp.status}`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  // Attempt 5: Execute subprocess
  console.log("5️⃣  Attempting to spawn subprocess (curl)...");
  try {
    const cmd = new Deno.Command("curl", { args: ["https://evil.com"] });
    const output = await cmd.output();
    console.log(`   ✅ SUCCESS (this shouldn't happen!)`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  // Attempt 6: Write to filesystem outside sandbox
  console.log("6️⃣  Attempting to write to /tmp/exfiltrated.txt...");
  try {
    await Deno.writeTextFile("/tmp/exfiltrated.txt", "stolen data");
    console.log(`   ✅ SUCCESS (this shouldn't happen!)`);
  } catch (e) {
    console.log(`   ❌ BLOCKED: ${e.message}\n`);
  }

  console.log("\n✅ All malicious operations were BLOCKED by Deno's permission system.");
  console.log("   The agent can ONLY read from ./sample-data/ — nothing else.");

} else {
  console.log(`Unknown mode: ${mode}. Use "analyze" or "malicious".`);
}
