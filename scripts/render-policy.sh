#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
temp_root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"

umask 077
output_dir="$(mktemp -d "${temp_root%/}/tailscale-acl.XXXXXX")"
chmod 0700 -- "${output_dir}"
output="${output_dir}/policy.generated.json"
tmp_output="$(mktemp "${output}.XXXXXX")"
cleanup() {
  rm -f -- "${tmp_output}" "${output}"
  rmdir -- "${output_dir}" 2>/dev/null || true
}
trap cleanup EXIT

sops --decrypt "${repo_root}/secrets.sops.json" \
  | jq -s '
      if any(.[]; type != "object") then
        error("every policy fragment must be a JSON object")
      else
        [ .[] | keys_unsorted[] ] as $keys
        | if ($keys | length) != ($keys | unique | length) then
            error("duplicate top-level policy keys")
          else
            add
          end
      end
    ' \
    "${repo_root}/policy/grants.json" \
    "${repo_root}/policy/ssh.json" \
    "${repo_root}/policy/tests.json" \
    "${repo_root}/policy/tag-owners.json" \
    - > "${tmp_output}"
chmod 0600 -- "${tmp_output}"
mv -f -- "${tmp_output}" "${output}"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'policy_file=%s\n' "${output}" >> "${GITHUB_OUTPUT}"
fi
printf '%s\n' "${output}"
trap - EXIT
