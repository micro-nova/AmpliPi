cmake_minimum_required(VERSION 3.9)

# Set version based on git info, with 0.0-0000000-dirty as default
set(FW_VER_MAJOR "0")
set(FW_VER_MINOR "0")
set(FW_VER_HASH0 "00")
set(FW_VER_HASH1 "00")
set(FW_VER_HASH2 "00")
set(FW_VER_HASH3 "01")

find_package(Git)
if(GIT_FOUND)
  execute_process(
    COMMAND ${GIT_EXECUTABLE} describe --match "fw/*" --long --abbrev=7 --dirty
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    OUTPUT_VARIABLE git_describe
    ERROR_VARIABLE git_error
    RESULT_VARIABLE git_result
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_STRIP_TRAILING_WHITESPACE
  )
  if(git_result AND NOT git_result EQUAL 0)
    message(WARNING
      " ${git_error}\n"
      " Will set version to 0.0-0000000-dirty"
    )
  else()
    string(REGEX MATCH "fw/([0-9]+)\.([0-9]+)-[0-9]+-g([0-9a-f]+)" _ ${git_describe})
    set(FW_VER_MAJOR ${CMAKE_MATCH_1})
    set(FW_VER_MINOR ${CMAKE_MATCH_2})
    set(FW_VER_HASH ${CMAKE_MATCH_3})
    string(SUBSTRING ${CMAKE_MATCH_3} 0 2 FW_VER_HASH0)
    string(SUBSTRING ${CMAKE_MATCH_3} 2 2 FW_VER_HASH1)
    string(SUBSTRING ${CMAKE_MATCH_3} 4 2 FW_VER_HASH2)
    string(SUBSTRING ${CMAKE_MATCH_3} 6 1 FW_VER_HASH3)
    if(git_describe MATCHES "-dirty$")
      string(APPEND FW_VER_HASH3 "1")
    else()
      string(APPEND FW_VER_HASH3 "0")
    endif()
    message(STATUS
      "Setting firmware version to ${FW_VER_MAJOR}.${FW_VER_MINOR}-"
      "${FW_VER_HASH0}${FW_VER_HASH1}${FW_VER_HASH2}${FW_VER_HASH3}"
    )
  endif()
else()
  message(WARNING
    " Git not found\n"
    " Will set version to 0.0-0000000-dirty"
  )
endif()

# Create version C file from template.
# The timestamp will only be updated if changes were made.
configure_file("${infile}" "${outfile}" @ONLY)
