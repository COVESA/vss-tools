cmake_minimum_required(VERSION 3.22)
project(cparserlib)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_VERBOSE_MAKEFILE false)
#add_link_options(--verbose)

add_compile_options(-Wall -Wextra -Wpedantic -Werror)

add_library(cparserlib SHARED cparserlib.c cparserlib.h)
set_property(TARGET cparserlib PROPERTY POSITION_INDEPENDENT_CODE ON)
target_include_directories(cparserlib PUBLIC .)

add_executable(ctestparser testparser.c)
target_link_libraries(ctestparser cparserlib)
