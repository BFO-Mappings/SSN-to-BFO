#!/usr/bin/env bash
set -euo pipefail

if (( $# > 1 )); then
  echo "Usage: $0 [installation-directory]" >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repository_root="$(cd -- "${script_dir}/.." && pwd -P)"
source "${repository_root}/config/validation-toolchain.env"

required_variables=(
  VALIDATION_ROBOT_VERSION
  VALIDATION_ROBOT_URL
  VALIDATION_ROBOT_SHA256
  VALIDATION_ROBOT_JAVA_HEAP
)
for variable in "${required_variables[@]}"; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Required validation toolchain variable is empty: ${variable}" >&2
    exit 1
  fi
done

if (( $# == 1 )); then
  installation_directory="$1"
else
  installation_directory="${repository_root}/build/lib/robot-${VALIDATION_ROBOT_VERSION}"
fi

mkdir -p -- "${installation_directory}"
installation_directory="$(cd -- "${installation_directory}" && pwd -P)"
bin_directory="${installation_directory}/bin"
jar_path="${installation_directory}/robot.jar"
wrapper_path="${bin_directory}/robot"
mkdir -p -- "${bin_directory}"

if command -v sha256sum >/dev/null 2>&1; then
  checksum_command="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
  checksum_command="shasum"
else
  echo "Cannot verify ROBOT: neither sha256sum nor shasum is available." >&2
  exit 1
fi

calculate_checksum() {
  if [[ "${checksum_command}" == "sha256sum" ]]; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

verify_checksum() {
  local file_path="$1"
  local actual_checksum
  actual_checksum="$(calculate_checksum "${file_path}")"
  if [[ "${actual_checksum}" != "${VALIDATION_ROBOT_SHA256}" ]]; then
    echo "ROBOT checksum mismatch for ${file_path}" >&2
    echo "Expected: ${VALIDATION_ROBOT_SHA256}" >&2
    echo "Actual:   ${actual_checksum}" >&2
    return 1
  fi
}

temporary_file=""
cleanup_temporary_file() {
  if [[ -n "${temporary_file}" && -e "${temporary_file}" ]]; then
    rm -f -- "${temporary_file}"
  fi
}
trap cleanup_temporary_file EXIT

if [[ -f "${jar_path}" ]]; then
  echo "Reusing existing ROBOT JAR: ${jar_path}" >&2
  if ! verify_checksum "${jar_path}"; then
    echo "Existing ROBOT JAR is invalid; remove it explicitly before reinstalling." >&2
    exit 1
  fi
else
  if ! command -v curl >/dev/null 2>&1; then
    echo "Cannot download ROBOT: curl is not available." >&2
    exit 1
  fi
  temporary_file="$(mktemp "${installation_directory}/robot.jar.download.XXXXXX")"
  echo "Downloading ROBOT ${VALIDATION_ROBOT_VERSION}" >&2
  if ! curl --fail --location --silent --show-error \
    --output "${temporary_file}" \
    "${VALIDATION_ROBOT_URL}"; then
    echo "ROBOT download failed." >&2
    exit 1
  fi
  if ! verify_checksum "${temporary_file}"; then
    echo "Downloaded ROBOT JAR is invalid and will not be installed." >&2
    exit 1
  fi
  mv -- "${temporary_file}" "${jar_path}"
  temporary_file=""
fi

temporary_file="$(mktemp "${bin_directory}/robot.wrapper.XXXXXX")"
printf '#!/usr/bin/env bash\nexec java -Xmx%s -jar %q "$@"\n' \
  "${VALIDATION_ROBOT_JAVA_HEAP}" "${jar_path}" > "${temporary_file}"
chmod +x "${temporary_file}"
mv -- "${temporary_file}" "${wrapper_path}"
temporary_file=""

printf '%s\n' "${bin_directory}"
