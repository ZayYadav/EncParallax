// AD_safe.cpp - Safe Android native diagnostics library
// Intentionally excludes destructive/resource-exhaustion attack routines.

#include <jni.h>
#include <android/log.h>
#include <sys/system_properties.h>
#include <sys/utsname.h>
#include <sys/statvfs.h>
#include <unistd.h>

#include <algorithm>
#include <fstream>
#include <mutex>
#include <sstream>
#include <string>

#define PARALLAX_TAG "ParallaxSafe"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, PARALLAX_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, PARALLAX_TAG, __VA_ARGS__)

namespace {

std::mutex g_mutex;
std::string g_cached_summary;

std::string get_property(const char* key) {
    char value[PROP_VALUE_MAX] = {0};
    const int len = __system_property_get(key, value);
    return len > 0 ? std::string(value, static_cast<size_t>(len)) : std::string("unknown");
}

long long read_mem_total_mb() {
    std::ifstream in("/proc/meminfo");
    std::string key;
    long long kb = 0;
    std::string unit;

    while (in >> key >> kb >> unit) {
        if (key == "MemTotal:") {
            return kb / 1024;
        }
        std::string rest;
        std::getline(in, rest);
    }
    return -1;
}

struct StorageInfo {
    long long total_mb = -1;
    long long free_mb = -1;
};

StorageInfo read_storage(const char* path) {
    struct statvfs vfs {};
    StorageInfo out;
    if (statvfs(path, &vfs) != 0) {
        return out;
    }

    const unsigned long long block_size =
        vfs.f_frsize != 0 ? vfs.f_frsize : vfs.f_bsize;
    out.total_mb = static_cast<long long>(
        (static_cast<unsigned long long>(vfs.f_blocks) * block_size) / (1024ULL * 1024ULL));
    out.free_mb = static_cast<long long>(
        (static_cast<unsigned long long>(vfs.f_bavail) * block_size) / (1024ULL * 1024ULL));
    return out;
}

std::string architecture() {
    struct utsname u {};
    if (uname(&u) == 0) {
        return u.machine;
    }
    return "unknown";
}

std::string build_summary() {
    const long cores = std::max<long>(1, sysconf(_SC_NPROCESSORS_ONLN));
    const long long ram_mb = read_mem_total_mb();
    const StorageInfo storage = read_storage("/data");

    std::ostringstream out;
    out << "{"
        << "\"library\":\"ParallaxSafe\","
        << "\"model\":\"" << get_property("ro.product.model") << "\","
        << "\"manufacturer\":\"" << get_property("ro.product.manufacturer") << "\","
        << "\"android\":\"" << get_property("ro.build.version.release") << "\","
        << "\"sdk\":\"" << get_property("ro.build.version.sdk") << "\","
        << "\"abi\":\"" << architecture() << "\","
        << "\"cpu_cores\":" << cores << ","
        << "\"ram_mb\":" << ram_mb << ","
        << "\"storage_total_mb\":" << storage.total_mb << ","
        << "\"storage_free_mb\":" << storage.free_mb
        << "}";
    return out.str();
}

} // namespace

extern "C" __attribute__((visibility("default")))
const char* parallax_device_summary() {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_cached_summary = build_summary();
    return g_cached_summary.c_str();
}

extern "C" __attribute__((visibility("default")))
int parallax_cpu_count() {
    const long cores = sysconf(_SC_NPROCESSORS_ONLN);
    return cores > 0 ? static_cast<int>(cores) : 1;
}

extern "C" __attribute__((visibility("default")))
long long parallax_total_ram_mb() {
    return read_mem_total_mb();
}

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    if (vm == nullptr) {
        LOGE("JNI_OnLoad called with null JavaVM");
        return JNI_ERR;
    }

    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK || env == nullptr) {
        LOGE("Unable to obtain JNIEnv");
        return JNI_ERR;
    }

    LOGI("ParallaxSafe loaded: %s", parallax_device_summary());
    return JNI_VERSION_1_6;
}
