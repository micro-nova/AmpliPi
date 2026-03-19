#!/bin/bash
# Test different chunks of the sp_meta.py script. Be sure to include src arg

echo -e "Running first test. If I get stuck on any test, terminate the test with ^C\n"
cat /data/.config/amplipi/python/tests/sample_info.txt | /home/pi/python/sp_meta.py $1
echo -e "First test complete. Showing file differences from known good -\n"
diff /data/.config/amplipi/srcs/$1/currentSong /home/pi/python/tests/test_metadata_script/kg_currentSong --color=always

echo -e "Running second test...\n"
cat /data/.config/amplipi/python/tests/sample_sinfo.txt | /home/pi/python/sp_meta.py $1
echo -e "Second test complete. Showing file differences from known good -\n"
diff /data/.config/amplipi/srcs/$1/sourceInfo /home/pi/python/tests/test_metadata_script/kg_sourceInfo --color=always

echo -e "Running third test...\n"
cat /data/.config/amplipi/python/tests/sample_info2.txt | /home/pi/python/sp_meta.py $1
echo -e "Third test complete. Showing file differences from known good -\n"
diff /data/.config/amplipi/srcs/$1/currentSong /home/pi/python/tests/test_metadata_script/kg_currentSong2 --color=always

echo -e "Running fourth test...\n"
cat /data/.config/amplipi/python/tests/sample_info3.txt | /home/pi/python/sp_meta.py $1
echo -e "Fourth test complete. Showing file differences from known good -\n"
diff /data/.config/amplipi/srcs/$1/currentSong /home/pi/python/tests/test_metadata_script/kg_currentSong3 --color=always


echo All tests complete.
