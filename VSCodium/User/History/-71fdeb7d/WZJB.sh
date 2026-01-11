#!/bin/bash
set -e

# =========================
# Configurações
# =========================
DEVICE=a34x
PROJECT=mgk_64_k66
MODE=user

ROOT_DIR=$(pwd)
KERNEL_DIR="$ROOT_DIR/kernel"
KDM_DIR="$KERNEL_DIR/kernel_device_modules-6.6"

OUT_BASE="$ROOT_DIR/out/target/product/$DEVICE/obj"
KERNEL_OBJ="$OUT_BASE/KERNEL_OBJ"
KLEAF_OBJ="$OUT_BASE/KLEAF_OBJ"

# =========================
# Garantir bazel em tools/
# =========================
cd "$KERNEL_DIR"

if [ ! -x tools/bazel ]; then
  echo "[*] Instalando bazel em kernel/tools/bazel"
  rm -rf tools
  mkdir -p tools
  cp prebuilts/kernel-build-tools/bazel/linux-x86_64/bazel* tools/bazel
  chmod +x tools/bazel
fi

./tools/bazel --version || true

# =========================
# Gerar build.config
# =========================
mkdir -p "$KERNEL_OBJ"

python kernel_device_modules-6.6/scripts/gen_build_config.py \
  --kernel-defconfig mediatek-bazel_defconfig \
  --kernel-defconfig-overlays "sec_ogki_fragment.config mt6877_overlay.config mt6877_teegris_5_overlay.config" \
  -o "$KERNEL_OBJ/build.config"

# =========================
# Exportar ambiente (Kleaf)
# =========================
export DEVICE_MODULES_DIR="kernel_device_modules-6.6"
export BUILD_CONFIG="$KERNEL_OBJ/build.config"
export OUT_DIR="$KLEAF_OBJ"
export DIST_DIR="$KLEAF_OBJ/dist"
export DEFCONFIG_OVERLAYS="sec_ogki_fragment.config mt6877_overlay.config mt6877_teegris_5_overlay.config"
export PROJECT="$PROJECT"
export MODE="$MODE"

# =========================
# Entrar no WORKSPACE Bazel
# =========================
cd "$KDM_DIR"

if [ ! -f MODULE.bazel ]; then
  echo "ERRO: MODULE.bazel não encontrado (workspace inválido)"
  exit 1
fi

# =========================
# Build dos módulos
# =========================
echo "[*] Iniciando build Kleaf (device modules)"
../build.sh "${PROJECT}_customer_modules_install.${MODE}"

echo "[✓] Build finalizado"
