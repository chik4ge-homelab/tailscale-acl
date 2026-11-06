# Tailscale ACL

GitOps source for the Tailscale tailnet policy. The source is split into ordinary
Tailscale JSON sections. The build creates one policy file for Tailscale.

## Files

* `policy/grants.json`: plaintext `grants` rules.
* `policy/ssh.json`: plaintext `ssh` rules.
* `policy/tests.json`: plaintext policy tests.
* `policy/tag-owners.json`: plaintext tag names and owners.
* `secrets.sops.json`: group membership data encrypted with SOPS + age.
* `scripts/render-policy.sh`: merges the fragments into a mode `0600` policy file in a
  temporary directory.
* `scripts/policy-graph.py`: creates a Graphviz view from the plaintext grant and SSH
  sections. It omits group membership and redacts selectors outside public group, tag,
  and autogroup names.
* `docs/access-graph.svg`: generated image shown below and refreshed automatically on
  same-repository pull requests when grant or SSH rules change.

The SOPS `encrypted_regex` in `.sops.yaml` matches keys beginning with `group:`. This
encrypts group membership values while keeping group names visible as JSON keys. SOPS
leaves keys visible and applies `encrypted_regex` to values whose key names match the
expression ([SOPS reference](https://getsops.io/docs/reference/)). The current ACL's
sensitive values are group membership identifiers. No email addresses, IP addresses,
or hostnames are embedded directly in the rule selectors, so this migration does not
need placeholder replacement.

Only `group:*` values are currently covered by the encryption rule. If a new sensitive
field is added, update the regex and verify that its values are encrypted before
committing it.

## Merge and validation

Each plaintext source is a JSON object with a distinct Tailscale top-level key. The
build sends SOPS plaintext directly to `jq`; it does not write a decrypted secrets
fragment. It rejects non-object fragments and duplicate top-level keys before combining
them. The generated policy was compared semantically with the previous policy before
this refactor was prepared.

## Key management

The repo-specific age private key is stored in the `homelab` 1Password vault as the
Secure Note **Tailscale ACL repo SOPS age key**. `fnox.toml` retrieves it through
1Password as a temporary local file and exports its path as `SOPS_AGE_KEY_FILE` only to
the command started by fnox. GitHub Actions uses the repository secret `SOPS_AGE_KEY`
for CI decryption. The public age recipient is in `.sops.yaml`.

The Tailscale credentials are separate repository Actions secrets:

| Secret | Value |
| --- | --- |
| `TS_OAUTH_ID` | Tailscale federated identity client ID |
| `TS_AUDIENCE` | Audience configured for that identity |
| `TS_TAILNET` | Tailnet name |

Configure the federated identity with the `policy_file` scope and restrict its GitHub
trust conditions to this repository. Pull requests run the Tailscale policy test when
all three credentials are configured. Pushes to `main` apply the policy when all three
credentials are configured. `workflow_dispatch` renders the policy only.

## Editing and encryption

Edit the four files under `policy/` as normal Tailscale policy JSON. This keeps
`grants`, `ssh`, `tests`, and tag ownership easy to review independently.

To edit encrypted values, use SOPS' editor with the local key supplied through fnox:

```sh
mise exec -- fnox --non-interactive --if-missing error --no-daemon exec sops secrets.sops.json
```

To create or restructure the encrypted groups object, prepare `secrets.json` with
restrictive permissions. It is ignored by Git. Then encrypt it using the public age
recipient:

```sh
set -eu
umask 077
# Write the groups object to secrets.json.
encrypted_tmp="$(mktemp)"
trap 'rm -f "$encrypted_tmp"' EXIT
mise exec -- sops --encrypt --input-type json --output-type json \
  secrets.json > "$encrypted_tmp"
chmod 0644 "$encrypted_tmp"
mv "$encrypted_tmp" secrets.sops.json
rm -f secrets.json
```

Do not print or commit plaintext values, generated policies, or the private age key.
`.gitignore` excludes local secret fragments, graph output, and local key files.

## Render and deploy

Render locally and capture the generated file path without displaying policy contents:

```sh
policy_file="$(mise exec -- fnox --non-interactive --if-missing error --no-daemon exec scripts/render-policy.sh)"
```

In CI, the file is created under `RUNNER_TEMP`; locally it uses the operating system's
temporary directory. The script prints the path, sets the GitHub step output, and writes
the file with mode `0600`. GitHub Actions passes that path to the Tailscale action and
removes the file after the job. A pull request to `main` tests the generated policy
when Tailscale credentials are configured; a push to `main` applies it when those
credentials are configured.

## Access graph

![Tailscale access graph](docs/access-graph.svg)

The access-graph workflow regenerates the SVG from `policy/grants.json` and
`policy/ssh.json`. If it changes, the workflow commits the new image to the PR branch,
so the README preview shows the updated graph. Group membership is not included, and
unrecognized selectors use generic labels. Blue edges are grants and orange edges are
SSH; green nodes are groups and blue nodes are tags.

See [Tailscale GitOps for GitHub Actions](https://tailscale.com/docs/integrations/github/gitops)
and [Tailscale policy syntax](https://tailscale.com/docs/reference/syntax/policy-file).
