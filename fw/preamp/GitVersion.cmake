cmake_minimum_required(VERSION 3.9)

# Set version based on git info, with 0.0-0000000-dirty as default
set(FW_VER_MAJOR "0")
set(FW_VER_MINOR "0")
set(FW_VER_HASH0 "00")
set(FW_VER_HASH1 "00")
set(FW_VER_HASH2 "00")
set(FW_VER_HASH3 "01")

# Check that git is available on the current system
find_package(Git)
if(GIT_FOUND)
  # Use 'git describe' to find the latest tag matching 'fw/*'.
  # Tags should be of the form fw/MAJOR.MINOR.
  # The current commit hash to 7 hex characters is also extracted,
  # as well as the dirty status.
  execute_process(
    COMMAND ${GIT_EXECUTABLE} describe --match "fw/*" --long --abbrev=7 --dirty
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    OUTPUT_VARIABLE git_describe  # The contents of stdout
    ERROR_VARIABLE git_error      # The contents of stderr
    RESULT_VARIABLE git_result    # The command's exit status
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_STRIP_TRAILING_WHITESPACE
  )
  if(git_result AND NOT git_result EQUAL 0)
    # 'git describe' did not complete successfully
    message(WARNING
      " ${git_error}\n"
      " Will set version to 0.0-0000000-dirty"
    )
  else()
    # Parse the version number from the git tag, should be of the
    # following form, where lowercase text is literal:
    # fw/MAJOR.MINOR-NUM_COMMITS_SINCE_TAG-gHASH[-dirty]
    string(REGEX MATCH "fw/([0-9]+)\.([0-9]+)-[0-9]+-g([0-9a-f]+)" _ ${git_describe})

    # The three capture groups from above contain the MAJOR, MINOR, and HASH.
    # The HASH needs to be split up into individual bytes with the last byte
    # also containing the dirty bit.
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
  # No git found, so fallback to the default version
  message(WARNING
    " Git not found\n"
    " Will set version to 0.0-0000000-dirty"
  )
endif()

# Create a version C file from the template.
# A C file is used instead of a header so that only the
# version file needs to be re-compiled.
#
# Additionally 'configure_file' will only update the file's
# timestamp if changes were made, so no re-compiling will be
# required unless part of the version changed.
configure_file("${infile}" "${outfile}" @ONLY)
