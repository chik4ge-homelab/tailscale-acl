# Tailscale ACL

GitOps source for the Tailscale tailnet policy. The repository is public, so the policy must be committed as a SOPS-encrypted file. GitHub Actions decrypts it only for validation and deployment.

The current live policy is not included yet. Add an encrypted export of the existing policy before enabling this repository as the source of truth.

## Encrypt the policy

Create a dedicated age key outside the repository and store its private key in a password manager:

```sh
age-keygen -o tailscale-acl.agekey
```

Keep `tailscale-acl.agekey` private. Encrypt a JSON-formatted Tailscale policy as `policy.json.sops`:

```sh
sops --encrypt \
  --input-type json \
  --output-type json \
  --age "$(age-keygen -y tailscale-acl.agekey)" \
  policy.json > policy.json.sops
```

`policy.json` and the decrypted `policy.hujson` are ignored by Git. Tailscale accepts JSON as HuJSON, so the policy can be stored as JSON without comments.

## Configure GitHub Actions

Add these repository Actions secrets:

| Secret | Value |
| --- | --- |
| `SOPS_AGE_KEY` | Private key from `tailscale-acl.agekey` |
| `TS_OAUTH_ID` | Tailscale federated identity client ID |
| `TS_AUDIENCE` | Audience configured for that identity |
| `TS_TAILNET` | Tailnet name |

Configure the Tailscale federated identity with the `policy_file` scope and restrict its GitHub trust conditions to this repository. The private age key and Tailscale credentials are only used by Actions; do not commit them.

The workflow tests policy changes on pull requests and applies them to the tailnet after a push to `main`. Pull requests from forks are skipped so they cannot access repository secrets.

## Security

Tailscale policy files can contain personal information such as user email addresses. This public repository stores the policy encrypted; review the decrypted policy locally before encrypting it and keep the age private key separate from Git.

See [Tailscale GitOps for GitHub Actions](https://tailscale.com/docs/integrations/github/gitops) for the policy sync action and [Tailscale policy syntax](https://tailscale.com/docs/reference/syntax/policy-file).
