# Tailscale ACL

GitOps source for the Tailscale tailnet policy. This repository is public; only the SOPS-encrypted policy is committed.

The current policy is in the ignored local file `policy.hujson`. The encrypted file `policy.hujson.sops.json` is the only policy file to commit.

## Key management

The repo-specific age private key is stored in the `homelab` 1Password vault as the Secure Note **Tailscale ACL repo SOPS age key**. `fnox.toml` retrieves it through 1Password as a temporary local file and exports its path as `SOPS_AGE_KEY_FILE` only to the command started by fnox. GitHub Actions uses the repository secret `SOPS_AGE_KEY` for CI decryption. The public age recipient is in `.sops.yaml`.

The Tailscale credentials are separate repository Actions secrets:

| Secret | Value |
| --- | --- |
| `TS_OAUTH_ID` | Tailscale federated identity client ID |
| `TS_AUDIENCE` | Audience configured for that identity |
| `TS_TAILNET` | Tailnet name |

Configure the federated identity with the `policy_file` scope and restrict its GitHub trust conditions to this repository. Until all three Tailscale secrets are set, the workflow decrypts the policy but skips the Tailscale test/apply step.

## Encrypt and verify

The policy stays as HuJSON locally. SOPS binary mode preserves the original bytes, including comments and trailing commas:

```sh
mise exec -- sops --encrypt \
  --input-type binary \
  --output-type json \
  policy.hujson > policy.hujson.sops.json
```

Verify local decryption without printing the policy:

```sh
mise exec -- fnox --non-interactive --if-missing error --no-daemon exec sops --decrypt \
  --input-type json \
  --output-type binary \
  policy.hujson.sops.json > /dev/null
```

`policy.hujson` is ignored by Git. Do not print or commit the private age key or plaintext policy. The private key is materialized only for the duration of a fnox command.

Tailscale policy files can contain personal information such as user email addresses. See [Tailscale GitOps for GitHub Actions](https://tailscale.com/docs/integrations/github/gitops), [Tailscale policy syntax](https://tailscale.com/docs/reference/syntax/policy-file), and [SOPS binary format](https://getsops.io/docs/usage/advanced/).
