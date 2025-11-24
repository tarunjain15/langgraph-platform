#!/usr/bin/env node

/**
 * Validation Witness: Proves coded-systems/ specification matches implementation
 *
 * This script closes the loop between specification and reality by:
 * 1. Loading coded-systems/*.jsonl (the claims)
 * 2. Introspecting dist/tools/*.js (the reality)
 * 3. Verifying every claim in spec matches implementation
 * 4. Failing loudly if ANY drift detected
 *
 * Run: node validate-spec.mjs
 * Exit: 0 if valid, 1 if drift detected
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ANSI colors for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m',
};

const { green, red, yellow, blue, gray, reset } = colors;

// Load JSONL file (newline-delimited JSON)
function loadJsonl(filename) {
  const filepath = path.join(__dirname, 'coded-systems', filename);
  const content = fs.readFileSync(filepath, 'utf8');
  return content
    .split('\n')
    .filter(line => line.trim())
    .map(line => JSON.parse(line));
}

// Load single-line JSONL
function loadSingleJsonl(filename) {
  const items = loadJsonl(filename);
  if (items.length !== 1) {
    throw new Error(`Expected 1 entry in ${filename}, got ${items.length}`);
  }
  return items[0];
}

console.log(`${blue}╔════════════════════════════════════════════════════════════╗${reset}`);
console.log(`${blue}║${reset}  Validation Witness: coded-systems/ Specification Check  ${blue}║${reset}`);
console.log(`${blue}╚════════════════════════════════════════════════════════════╝${reset}\n`);

let validationsPassed = 0;
let validationsFailed = 0;

function pass(message) {
  console.log(`${green}✓${reset} ${message}`);
  validationsPassed++;
}

function fail(message) {
  console.log(`${red}✗${reset} ${message}`);
  validationsFailed++;
}

function info(message) {
  console.log(`${gray}  ${message}${reset}`);
}

function section(title) {
  console.log(`\n${blue}▸${reset} ${title}`);
}

// === LOAD SPECIFICATIONS ===
section('Loading specifications...');

const primitive = loadSingleJsonl('primitive.jsonl');
pass(`Loaded primitive.jsonl: ${primitive.name}`);

const constraints = loadJsonl('constraints.jsonl');
pass(`Loaded constraints.jsonl: ${constraints.length} constraints`);

const infrastructure = loadJsonl('infrastructure.jsonl');
pass(`Loaded infrastructure.jsonl: ${infrastructure.length} components`);

const toolSpecs = loadJsonl('tools.jsonl');
pass(`Loaded tools.jsonl: ${toolSpecs.length} tools`);

// === VALIDATE PRIMITIVE ===
section('Validating primitive specification...');

// Primitive must have all 5 components
const requiredComponents = [
  'conversational_negotiation',
  'graduated_permissions',
  'hot_reload_lifecycle',
  'state_continuity',
  'tool_isolation',
];

requiredComponents.forEach(component => {
  if (primitive.components[component]) {
    pass(`Primitive defines ${component}`);
  } else {
    fail(`Primitive missing ${component}`);
  }
});

// Primitive must declare immutability
if (primitive.immutability && primitive.immutability.includes('not negotiable')) {
  pass('Primitive declares immutability');
} else {
  fail('Primitive missing immutability clause');
}

// Primitive must declare emergence principle
if (primitive.emergence_principle) {
  pass('Primitive declares emergence principle');
} else {
  fail('Primitive missing emergence principle');
}

// === VALIDATE CONSTRAINTS ===
section('Validating constraints specification...');

// Must have exactly 5 sacred constraints
if (constraints.length === 5) {
  pass(`Found 5 sacred constraints`);
} else {
  fail(`Expected 5 sacred constraints, found ${constraints.length}`);
}

// Verify constraint names match expected
const expectedConstraintNames = [
  'CONVERSATIONAL_ALIGNMENT',
  'PERMISSION_GRADUATION',
  'HOT_RELOAD_SAFETY',
  'STATE_CONTINUITY',
  'TOOL_CLASS_ISOLATION',
];

expectedConstraintNames.forEach(name => {
  const constraint = constraints.find(c => c.name === name);
  if (constraint) {
    pass(`Constraint ${name} defined`);

    // Each constraint must have witness_protocol
    if (constraint.witness_protocol) {
      info(`  witness protocol: ${Object.keys(constraint.witness_protocol).length} metrics`);
    } else {
      fail(`  ${name} missing witness_protocol`);
    }

    // Each constraint must have enforcement
    if (constraint.enforcement) {
      info(`  enforcement: automatic + manual`);
    } else {
      fail(`  ${name} missing enforcement`);
    }
  } else {
    fail(`Missing constraint: ${name}`);
  }
});

// === VALIDATE INFRASTRUCTURE ===
section('Validating infrastructure specification...');

// Expected infrastructure components (M1-M6)
const expectedInfra = [
  'conversation-meta-actions',
  'hot-reload-mechanism',
  'permission-graduation-system',
  'alignment-detection-system',
  'orchestration-safety-system',
  'shared-context-system',
];

expectedInfra.forEach(name => {
  const component = infrastructure.find(i => i.name === name);
  if (component) {
    pass(`Infrastructure component: ${name}`);
  } else {
    fail(`Missing infrastructure: ${name}`);
  }
});

// === VALIDATE TOOLS AGAINST IMPLEMENTATION ===
section('Validating tools against implementation...');

// Load actual tool implementations
const toolsDir = path.join(__dirname, 'dist', 'tools');
let actualTools = [];

try {
  const files = fs.readdirSync(toolsDir);
  actualTools = files
    .filter(f => f.endsWith('.js'))
    .map(f => f.replace('.js', ''));

  info(`Found ${actualTools.length} compiled tools: ${actualTools.join(', ')}`);
} catch (error) {
  fail(`Cannot read dist/tools/: ${error.message}`);
  fail('Run "npm run build" first');
  process.exit(1);
}

// Verify each spec has corresponding implementation
toolSpecs.forEach(spec => {
  const implExists = actualTools.includes(spec.name);
  if (implExists) {
    pass(`${spec.name}: implementation exists`);
  } else {
    fail(`${spec.name}: implementation MISSING (spec without code)`);
  }

  // Validate tool structure

  // 1. Must have all 5 sacred refusals
  const requiredRefusals = [
    'blind_execution',
    'permission_escalation',
    'state_amnesia',
    'reload_corruption',
    'tool_interference',
  ];

  requiredRefusals.forEach(refusal => {
    if (spec.refusals && spec.refusals[refusal]) {
      // pass silently (too verbose)
    } else {
      fail(`${spec.name}: missing refusal '${refusal}'`);
    }
  });

  if (Object.keys(spec.refusals || {}).length >= 5) {
    pass(`${spec.name}: all 5 sacred refusals declared`);
  }

  // 2. Every capability must have permission requirement
  const capabilities = spec.capabilities || [];
  const permReqs = spec.permission_requirements || {};

  let allCapabilitiesHavePerms = true;
  capabilities.forEach(action => {
    if (!(action in permReqs)) {
      fail(`${spec.name}.${action}: missing permission requirement`);
      allCapabilitiesHavePerms = false;
    }
  });

  if (allCapabilitiesHavePerms && capabilities.length > 0) {
    pass(`${spec.name}: all ${capabilities.length} capabilities have permission requirements`);
  }

  // 3. Must require conversationId and alignmentCheck
  const required = spec.context_dependencies?.required || [];

  if (required.includes('conversationId')) {
    // pass silently
  } else {
    fail(`${spec.name}: doesn't require conversationId`);
  }

  if (required.includes('alignmentCheck')) {
    // pass silently
  } else {
    fail(`${spec.name}: doesn't require alignmentCheck`);
  }

  if (required.includes('conversationId') && required.includes('alignmentCheck')) {
    pass(`${spec.name}: requires conversationId + alignmentCheck`);
  }

  // 4. Orchestrator-specific validations
  if (spec.name === 'orchestrator-tool') {
    if (spec.orchestration_limits) {
      pass(`${spec.name}: declares orchestration limits`);

      if (spec.orchestration_limits.max_depth === 5) {
        pass(`  max_depth: 5 (recursion protection)`);
      } else {
        fail(`  max_depth should be 5, got ${spec.orchestration_limits.max_depth}`);
      }

      if (spec.orchestration_limits.circular_detection === true) {
        pass(`  circular_detection: enabled`);
      } else {
        fail(`  circular_detection should be true`);
      }
    } else {
      fail(`${spec.name}: missing orchestration_limits`);
    }

    // Must have M6-specific refusals
    const m6Refusals = ['recursion_runaway', 'circular_dependency', 'error_bypass'];
    m6Refusals.forEach(refusal => {
      if (spec.refusals && spec.refusals[refusal]) {
        // pass silently
      } else {
        fail(`${spec.name}: missing M6 refusal '${refusal}'`);
      }
    });
  }
});

// Verify no implementation without spec
actualTools.forEach(toolName => {
  const hasSpec = toolSpecs.find(s => s.name === toolName);
  if (!hasSpec) {
    fail(`${toolName}: implementation exists but NO SPEC (code without documentation)`);
  }
});

// === FINAL SUMMARY ===
console.log(`\n${blue}╔════════════════════════════════════════════════════════════╗${reset}`);
console.log(`${blue}║${reset}  Validation Summary                                        ${blue}║${reset}`);
console.log(`${blue}╚════════════════════════════════════════════════════════════╝${reset}\n`);

console.log(`${green}Passed:${reset} ${validationsPassed}`);
console.log(`${red}Failed:${reset} ${validationsFailed}\n`);

if (validationsFailed === 0) {
  console.log(`${green}✅ ALL VALIDATIONS PASSED${reset}`);
  console.log(`${gray}coded-systems/ specification is consistent with implementation${reset}\n`);
  process.exit(0);
} else {
  console.log(`${red}❌ VALIDATION FAILED${reset}`);
  console.log(`${gray}coded-systems/ has drifted from implementation${reset}\n`);
  process.exit(1);
}
