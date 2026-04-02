# knurl-persona

Override your Claude Code companion's personality with a single text file.

Claude Code ships with a companion creature (the little owl next to your input box) whose personality is controlled server-side. **knurl-persona** intercepts the API call via a local proxy and swaps in your custom persona — no patching, no forks.

## How it works

```
Claude Code  ──HTTPS_PROXY──▶  mitmdump  ──▶  Anthropic API
                                  │
                          reads persona.txt
                          swaps personality field
```

The companion's `buddy_react` API sends a `personality` field with each request. knurl-persona intercepts this and replaces it with whatever you write in a text file (max 200 characters, enforced by the API).

## Quick start

```bash
# Install dependency
brew install mitmproxy

# Clone
git clone https://github.com/YOUR_USERNAME/knurl-persona.git
cd knurl-persona

# Edit persona.txt (or pick a preset)
cp personas/catgirl-zh.txt persona.txt

# Launch — starts proxy and claude in one command
chmod +x knurl-persona
./knurl-persona
```

## Usage

```
knurl-persona [options] [-- claude-args...]

Options:
  -p, --persona FILE   Path to persona file (default: persona.txt)
  -n, --name NAME      Override companion name
  -v, --verbose        Print interception logs
  -P, --port PORT      Proxy port (default: 18888)
  --proxy-only         Start proxy only, don't launch claude
  -h, --help           Show this help
```

### Examples

```bash
# Use a preset persona
./knurl-persona -p personas/pirate.txt

# Rename the companion
./knurl-persona -n "Captain" -p personas/pirate.txt

# Debug mode — see raw payloads
./knurl-persona -v

# Proxy only (if you want to start claude separately)
./knurl-persona --proxy-only &
HTTPS_PROXY=http://127.0.0.1:18888 NODE_TLS_REJECT_UNAUTHORIZED=0 claude
```

## Writing a persona

Create a text file with a personality description. Keep it under 200 characters (the API truncates beyond that). The text is injected as the companion's `personality` field, which the server-side model uses to generate speech bubble reactions.

Tips:
- Be specific about language ("only speak in Chinese", "respond in haiku")
- Define tone and quirks ("ends every sentence with arrr")
- The companion sees a transcript of recent conversation, so it has context

## Included personas

| File | Description |
|------|-------------|
| `personas/catgirl-zh.txt` | Gentle cat-girl, Chinese only, praises everything |
| `personas/grumpy-senior.txt` | Tired senior engineer who sighs at abstractions |
| `personas/pirate.txt` | Pirate captain on a coding voyage |
| `personas/haiku-poet.txt` | Responds only in haiku |

## How it was discovered

The companion's speech is generated via `POST /api/organizations/{org}/claude_code/buddy_react` with a payload containing `name`, `personality`, `species`, `transcript`, etc. The `personality` field (max 200 chars) is the primary lever controlling the companion's tone and language. This tool simply rewrites that field in-flight.

## Security note

This tool sets `NODE_TLS_REJECT_UNAUTHORIZED=0` to allow the local proxy to intercept HTTPS traffic. This is safe for local use but **do not use this on untrusted networks**. The proxy only runs on localhost.

## Requirements

- [Claude Code](https://claude.ai/code) (CLI)
- [mitmproxy](https://mitmproxy.org/) (`brew install mitmproxy`)

## License

MIT
