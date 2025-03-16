const fs = require('fs');
const path = require('path');

// Get inputs from environment variables
const runsOn = process.env.RUNS_ON;
const toolchain = process.env.TOOLCHAIN;
const preset = process.env.PRESET;

// Set up paths
const basePath = `./.github/actions/cmake-builder/${runsOn}`;
const baseActionPath = `${basePath}/base`;
const toolchainActionPath = `${basePath}/toolchains/${toolchain}`;
const presetActionPath = `${basePath}/presets/${preset}`;

// Check which actions exist
function checkActionExists(actionPath) {
  return fs.existsSync(`${actionPath}/action.yml`) ||
         fs.existsSync(`${actionPath}/action.yaml`);
}

const baseActionExists = checkActionExists(baseActionPath);
const toolchainActionExists = checkActionExists(toolchainActionPath);
const presetActionExists = checkActionExists(presetActionPath);

// If no actions exist, exit gracefully
if (!baseActionExists && !toolchainActionExists && !presetActionExists) {
  console.log("No actions found, exiting gracefully");
  process.exit(0);
}

// Create directory for the dynamic action
const selectSetupActionsPath = './.select-setup-actions';
if (!fs.existsSync(selectSetupActionsPath)) {
  fs.mkdirSync(selectSetupActionsPath, { recursive: true });
}

// Generate the action content
let actionContent = `name: Dynamic Setup Action
description: Dynamically generated action

# Input definitions for secrets
inputs:
  secret1:
    description: "Generic secret slot 1"
    required: false
  secret2:
    description: "Generic secret slot 2"
    required: false
  secret3:
    description: "Generic secret slot 3"
    required: false
  secret4:
    description: "Generic secret slot 4"
    required: false

runs:
  using: composite
  steps:`;

// Add steps for each action that exists
if (baseActionExists) {
  console.log("Found BASE action");
  actionContent += `
    - uses: ${baseActionPath}
      with:
        secret1: \${{ inputs.secret1 }}
        secret2: \${{ inputs.secret2 }}
        secret3: \${{ inputs.secret3 }}
        secret4: \${{ inputs.secret4 }}`;
}

if (toolchainActionExists) {
  console.log("Found TOOLCHAIN action");
  actionContent += `
    - uses: ${toolchainActionPath}
      with:
        secret1: \${{ inputs.secret1 }}
        secret2: \${{ inputs.secret2 }}
        secret3: \${{ inputs.secret3 }}
        secret4: \${{ inputs.secret4 }}`;
}

if (presetActionExists) {
  console.log("Found PRESET action");
  actionContent += `
    - uses: ${presetActionPath}
      with:
        secret1: \${{ inputs.secret1 }}
        secret2: \${{ inputs.secret2 }}
        secret3: \${{ inputs.secret3 }}
        secret4: \${{ inputs.secret4 }}`;
}

// Write the generated action file
fs.writeFileSync(`${selectSetupActionsPath}/action.yml`, actionContent);

// Output the content for debugging
console.log("Generated action file content:");
console.log(actionContent);
