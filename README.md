# Tailscale ACL

GitOps source for the Tailscale tailnet policy. The repository is public, so the policy must be committed as a SOPS-encrypted file. GitHub Actions decrypts it only for validation and deployment.

Place the current policy in the ignored local file `policy.hujson` at the repository root. The encrypted file `policy.hujson.sops.json` is the only policy file that should be committed. The current live policy is not included in Git yet.

## Encrypt the policy

Create a dedicated age key outside the repository and store its private key in a password manager:

```sh
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/tailscale-acl.agekey
```

Keep `~/.config/sops/age/tailscale-acl.agekey` private. Encrypt the HuJSON file as a SOPS binary payload so comments and trailing commas are preserved:

```sh
sops --encrypt \
  --input-type binary \
  --output-type json \
  --age "$(age-keygen -y ~/.config/sops/age/tailscale-acl.agekey)" \
  policy.hujson > policy.hujson.sops.json
```

`policy.hujson` is ignored by Git. SOPS stores the encrypted binary payload in a JSON envelope; decryption restores the original HuJSON bytes.

## Configure GitHub Actions

Add these repository Actions secrets:

| Secret | Value |
| --- | --- |
| `SOPS_AGE_KEY` | Private key from `~/.config/sops/age/tailscale-acl.agekey` |
| `TS_OAUTH_ID` | Tailscale federated identity client ID |
| `TS_AUDIENCE` | Audience configured for that identity |
| `TS_TAILNET` | Tailnet name |

Configure the Tailscale federated identity with the `policy_file` scope and restrict its GitHub trust conditions to this repository. The private age key and Tailscale credentials are only used by Actions; do not commit them.

The workflow tests policy changes on pull requests and applies them to the tailnet after a push to `main`. Pull requests from forks are skipped so they cannot access repository secrets.

## Security

Tailscale policy files can contain personal information such as user email addresses. This public repository stores the policy encrypted; review the decrypted policy locally before encrypting it and keep the age private key separate from Git.

See [Tailscale GitOps for GitHub Actions](https://tailscale.com/docs/integrations/github/gitops) for the policy sync action, [Tailscale policy syntax](https://tailscale.com/docs/reference/syntax/policy-file), and [SOPS binary format](https://getsops.io/docs/usage/advanced/).
