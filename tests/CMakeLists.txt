cmake_minimum_required(VERSION 3.28)
project(test_project VERSION 0.1.0)

# Enable testing
include(CTest)

# Create main executable
add_executable(test_app src/main.cpp)

# Set up tests
add_executable(test_main test/test_main.cpp)
add_test(NAME TestMain COMMAND test_main)

# Set up packaging
include(CPack)
set(CPACK_PACKAGE_NAME "test_project")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_GENERATOR "TGZ")
