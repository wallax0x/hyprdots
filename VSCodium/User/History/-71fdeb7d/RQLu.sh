#!/bin/bash
set -e

#!/bin/bash
set -e

cd kernel || exit 1

python kernel_device_modules-6.6/scripts/gen_build_config.py \
  --kernel-defconfig mediatek-bazel_defconfig \
  --kernel-defconfig-overlays "sec_ogki_fragment.config mt6877_overlay.config mt6877_teegris_5_overlay.config" \
  -o ../out/target/product/a34x/obj/KERNEL_OBJ/build.config

cd kernel_device_modules-6.6 || exit 1
../build.sh mgk_64_k66_customer_modules_install.user

export DEVICE_MODULES_DIR="kernel_device_modules-6.6"
export BUILD_CONFIG="../out/target/product/a34x/obj/KERNEL_OBJ/build.config"
export OUT_DIR="../out/target/product/a34x/obj/KLEAF_OBJ"
export DIST_DIR="../out/target/product/a34x/obj/KLEAF_OBJ/dist"
export DEFCONFIG_OVERLAYS="sec_ogki_fragment.config mt6877_overlay.config mt6877_teegris_5_overlay.config"
export PROJECT="mgk_64_k66"
export MODE="user"

kernel_device_modules-6.6/build.sh mgk_64_k66_customer_modules_install.user
