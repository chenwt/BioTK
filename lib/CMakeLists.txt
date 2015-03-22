project(BioTK)
cmake_minimum_required(VERSION 3.0)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
set(CMAKE_BUILD_TYPE Release)

find_package(CUDA QUIET REQUIRED)
add_subdirectory(src/cuda)
enable_testing()

include(CheckCXXCompilerFlag)
CHECK_CXX_COMPILER_FLAG("-std=c++14" COMPILER_SUPPORTS_CXX14)
if(COMPILER_SUPPORTS_CXX14)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")
else()
    message(STATUS "The compiler ${CMAKE_CXX_COMPILER} has no C++14 support. Please use a different C++ compiler.")
endif()

#include(CMakeForceCompiler)
#CMAKE_FORCE_C_COMPILER(icc "Intel C Compiler")
#CMAKE_FORCE_CXX_COMPILER(icpc "Intel C++ Compiler")

set(CMAKE_C_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp -march=native")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp -march=native")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fopenmp")

# See also: http://www.cmake.org/pipermail/cmake/2011-May/044445.html
if(${CMAKE_CXX_COMPILER_ID} STREQUAL "Intel")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -xHost -ip -ipo -IP_fma -parallel")
endif()

link_directories(/lib /lib64 /usr/lib /usr/lib64)
include_directories(SYSTEM "/usr/include")

set(BioTK_VERSION_MAJOR 0)
set(BioTK_VERSION_MINOR 1)
set(BioTK_VERSION_PATCH 0)
set(BioTK_VERSION_STRING ${BioTK_VERSION_MAJOR}.${BioTK_VERSION_MINOR}.${BioTK_VERSION_PATCH})

add_subdirectory(src/ext)
add_subdirectory(src/lib)
add_subdirectory(src/bin)
add_subdirectory(src/test)
