cmake_minimum_required(VERSION 3.22)
project(vss-binary)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_VERBOSE_MAKEFILE false)
#add_link_options(--verbose)

add_compile_options(-Wall -Wextra -Wpedantic -Werror)


add_subdirectory(c_parser)
