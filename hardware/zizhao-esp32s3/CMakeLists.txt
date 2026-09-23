# zizhao ESP32-S3 firmware
cmake_minimum_required(VERSION 3.16)

# 镜像版本：写进 esp_app_desc.version，后台 OTA 靠它与服务端 manifest 比对。
# 不用 VERSION 文件（IDF 5.1 只认 version.txt / git describe，否则恒为 "1"），
# 也不用 project(... VERSION)（要到 IDF 5.3+ 才被解析）。发版改这里 + 改 manifest。
set(PROJECT_VER "1.0.0")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(zizhao_esp32s3)
